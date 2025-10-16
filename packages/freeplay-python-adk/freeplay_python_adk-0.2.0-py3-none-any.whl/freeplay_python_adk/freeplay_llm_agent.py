import json
import re
from typing import Any, Callable, Optional, Union

from freeplay import Freeplay
from freeplay.resources.prompts import TemplatePrompt
from freeplay.support import TemplateChatMessage, TemplateMessage
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import InstructionProvider
from google.adk.models.base_llm import BaseLlm
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from opentelemetry import context as otel_context
from opentelemetry import trace
from pydantic import Field, model_validator

from freeplay_python_adk.client import get_global_config
from freeplay_python_adk.constants import FreeplayOTelAttributes


class FreeplayLLMAgent(LlmAgent, arbitrary_types_allowed=True):
    model: Union[str, BaseLlm] = Field(init=False, default="")
    instruction: Union[str, InstructionProvider] = Field(init=False, default="")

    input_variables: Optional[dict[str, Any]] = None
    project_id: Optional[str] = None
    environment: Optional[str] = None
    freeplay: Optional[Freeplay] = None

    @model_validator(mode="before")
    @classmethod
    def update_model(cls, data: Any) -> Any:
        if (
            data.get("project_id") is None
            or data.get("environment") is None
            or data.get("freeplay") is None
        ):
            global_config = get_global_config()
            if global_config is None:
                raise FreeplayConfigurationError()

            project_id = data.get("project_id") or global_config.project_id
            environment = data.get("environment") or global_config.environment
            freeplay = data.get("freeplay") or global_config.freeplay

        prompt_template = freeplay.prompts.get(
            project_id=project_id,
            template_name=data.get("name"),
            environment=environment,
        )
        if prompt_template.prompt_info.provider == "vertex":
            # Avoid going through LiteLlm for Gemini/Vertex models.
            data["model"] = prompt_template.prompt_info.model
        else:
            data["model"] = LiteLlm(
                model=lite_llm_model_string(prompt_template),
            )

        add_callback(
            data,
            "before_model_callback",
            lambda callback_context, llm_request: FreeplayLLMAgent._before_model_callback(
                callback_context=callback_context,
                llm_request=llm_request,
                prompt_template=prompt_template,
                agent_input_variables=data.get("input_variables"),
            ),
        )
        add_callback(
            data,
            "after_model_callback",
            lambda callback_context, llm_response: FreeplayLLMAgent._after_model_callback(  # noqa: ARG005
                prompt_template=prompt_template,
                environment=environment,
            ),
        )
        return data

    @staticmethod
    def _before_model_callback(
        callback_context: CallbackContext,
        llm_request: LlmRequest,
        prompt_template: TemplatePrompt,
        agent_input_variables: dict[str, Any],
    ) -> None:
        # Google ADK does a bunch of system message manipulation to add
        # information about what agents are available to call, so we preserve
        # that and pass it through agent_context.
        agent_context = llm_request.config.system_instruction
        input_variables = relevant_variables(
            prompt_template,
            sanitize(
                {
                    **(agent_input_variables or {}),
                    **callback_context.state.to_dict(),
                    "agent_context": str(agent_context),
                }
            ),
        )

        # Store input variables in OpenTelemetry context for use in after_model_callback
        otel_context.attach(
            otel_context.set_value(
                FreeplayOTelAttributes.FREEPLAY_INPUT_VARIABLES.value,
                json.dumps(input_variables),
            )
        )

        bound_prompt = prompt_template.bind(
            input_variables,
            # History is added through different mechanisms, we just use the
            # system prompt here.
            history=[],
        )
        formatted_prompt = bound_prompt.format(flavor_name="openai_chat")
        llm_request.config.system_instruction = formatted_prompt.system_content

        # Model parameters
        prompt_params = bound_prompt.prompt_info.model_parameters
        if "temperature" in prompt_params:
            llm_request.config.temperature = prompt_params["temperature"]
        if "top_p" in prompt_params:
            llm_request.config.top_p = prompt_params["top_p"]

        if "max_output_tokens" in prompt_params:
            llm_request.config.max_output_tokens = prompt_params["max_output_tokens"]
        elif "max_completion_tokens" in prompt_params:
            llm_request.config.max_output_tokens = prompt_params[
                "max_completion_tokens"
            ]
        elif "max_tokens" in prompt_params:
            llm_request.config.max_output_tokens = prompt_params["max_tokens"]

    @staticmethod
    def _after_model_callback(
        prompt_template: TemplatePrompt,
        environment: str,
    ) -> None:
        span = trace.get_current_span()

        # Retrieve input_variables from OpenTelemetry context
        input_variables_json = otel_context.get_value(
            FreeplayOTelAttributes.FREEPLAY_INPUT_VARIABLES.value
        )
        if input_variables_json and isinstance(input_variables_json, str):
            span.set_attribute(
                FreeplayOTelAttributes.FREEPLAY_INPUT_VARIABLES.value,
                input_variables_json,
            )

        span.set_attribute(
            FreeplayOTelAttributes.FREEPLAY_PROMPT_TEMPLATE_VERSION_ID.value,
            prompt_template.prompt_info.prompt_template_version_id,
        )
        span.set_attribute(
            FreeplayOTelAttributes.FREEPLAY_ENVIRONMENT.value,
            environment,
        )


def add_callback(data: Any, field: str, callback: Callable[..., None]) -> None:
    if field not in data or not data[field]:
        data[field] = []
    elif not isinstance(data[field], list):
        data[field] = [data[field]]
    data[field].append(callback)
    return data


class FreeplayConfigurationError(Exception):
    """Raised when Freeplay configuration is missing or incomplete."""

    def __init__(self):
        super().__init__(
            "Freeplay configuration not initialized. Either call FreeplayADK.initialize_observability() first or provide project_id, environment, and freeplay parameters explicitly."
        )


def lite_llm_model_string(prompt_template: TemplatePrompt) -> str:
    provider = prompt_template.prompt_info.provider
    model = prompt_template.prompt_info.model
    return f"{provider}/{model}"


mustache_variable_pattern = re.compile(r"{{(\w+)}}")


def extract_variable_name(message: TemplateMessage) -> list[str]:
    if not isinstance(message, TemplateChatMessage):
        return []
    return mustache_variable_pattern.findall(message.content)


def relevant_variables(
    prompt_template: TemplatePrompt, variables: dict[Any, Any]
) -> dict[Any, Any]:
    all_variables = {
        variable
        for message in prompt_template.messages
        for variable in extract_variable_name(message)
    }
    return {key: value for key, value in variables.items() if key in all_variables}


def sanitize(data: Any) -> Any:
    if isinstance(data, (str, int, float, bool)):
        return data
    if isinstance(data, dict):
        return {
            key: sanitize(value) for key, value in data.items() if isinstance(key, str)
        }
    if isinstance(data, list):
        return [sanitize(item) for item in data]
    return None
