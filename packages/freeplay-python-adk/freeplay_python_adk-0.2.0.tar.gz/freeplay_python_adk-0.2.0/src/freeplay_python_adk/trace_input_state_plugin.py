import json

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.sessions.session import Session
from google.genai import types
from opentelemetry import context as otel_context
from opentelemetry import trace
from typing_extensions import Any

from freeplay_python_adk.constants import FreeplayOTelAttributes


class TraceInputStatePlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="trace_input_state_plugin")

    async def before_run_callback(
        self,
        *,
        invocation_context: InvocationContext,
    ) -> None:
        TraceInputStatePlugin.__add_trace_info(
            invocation_context.session, invocation_context.session.state
        )

        if not otel_context.get_value(FreeplayOTelAttributes.FREEPLAY_SESSION_ID.value):
            otel_context.attach(
                otel_context.set_value(
                    FreeplayOTelAttributes.FREEPLAY_SESSION_ID.value,
                    invocation_context.session.id,
                )
            )

    async def before_agent_callback(
        self,
        *,
        agent: BaseAgent,  # noqa: ARG002
        callback_context: CallbackContext,
    ) -> None:
        TraceInputStatePlugin.__add_trace_info(
            callback_context._invocation_context.session,  # noqa: SLF001
            callback_context.state.to_dict(),
        )

    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,  # noqa: ARG002
        llm_response: LlmResponse,  # noqa: ARG002
    ) -> None:
        span = trace.get_current_span()
        freeplay_session_id = otel_context.get_value(
            FreeplayOTelAttributes.FREEPLAY_SESSION_ID.value
        )
        if freeplay_session_id and isinstance(freeplay_session_id, str):
            span.set_attribute(
                FreeplayOTelAttributes.FREEPLAY_SESSION_ID.value,
                freeplay_session_id,
            )

    @staticmethod
    def __add_trace_info(session: Session, state: dict[str, Any]) -> None:
        inputs = {}
        if state:
            inputs["state"] = state
        messages = []
        for event in session.events:
            if event.content:
                content = TraceInputStatePlugin.__drop_thought_signatures(event.content)
                if content.parts:
                    messages.append(content.to_json_dict())
        if messages:
            inputs["messages"] = messages

        span = trace.get_current_span()
        span.set_attribute(
            FreeplayOTelAttributes.FREEPLAY_INPUT_VARIABLES.value,
            json.dumps(inputs),
        )
        freeplay_session_id = otel_context.get_value(
            FreeplayOTelAttributes.FREEPLAY_SESSION_ID.value
        )
        if freeplay_session_id and isinstance(freeplay_session_id, str):
            span.set_attribute(
                FreeplayOTelAttributes.FREEPLAY_SESSION_ID.value,
                freeplay_session_id,
            )

    @staticmethod
    def __drop_thought_signatures(content: types.Content) -> types.Content:
        return types.Content(
            parts=(
                [part for part in content.parts if not part.thought_signature]
                if content.parts
                else None
            ),
            role=content.role,
        )
