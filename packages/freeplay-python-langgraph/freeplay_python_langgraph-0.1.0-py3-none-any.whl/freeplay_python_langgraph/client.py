import os
from dataclasses import dataclass
from typing import Optional

from freeplay.freeplay import Freeplay
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


@dataclass
class FreeplayConfig:
    """Freeplay configuration."""

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


class FreeplayLangGraph:
    """Minimal Freeplay LangGraph integration."""

    @staticmethod
    def initialize_observability(
        freeplay_api_url: Optional[str] = None,
        freeplay_api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        environment: str = "latest",
        log_spans_to_console: bool = False,
    ) -> None:
        """Initialize Freeplay observability."""
        # Get from environment if not provided
        freeplay_api_url = freeplay_api_url or os.environ.get("FREEPLAY_API_URL", "")
        freeplay_api_key = freeplay_api_key or os.environ.get("FREEPLAY_API_KEY", "")
        project_id = project_id or os.environ.get("FREEPLAY_PROJECT_ID", "")

        # Setup OTEL exporter
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

        # Instrument LangChain - this creates spans for LangChain/LangGraph calls
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

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
