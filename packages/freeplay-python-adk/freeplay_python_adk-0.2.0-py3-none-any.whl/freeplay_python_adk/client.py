import os
from dataclasses import dataclass
from typing import Optional

from freeplay.freeplay import Freeplay
from openinference.instrumentation.google_adk import GoogleADKInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


@dataclass
class FreeplayConfig:
    """Configuration for Freeplay ADK."""

    freeplay_api_url: str
    freeplay_api_key: str
    project_id: str
    environment: str
    freeplay: Freeplay


class FreeplayConfigSingleton:
    """Class to manage Freeplay configuration."""

    _config: Optional[FreeplayConfig] = None

    @classmethod
    def set_config(cls, config: FreeplayConfig) -> None:
        """Set the configuration."""
        cls._config = config

    @classmethod
    def get_config(cls) -> Optional[FreeplayConfig]:
        """Get the configuration."""
        return cls._config


class FreeplayADK:
    """Freeplay ADK for Google ADK integration."""

    @staticmethod
    def initialize_observability(
        freeplay_api_url: str = os.environ.get("FREEPLAY_API_URL", ""),
        freeplay_api_key: str = os.environ.get("FREEPLAY_API_KEY", ""),
        project_id: str = os.environ.get("FREEPLAY_PROJECT_ID", ""),
        environment: str = "latest",
        log_spans_to_console: bool = False,
    ) -> None:
        """Initialize global Freeplay settings.

        This allows users to call FreeplayLLMAgent() directly without needing to
        pass configuration each time.

        Args:
            freeplay_api_url: Freeplay API URL
            freeplay_api_key: Freeplay API key
            project_id: Freeplay project ID
            environment: Environment to use (default: "latest")
            log_spans_to_console: Log spans to console (default: False)
        """
        # Set up telemetry
        exporter = OTLPSpanExporter(
            endpoint=f"{freeplay_api_url}/v0/otel/v1/traces",
            headers={
                "Authorization": f"Bearer {freeplay_api_key}",
                "X-Freeplay-Project-Id": project_id,
            },
        )

        tracer_provider = trace_sdk.TracerProvider()
        tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
        if log_spans_to_console:
            tracer_provider.add_span_processor(
                SimpleSpanProcessor(ConsoleSpanExporter())
            )
        GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)

        # Store configuration using singleton
        config = FreeplayConfig(
            freeplay_api_url=freeplay_api_url,
            freeplay_api_key=freeplay_api_key,
            project_id=project_id,
            environment=environment,
            freeplay=Freeplay(
                freeplay_api_key=freeplay_api_key,
                api_base=freeplay_api_url,
            ),
        )
        FreeplayConfigSingleton.set_config(config)


def get_global_config() -> Optional[FreeplayConfig]:
    """Get the global Freeplay configuration."""
    return FreeplayConfigSingleton.get_config()
