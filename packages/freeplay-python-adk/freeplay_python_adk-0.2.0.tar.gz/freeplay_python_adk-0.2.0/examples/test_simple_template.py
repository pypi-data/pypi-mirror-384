import logging
import uuid

import pytest
from dotenv import load_dotenv
from freeplay_python_adk.client import FreeplayADK
from freeplay_python_adk.freeplay_llm_agent import FreeplayLLMAgent
from freeplay_python_adk.trace_input_state_plugin import TraceInputStatePlugin
from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger(__name__)

load_dotenv("../../../.env")
FreeplayADK.initialize_observability(log_spans_to_console=True)


async def run_step_async(runner: Runner, message: str, session_id: str) -> None:
    logger.debug(f"Running step with message: {message}")
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    events = runner.run_async(
        user_id="test_user", session_id=session_id, new_message=content
    )

    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            response = event.content.parts[0].text
            logger.debug(f"Output: {response}")


@pytest.mark.vcr
async def test_simple_template():
    basic_agent = FreeplayLLMAgent(
        name="greeter",
        description="Greets the user, in a friendly and concise way.",
        sub_agents=[],
    )

    session_id = uuid.uuid4()

    app = App(
        name="greeter_app",
        root_agent=basic_agent,
        plugins=[TraceInputStatePlugin()],
    )

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app.name, user_id="test_user", session_id=str(session_id)
    )
    runner = Runner(
        app=app,
        session_service=session_service,
    )

    await run_step_async(
        runner,
        "Hello, how are you?",
        str(session_id),
    )
