from enum import Enum


class FreeplayOTelAttributes(Enum):
    FREEPLAY_INPUT_VARIABLES = "freeplay.input_variables"
    FREEPLAY_PROMPT_TEMPLATE_VERSION_ID = "freeplay.prompt_template.version.id"
    FREEPLAY_ENVIRONMENT = "freeplay.environment"
    FREEPLAY_SESSION_ID = "freeplay.session.id"
