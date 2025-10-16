import logging
import uuid

import pytest
from dotenv import load_dotenv
from freeplay_python_adk.client import FreeplayADK
from freeplay_python_adk.trace_input_state_plugin import TraceInputStatePlugin
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv("../../../.env")
FreeplayADK.initialize_observability(log_spans_to_console=True)


logger = logging.getLogger(__name__)


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
async def test_research_agent():
    from examples.research_agent import root_agent  # noqa: PLC0415

    session_id = uuid.uuid4()

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="test_app", user_id="test_user", session_id=str(session_id)
    )
    runner = Runner(
        agent=root_agent,
        app_name="test_app",
        session_service=session_service,
        plugins=[TraceInputStatePlugin()],
    )

    await run_step_async(
        runner,
        "What's the best route from Portland OR to Bend OR on a gravel bike?",
        str(session_id),
    )
    await run_step_async(runner, "That's great, go ahead.", str(session_id))
