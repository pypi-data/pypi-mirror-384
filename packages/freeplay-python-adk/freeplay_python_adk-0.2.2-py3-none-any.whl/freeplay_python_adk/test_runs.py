from opentelemetry import context as otel_context

from freeplay_python_adk.constants import FreeplayOTelAttributes


def attach_test_info(test_run_id: str, test_case_id: str) -> None:
    otel_context.attach(
        otel_context.set_value(
            FreeplayOTelAttributes.FREEPLAY_TEST_RUN_ID.value,
            test_run_id,
        )
    )
    otel_context.attach(
        otel_context.set_value(
            FreeplayOTelAttributes.FREEPLAY_TEST_CASE_ID.value,
            test_case_id,
        )
    )
