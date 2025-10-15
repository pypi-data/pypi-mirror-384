import atexit
import contextvars
import itertools
import logging
import os
import sys
import threading
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from enum import Enum
from importlib.metadata import Distribution, distributions
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import requests
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPExporter
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, SpanProcessor, TracerProvider, SpanLimits
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
)
from opentelemetry.trace import Span, SpanContext

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_ENDPOINT = "https://api.docent.transluce.org/rest/telemetry"
DEFAULT_COLLECTION_NAME = "default-collection-name"


class Instruments(Enum):
    """Enumeration of available instrument types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    LANGCHAIN = "langchain"


class DocentSpanProcessor(SpanProcessor):
    """Span processor that enriches spans on_end and forwards to exporters."""

    class _MergedReadableSpan:
        def __init__(self, original: ReadableSpan, extra_attributes: Dict[str, Any]):
            self._original = original
            self._extra_attributes = extra_attributes
            self._merged_attributes: Optional[Dict[str, Any]] = None

        def __getattr__(self, item: str) -> Any:
            return getattr(self._original, item)

        @property
        def attributes(self) -> Mapping[str, Any]:
            if self._merged_attributes is None:
                original_attrs = cast(Mapping[str, Any], self._original.attributes)
                merged = dict(original_attrs.items())
                merged.update(self._extra_attributes)
                self._merged_attributes = merged
            return cast(Mapping[str, Any], self._merged_attributes)

    def __init__(
        self,
        manager: "DocentTracer",
        exporters: Sequence[SpanExporter],
        use_simple_processor: bool,
    ) -> None:
        self._manager = manager
        self._delegates: List[SpanProcessor] = [
            SimpleSpanProcessor(exporter) if use_simple_processor else BatchSpanProcessor(exporter)
            for exporter in exporters
        ]
        self._span_attributes: Dict[Tuple[int, int], Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _span_key(span: Union[Span, ReadableSpan]) -> Tuple[int, int]:
        context = cast(SpanContext, span.get_span_context())
        return (context.trace_id, context.span_id)

    def on_start(
        self,
        span: Span,
        parent_context: Optional[Context] = None,
    ) -> None:
        if self._manager.is_disabled() or not self._delegates:
            return

        attributes = self._manager.build_span_context_attributes()
        key = self._span_key(span)
        with self._lock:
            self._span_attributes[key] = attributes

    def on_end(self, span: ReadableSpan) -> None:
        key = self._span_key(span)
        with self._lock:
            context_attributes = self._span_attributes.pop(key, {})

        if self._manager.is_disabled() or not self._delegates:
            return

        wrapped_span = cast(ReadableSpan, self._MergedReadableSpan(span, context_attributes))
        span_attrs_mapping = cast(Mapping[str, Any], wrapped_span.attributes)
        span_attrs = dict(span_attrs_mapping.items())
        logger.debug(
            "Exporting span copy: name='%s', collection_id=%s, agent_run_id=%s, transcript_id=%s",
            wrapped_span.name,
            span_attrs.get("collection_id"),
            span_attrs.get("agent_run_id"),
            span_attrs.get("transcript_id"),
        )

        for delegate in self._delegates:
            delegate.on_end(wrapped_span)

    def shutdown(self) -> None:
        for delegate in self._delegates:
            delegate.shutdown()

    def force_flush(self, timeout_millis: Optional[float] = None) -> bool:
        result = True
        delegate_timeout = int(timeout_millis) if timeout_millis is not None else 30000
        for delegate in self._delegates:
            result = delegate.force_flush(delegate_timeout) and result
        return result


class DocentTracer:
    """
    Manages Docent tracing setup and provides tracing utilities.
    """

    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        collection_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        endpoint: Union[str, List[str]] = DEFAULT_ENDPOINT,
        headers: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
        enable_console_export: bool = False,
        enable_otlp_export: bool = True,
        disable_batch: bool = False,
        instruments: Optional[Set[Instruments]] = None,
        block_instruments: Optional[Set[Instruments]] = None,
    ):
        self._initialized: bool = False
        # Check if tracing is disabled via environment variable
        if _is_tracing_disabled():
            self._disabled = True
            logger.info("Docent tracing disabled via DOCENT_DISABLE_TRACING environment variable")
            return

        self.collection_name: str = collection_name
        self.collection_id: str = collection_id if collection_id else str(uuid.uuid4())
        self.default_agent_run_id: str = agent_run_id if agent_run_id else str(uuid.uuid4())
        self.endpoints: List[str]

        # Handle endpoint parameter - convert to list if it's a string
        if isinstance(endpoint, str):
            self.endpoints = [endpoint]
        else:
            self.endpoints = endpoint

        # Build headers with authentication if provided
        self.headers = headers or {}

        # Handle API key authentication (takes precedence over custom headers)
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            logger.info(f"Using API key authentication for {self.collection_name}")
        elif self.headers.get("Authorization"):
            logger.info(f"Using custom Authorization header for {self.collection_name}")
        else:
            logger.info(f"No authentication configured for {self.collection_name}")

        self.enable_console_export = enable_console_export
        self.enable_otlp_export = enable_otlp_export
        self.disable_batch = disable_batch
        self.disabled_instruments: Set[Instruments] = {Instruments.LANGCHAIN}
        self.instruments = instruments or (set(Instruments) - self.disabled_instruments)
        self.block_instruments = block_instruments or set()

        # Use separate tracer provider to avoid interfering with existing OTEL setup
        self._tracer_provider: Optional[TracerProvider] = None
        self._root_context: Optional[Context] = Context()
        self._tracer: Optional[trace.Tracer] = None
        self._cleanup_registered: bool = False
        self._disabled: bool = False
        self._span_processor: Optional[SpanProcessor] = None

        # Base HTTP endpoint for direct API calls (scores, metadata, trace-done)
        if len(self.endpoints) > 0:
            self._api_endpoint_base: Optional[str] = self.endpoints[0]

        # Context variables for agent_run_id and transcript_id
        self._collection_id_var: ContextVar[str] = contextvars.ContextVar("docent_collection_id")
        self._agent_run_id_var: ContextVar[str] = contextvars.ContextVar("docent_agent_run_id")
        self._transcript_id_var: ContextVar[str] = contextvars.ContextVar("docent_transcript_id")
        self._transcript_group_id_var: ContextVar[str] = contextvars.ContextVar(
            "docent_transcript_group_id"
        )
        self._attributes_var: ContextVar[dict[str, Any]] = contextvars.ContextVar(
            "docent_attributes"
        )
        # Store atomic span order counters per transcript_id to persist across context switches
        self._transcript_counters: defaultdict[str, itertools.count[int]] = defaultdict(
            lambda: itertools.count(0)
        )
        self._transcript_counter_lock = threading.Lock()
        self._flush_lock = threading.Lock()

    def get_current_agent_run_id(self) -> Optional[str]:
        """
        Get the current agent run ID from context.

        Retrieves the agent run ID that was set in the current execution context.
        If no agent run context is active, returns the default agent run ID.

        Returns:
            The current agent run ID if available, or the default agent run ID
            if no context is active.
        """
        try:
            return self._agent_run_id_var.get()
        except LookupError:
            return self.default_agent_run_id

    def _register_cleanup(self):
        """Register cleanup handlers."""
        if self._cleanup_registered:
            return

        # Register atexit handler
        atexit.register(self.cleanup)

        self._cleanup_registered = True

    def _next_span_order(self, transcript_id: str) -> int:
        """
        Get the next span order for a given transcript_id.
        Thread-safe and guaranteed to be unique and monotonic.
        """
        with self._transcript_counter_lock:
            return next(self._transcript_counters[transcript_id])

    def build_span_context_attributes(self) -> Dict[str, Any]:
        """Collect context-driven attributes to attach to exported spans."""

        attributes: Dict[str, Any] = {"collection_id": self.collection_id}

        try:
            agent_run_id = self._agent_run_id_var.get()
            if agent_run_id:
                attributes["agent_run_id"] = agent_run_id
            else:
                attributes["agent_run_id_default"] = True
                attributes["agent_run_id"] = self.default_agent_run_id
        except LookupError:
            attributes["agent_run_id_default"] = True
            attributes["agent_run_id"] = self.default_agent_run_id

        try:
            transcript_group_id = self._transcript_group_id_var.get()
            if transcript_group_id:
                attributes["transcript_group_id"] = transcript_group_id
        except LookupError:
            pass

        transcript_id: Optional[str] = None
        try:
            transcript_id = self._transcript_id_var.get()
        except LookupError:
            transcript_id = None

        if transcript_id:
            attributes["transcript_id"] = transcript_id
            attributes["span_order"] = self._next_span_order(transcript_id)

        try:
            additional_attributes = self._attributes_var.get()
            for key, value in additional_attributes.items():
                attributes[key] = value
        except LookupError:
            pass

        return attributes

    def _init_spans_exporter(self, endpoint: str) -> Optional[Union[HTTPExporter, GRPCExporter]]:
        """Initialize the appropriate span exporter based on endpoint."""
        if not self.enable_otlp_export:
            return None

        try:
            if "http" in endpoint.lower() or "https" in endpoint.lower():
                http_exporter: HTTPExporter = HTTPExporter(
                    endpoint=f"{endpoint}/v1/traces", headers=self.headers, timeout=30
                )
                logger.debug(f"Initialized HTTP exporter for endpoint: {endpoint}/v1/traces")
                return http_exporter
            else:
                grpc_exporter: GRPCExporter = GRPCExporter(
                    endpoint=endpoint, headers=self.headers, timeout=30
                )
                logger.debug(f"Initialized gRPC exporter for endpoint: {endpoint}")
                return grpc_exporter
        except Exception as e:
            logger.error(f"Failed to initialize span exporter for {endpoint}: {e}")
            return None

    def _init_spans_exporters(self) -> List[Union[HTTPExporter, GRPCExporter]]:
        """Initialize span exporters for all endpoints."""
        exporters: List[Union[HTTPExporter, GRPCExporter]] = []

        for endpoint in self.endpoints:
            exporter = self._init_spans_exporter(endpoint)
            if exporter:
                exporters.append(exporter)
                logger.info(f"Initialized exporter for endpoint: {endpoint}")
            else:
                logger.critical(f"Failed to initialize exporter for endpoint: {endpoint}")

        return exporters

    def initialize(self):
        """Initialize Docent tracing setup."""
        if self._initialized:
            return

        # If tracing is disabled, mark as initialized but don't set up anything
        if self._disabled:
            self._initialized = True
            return

        try:

            # Check for OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT environment variable
            default_attribute_limit = 1024
            env_value = os.environ.get("OTEL_SPAN_ATTRIBUTE_COUNT_LIMIT", "0")
            env_limit = int(env_value) if env_value.isdigit() else 0
            attribute_limit = max(env_limit, default_attribute_limit)

            span_limits = SpanLimits(
                max_attributes=attribute_limit,
            )

            # Create our own isolated tracer provider
            self._tracer_provider = TracerProvider(
                resource=Resource.create({"service.name": self.collection_name}),
                span_limits=span_limits,
            )

            exporters: List[SpanExporter] = []

            if self.enable_otlp_export:
                otlp_exporters: List[Union[HTTPExporter, GRPCExporter]] = (
                    self._init_spans_exporters()
                )
                if otlp_exporters:
                    exporters.extend(otlp_exporters)
                    logger.info(
                        "Registered %s OTLP exporter(s) for %s endpoint(s)",
                        len(otlp_exporters),
                        len(self.endpoints),
                    )

            if self.enable_console_export:
                exporters.append(ConsoleSpanExporter())
                logger.info("Registered console span exporter")

            if exporters:
                use_simple_processor = self.disable_batch or _is_notebook()
                if use_simple_processor:
                    logger.debug("Using SimpleSpanProcessor delegation for Docent spans")
                else:
                    logger.debug("Using BatchSpanProcessor delegation for Docent spans")

                self._span_processor = DocentSpanProcessor(
                    manager=self,
                    exporters=exporters,
                    use_simple_processor=use_simple_processor,
                )
                self._tracer_provider.add_span_processor(self._span_processor)
            else:
                logger.warning("No span exporters configured; spans will not be exported")

            # Get tracer from our isolated provider (don't set global provider)
            self._tracer = self._tracer_provider.get_tracer(__name__)

            # Instrument threading for better context propagation
            try:
                ThreadingInstrumentor().instrument()
            except Exception as e:
                logger.warning(f"Failed to instrument threading: {e}")

            enabled_instruments = self.instruments - self.block_instruments

            # Instrument OpenAI with our isolated tracer provider
            if Instruments.OPENAI in enabled_instruments:
                try:
                    if is_package_installed("openai"):
                        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

                        OpenAIInstrumentor().instrument(tracer_provider=self._tracer_provider)
                        logger.info("Instrumented OpenAI")
                except Exception as e:
                    logger.warning(f"Failed to instrument OpenAI: {e}")

            # Instrument Anthropic with our isolated tracer provider
            if Instruments.ANTHROPIC in enabled_instruments:
                try:
                    if is_package_installed("anthropic"):
                        from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

                        AnthropicInstrumentor().instrument(tracer_provider=self._tracer_provider)
                        logger.info("Instrumented Anthropic")
                except Exception as e:
                    logger.warning(f"Failed to instrument Anthropic: {e}")

            # Instrument Bedrock with our isolated tracer provider
            if Instruments.BEDROCK in enabled_instruments:
                try:
                    if is_package_installed("boto3"):
                        from opentelemetry.instrumentation.bedrock import BedrockInstrumentor

                        BedrockInstrumentor().instrument(tracer_provider=self._tracer_provider)
                        logger.info("Instrumented Bedrock")
                except Exception as e:
                    logger.warning(f"Failed to instrument Bedrock: {e}")

            # Instrument LangChain with our isolated tracer provider
            if Instruments.LANGCHAIN in enabled_instruments:
                try:
                    if is_package_installed("langchain") or is_package_installed("langgraph"):
                        from opentelemetry.instrumentation.langchain import LangchainInstrumentor

                        LangchainInstrumentor().instrument(tracer_provider=self._tracer_provider)
                        logger.info("Instrumented LangChain")
                except Exception as e:
                    logger.warning(f"Failed to instrument LangChain: {e}")

            # Register cleanup handlers
            self._register_cleanup()

            self._initialized = True
            logger.info(f"Docent tracing initialized for {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Docent tracing: {e}")
            self._disabled = True
            raise

    def cleanup(self):
        """
        Clean up Docent tracing resources.

        Flushes all pending spans to exporters and shuts down the tracer provider.
        This method is automatically called during application shutdown via atexit
        handlers, but can also be called manually for explicit cleanup.

        The cleanup process:
        1. Flushes all span processors to ensure data is exported
        2. Shuts down the tracer provider and releases resources
        """
        if self._disabled:
            return

        try:
            self.flush()

            if self._tracer_provider:
                self._tracer_provider.shutdown()
                self._tracer_provider = None
                self._span_processor = None
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def close(self):
        """Explicitly close the Docent tracing manager."""
        if self._disabled:
            return

        try:
            self.cleanup()
            if self._cleanup_registered:
                atexit.unregister(self.cleanup)
                self._cleanup_registered = False
        except Exception as e:
            logger.error(f"Error during close: {e}")

    def flush(self) -> None:
        """Force flush all spans to exporters."""
        if self._disabled:
            return

        try:
            if not self._span_processor:
                logger.debug("No Docent span processor registered to flush")
                return

            logger.debug("Flushing Docent span processor")
            self._span_processor.force_flush(timeout_millis=50)
            logger.debug("Span flush completed")
        except Exception as e:
            logger.error(f"Error during flush: {e}")

    def is_disabled(self) -> bool:
        """Check if tracing is disabled."""
        return self._disabled

    def set_disabled(self, disabled: bool) -> None:
        """Enable or disable tracing."""
        self._disabled = disabled
        if disabled and self._initialized:
            self.cleanup()

    def is_initialized(self) -> bool:
        """Verify if the manager is properly initialized."""
        return self._initialized

    @contextmanager
    def agent_run_context(
        self,
        agent_run_id: Optional[str] = None,
        transcript_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **attributes: Any,
    ) -> Iterator[tuple[str, str]]:
        """
        Context manager for setting up an agent run context.

        Args:
            agent_run_id: Optional agent run ID (auto-generated if not provided)
            transcript_id: Optional transcript ID (auto-generated if not provided)
            metadata: Optional nested dictionary of metadata to send to backend
            **attributes: Additional attributes to add to the context

        Yields:
            Tuple of (agent_run_id, transcript_id)
        """
        if self._disabled:
            # Return dummy IDs when tracing is disabled
            if agent_run_id is None:
                agent_run_id = str(uuid.uuid4())
            if transcript_id is None:
                transcript_id = str(uuid.uuid4())
            yield agent_run_id, transcript_id
            return

        if not self._initialized:
            self.initialize()

        if agent_run_id is None:
            agent_run_id = str(uuid.uuid4())
        if transcript_id is None:
            transcript_id = str(uuid.uuid4())

        # Set context variables for this execution context
        agent_run_id_token: Token[str] = self._agent_run_id_var.set(agent_run_id)
        transcript_id_token: Token[str] = self._transcript_id_var.set(transcript_id)
        attributes_token: Token[dict[str, Any]] = self._attributes_var.set(attributes)

        try:
            # Send metadata directly to backend if provided
            if metadata:
                try:
                    self.send_agent_run_metadata(agent_run_id, metadata)
                except Exception as e:
                    logger.warning(f"Failed sending agent run metadata: {e}")

            yield agent_run_id, transcript_id
        finally:
            self._agent_run_id_var.reset(agent_run_id_token)
            self._transcript_id_var.reset(transcript_id_token)
            self._attributes_var.reset(attributes_token)

    @asynccontextmanager
    async def async_agent_run_context(
        self,
        agent_run_id: Optional[str] = None,
        transcript_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **attributes: Any,
    ) -> AsyncIterator[tuple[str, str]]:
        """
        Async context manager for setting up an agent run context.
        Modifies the OpenTelemetry context so all spans inherit agent_run_id and transcript_id.

        Args:
            agent_run_id: Optional agent run ID (auto-generated if not provided)
            transcript_id: Optional transcript ID (auto-generated if not provided)
            metadata: Optional nested dictionary of metadata to send to backend
            **attributes: Additional attributes to add to the context

        Yields:
            Tuple of (agent_run_id, transcript_id)
        """
        if self._disabled:
            # Return dummy IDs when tracing is disabled
            if agent_run_id is None:
                agent_run_id = str(uuid.uuid4())
            if transcript_id is None:
                transcript_id = str(uuid.uuid4())
            yield agent_run_id, transcript_id
            return

        if not self._initialized:
            self.initialize()

        if agent_run_id is None:
            agent_run_id = str(uuid.uuid4())
        if transcript_id is None:
            transcript_id = str(uuid.uuid4())

        # Set context variables for this execution context
        agent_run_id_token: Token[str] = self._agent_run_id_var.set(agent_run_id)
        transcript_id_token: Token[str] = self._transcript_id_var.set(transcript_id)
        attributes_token: Token[dict[str, Any]] = self._attributes_var.set(attributes)

        try:
            # Send metadata directly to backend if provided
            if metadata:
                try:
                    self.send_agent_run_metadata(agent_run_id, metadata)
                except Exception as e:
                    logger.warning(f"Failed sending agent run metadata: {e}")

            yield agent_run_id, transcript_id
        finally:
            self._agent_run_id_var.reset(agent_run_id_token)
            self._transcript_id_var.reset(transcript_id_token)
            self._attributes_var.reset(attributes_token)

    def _api_headers(self) -> Dict[str, str]:
        """
        Get the API headers for HTTP requests.

        Returns:
            Dictionary of headers including Authorization if set
        """
        headers = {"Content-Type": "application/json"}

        authorization = self.headers.get("Authorization")
        if authorization:
            headers["Authorization"] = authorization

        return headers

    def _post_json(self, path: str, data: Dict[str, Any]) -> None:
        if not self._api_endpoint_base:
            raise RuntimeError("API endpoint base is not configured")
        url = f"{self._api_endpoint_base}{path}"
        try:
            resp = requests.post(url, json=data, headers=self._api_headers(), timeout=(10, 60))
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed POST {url}: {e}")

    def send_agent_run_score(
        self,
        agent_run_id: str,
        name: str,
        score: float,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send a score to the backend for a specific agent run.

        Args:
            agent_run_id: The agent run ID
            name: Name of the score metric
            score: Numeric score value
            attributes: Optional additional attributes
        """
        if self._disabled:
            return

        collection_id = self.collection_id
        payload: Dict[str, Any] = {
            "collection_id": collection_id,
            "agent_run_id": agent_run_id,
            "score_name": name,
            "score_value": score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if attributes:
            payload.update(attributes)
        self._post_json("/v1/scores", payload)

    def send_agent_run_metadata(self, agent_run_id: str, metadata: Dict[str, Any]) -> None:
        if self._disabled:
            return

        collection_id = self.collection_id
        payload: Dict[str, Any] = {
            "collection_id": collection_id,
            "agent_run_id": agent_run_id,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._post_json("/v1/agent-run-metadata", payload)

    def send_transcript_metadata(
        self,
        transcript_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        transcript_group_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send transcript data to the backend.

        Args:
            transcript_id: The transcript ID
            name: Optional transcript name
            description: Optional transcript description
            transcript_group_id: Optional transcript group ID
            metadata: Optional metadata to send
        """
        if self._disabled:
            return

        collection_id = self.collection_id
        payload: Dict[str, Any] = {
            "collection_id": collection_id,
            "transcript_id": transcript_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Only add fields that are provided
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if transcript_group_id is not None:
            payload["transcript_group_id"] = transcript_group_id
        if metadata is not None:
            payload["metadata"] = metadata

        self._post_json("/v1/transcript-metadata", payload)

    def get_current_transcript_id(self) -> Optional[str]:
        """
        Get the current transcript ID from context.

        Returns:
            The current transcript ID if available, None otherwise
        """
        try:
            return self._transcript_id_var.get()
        except LookupError:
            return None

    def get_current_transcript_group_id(self) -> Optional[str]:
        """
        Get the current transcript group ID from context.

        Returns:
            The current transcript group ID if available, None otherwise
        """
        try:
            return self._transcript_group_id_var.get()
        except LookupError:
            return None

    @contextmanager
    def transcript_context(
        self,
        name: Optional[str] = None,
        transcript_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        transcript_group_id: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Context manager for setting up a transcript context.

        Args:
            name: Optional transcript name
            transcript_id: Optional transcript ID (auto-generated if not provided)
            description: Optional transcript description
            metadata: Optional metadata to send to backend
            transcript_group_id: Optional transcript group ID

        Yields:
            The transcript ID
        """
        if self._disabled:
            # Return dummy ID when tracing is disabled
            if transcript_id is None:
                transcript_id = str(uuid.uuid4())
            yield transcript_id
            return

        if not self._initialized:
            raise RuntimeError(
                "Tracer is not initialized. Call initialize_tracing() before using transcript context."
            )

        if transcript_id is None:
            transcript_id = str(uuid.uuid4())

        # Determine transcript group ID before setting new context
        if transcript_group_id is None:
            try:
                transcript_group_id = self._transcript_group_id_var.get()
            except LookupError:
                # No current transcript group context, this transcript has no group
                transcript_group_id = None

        # Set context variable for this execution context
        transcript_id_token: Token[str] = self._transcript_id_var.set(transcript_id)

        try:
            # Send transcript data and metadata to backend
            try:
                self.send_transcript_metadata(
                    transcript_id, name, description, transcript_group_id, metadata
                )
            except Exception as e:
                logger.warning(f"Failed sending transcript data: {e}")

            yield transcript_id
        finally:
            # Reset context variable to previous state
            self._transcript_id_var.reset(transcript_id_token)

    @asynccontextmanager
    async def async_transcript_context(
        self,
        name: Optional[str] = None,
        transcript_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        transcript_group_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Async context manager for setting up a transcript context.

        Args:
            name: Optional transcript name
            transcript_id: Optional transcript ID (auto-generated if not provided)
            description: Optional transcript description
            metadata: Optional metadata to send to backend
            transcript_group_id: Optional transcript group ID

        Yields:
            The transcript ID
        """
        if self._disabled:
            # Return dummy ID when tracing is disabled
            if transcript_id is None:
                transcript_id = str(uuid.uuid4())
            yield transcript_id
            return

        if not self._initialized:
            raise RuntimeError(
                "Tracer is not initialized. Call initialize_tracing() before using transcript context."
            )

        if transcript_id is None:
            transcript_id = str(uuid.uuid4())

        # Determine transcript group ID before setting new context
        if transcript_group_id is None:
            try:
                transcript_group_id = self._transcript_group_id_var.get()
            except LookupError:
                # No current transcript group context, this transcript has no group
                transcript_group_id = None

        # Set context variable for this execution context
        transcript_id_token: Token[str] = self._transcript_id_var.set(transcript_id)

        try:
            # Send transcript data and metadata to backend
            try:
                self.send_transcript_metadata(
                    transcript_id, name, description, transcript_group_id, metadata
                )
            except Exception as e:
                logger.warning(f"Failed sending transcript data: {e}")

            yield transcript_id
        finally:
            # Reset context variable to previous state
            self._transcript_id_var.reset(transcript_id_token)

    def send_transcript_group_metadata(
        self,
        transcript_group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parent_transcript_group_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send transcript group data to the backend.

        Args:
            transcript_group_id: The transcript group ID
            name: Optional transcript group name
            description: Optional transcript group description
            parent_transcript_group_id: Optional parent transcript group ID
            metadata: Optional metadata to send
        """
        if self._disabled:
            return

        collection_id = self.collection_id

        # Get agent_run_id from current context
        agent_run_id = self.get_current_agent_run_id()
        if not agent_run_id:
            logger.error(
                f"Cannot send transcript group metadata for {transcript_group_id} - no agent_run_id in context"
            )
            return

        payload: Dict[str, Any] = {
            "collection_id": collection_id,
            "transcript_group_id": transcript_group_id,
            "agent_run_id": agent_run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if parent_transcript_group_id is not None:
            payload["parent_transcript_group_id"] = parent_transcript_group_id
        if metadata is not None:
            payload["metadata"] = metadata

        self._post_json("/v1/transcript-group-metadata", payload)

    @contextmanager
    def transcript_group_context(
        self,
        name: Optional[str] = None,
        transcript_group_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_transcript_group_id: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Context manager for setting up a transcript group context.

        Args:
            name: Optional transcript group name
            transcript_group_id: Optional transcript group ID (auto-generated if not provided)
            description: Optional transcript group description
            metadata: Optional metadata to send to backend
            parent_transcript_group_id: Optional parent transcript group ID

        Yields:
            The transcript group ID
        """
        if self._disabled:
            # Return dummy ID when tracing is disabled
            if transcript_group_id is None:
                transcript_group_id = str(uuid.uuid4())
            yield transcript_group_id
            return

        if not self._initialized:
            raise RuntimeError(
                "Tracer is not initialized. Call initialize_tracing() before using transcript group context."
            )

        if transcript_group_id is None:
            transcript_group_id = str(uuid.uuid4())

        # Determine parent transcript group ID before setting new context
        if parent_transcript_group_id is None:
            try:
                parent_transcript_group_id = self._transcript_group_id_var.get()
            except LookupError:
                # No current transcript group context, this becomes a root group
                parent_transcript_group_id = None

        # Set context variable for this execution context
        transcript_group_id_token: Token[str] = self._transcript_group_id_var.set(
            transcript_group_id
        )

        try:
            # Send transcript group data and metadata to backend
            try:
                self.send_transcript_group_metadata(
                    transcript_group_id, name, description, parent_transcript_group_id, metadata
                )
            except Exception as e:
                logger.warning(f"Failed sending transcript group data: {e}")

            yield transcript_group_id
        finally:
            # Reset context variable to previous state
            self._transcript_group_id_var.reset(transcript_group_id_token)

    @asynccontextmanager
    async def async_transcript_group_context(
        self,
        name: Optional[str] = None,
        transcript_group_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_transcript_group_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Async context manager for setting up a transcript group context.

        Args:
            name: Optional transcript group name
            transcript_group_id: Optional transcript group ID (auto-generated if not provided)
            description: Optional transcript group description
            metadata: Optional metadata to send to backend
            parent_transcript_group_id: Optional parent transcript group ID

        Yields:
            The transcript group ID
        """
        if self._disabled:
            # Return dummy ID when tracing is disabled
            if transcript_group_id is None:
                transcript_group_id = str(uuid.uuid4())
            yield transcript_group_id
            return

        if not self._initialized:
            raise RuntimeError(
                "Tracer is not initialized. Call initialize_tracing() before using transcript group context."
            )

        if transcript_group_id is None:
            transcript_group_id = str(uuid.uuid4())

        # Determine parent transcript group ID before setting new context
        if parent_transcript_group_id is None:
            try:
                parent_transcript_group_id = self._transcript_group_id_var.get()
            except LookupError:
                # No current transcript group context, this becomes a root group
                parent_transcript_group_id = None

        # Set context variable for this execution context
        transcript_group_id_token: Token[str] = self._transcript_group_id_var.set(
            transcript_group_id
        )

        try:
            # Send transcript group data and metadata to backend
            try:
                self.send_transcript_group_metadata(
                    transcript_group_id, name, description, parent_transcript_group_id, metadata
                )
            except Exception as e:
                logger.warning(f"Failed sending transcript group data: {e}")

            yield transcript_group_id
        finally:
            # Reset context variable to previous state
            self._transcript_group_id_var.reset(transcript_group_id_token)

    def _send_trace_done(self) -> None:
        if self._disabled:
            return

        collection_id = self.collection_id
        payload: Dict[str, Any] = {
            "collection_id": collection_id,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._post_json("/v1/trace-done", payload)


_global_tracer: Optional[DocentTracer] = None


def initialize_tracing(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    collection_id: Optional[str] = None,
    endpoint: Union[str, List[str]] = DEFAULT_ENDPOINT,
    headers: Optional[Dict[str, str]] = None,
    api_key: Optional[str] = None,
    enable_console_export: bool = False,
    enable_otlp_export: bool = True,
    disable_batch: bool = False,
    instruments: Optional[Set[Instruments]] = None,
    block_instruments: Optional[Set[Instruments]] = None,
) -> DocentTracer:
    """
    Initialize the global Docent tracer.

    This is the primary entry point for setting up Docent tracing.
    It creates a global singleton instance that can be accessed via get_tracer().

    Args:
        collection_name: Name of the collection
        collection_id: Optional collection ID (auto-generated if not provided)
        endpoint: OTLP endpoint URL(s) for span export - can be a single string or list of strings for multiple endpoints
        headers: Optional headers for authentication
        api_key: Optional API key for bearer token authentication (takes precedence
                over DOCENT_API_KEY environment variable)
        enable_console_export: Whether to export spans to console for debugging
        enable_otlp_export: Whether to export spans to OTLP endpoint
        disable_batch: Whether to disable batch processing (use SimpleSpanProcessor)
        instruments: Set of instruments to enable (None = all instruments).
        block_instruments: Set of instruments to explicitly disable.

    Returns:
        The initialized Docent tracer

    Example:
        initialize_tracing("my-collection")
    """

    global _global_tracer

    # Check for API key in environment variable if not provided as parameter
    if api_key is None:
        env_api_key: Optional[str] = os.environ.get("DOCENT_API_KEY")
        api_key = env_api_key

    if _global_tracer is None:
        _global_tracer = DocentTracer(
            collection_name=collection_name,
            collection_id=collection_id,
            endpoint=endpoint,
            headers=headers,
            api_key=api_key,
            enable_console_export=enable_console_export,
            enable_otlp_export=enable_otlp_export,
            disable_batch=disable_batch,
            instruments=instruments,
            block_instruments=block_instruments,
        )
        _global_tracer.initialize()

    return _global_tracer


def _get_package_name(dist: Distribution) -> str | None:
    try:
        return dist.name.lower()
    except (KeyError, AttributeError):
        return None


installed_packages = {
    name for dist in distributions() if (name := _get_package_name(dist)) is not None
}


def is_package_installed(package_name: str) -> bool:
    return package_name.lower() in installed_packages


def get_tracer() -> DocentTracer:
    """Get the global Docent tracer."""
    if _global_tracer is None:
        raise RuntimeError("Docent tracer not initialized")
    return _global_tracer


def close_tracing() -> None:
    """Close the global Docent tracer."""
    global _global_tracer
    if _global_tracer:
        _global_tracer.close()
        _global_tracer = None


def flush_tracing() -> None:
    """Force flush all spans to exporters."""
    if _global_tracer:
        logger.debug("Flushing Docent tracer")
        _global_tracer.flush()
    else:
        logger.debug("No global tracer available to flush")


def is_initialized() -> bool:
    """Verify if the global Docent tracer is properly initialized."""
    if _global_tracer is None:
        return False
    return _global_tracer.is_initialized()


def is_disabled() -> bool:
    """Check if global tracing is disabled."""
    if _global_tracer:
        return _global_tracer.is_disabled()
    return True


def set_disabled(disabled: bool) -> None:
    """Enable or disable global tracing."""
    if _global_tracer:
        _global_tracer.set_disabled(disabled)


def agent_run_score(name: str, score: float, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Send a score to the backend for the current agent run.

    Args:
        name: Name of the score metric
        score: Numeric score value
        attributes: Optional additional attributes for the score event
    """
    try:
        tracer: DocentTracer = get_tracer()
        if tracer.is_disabled():
            return
        agent_run_id = tracer.get_current_agent_run_id()

        if not agent_run_id:
            logger.warning("No active agent run context. Score will not be sent.")
            return

        tracer.send_agent_run_score(agent_run_id, name, score, attributes)
    except Exception as e:
        logger.error(f"Failed to send score: {e}")


def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten nested dictionary with dot notation."""
    flattened: Dict[str, Any] = {}
    for key, value in d.items():
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten_dict(dict(value), new_key))  # type: ignore
        else:
            flattened[new_key] = value
    return flattened


def agent_run_metadata(metadata: Dict[str, Any]) -> None:
    """
    Send metadata directly to the backend for the current agent run.

    Args:
        metadata: Dictionary of metadata to attach to the current span (can be nested)

    Example:
        agent_run_metadata({"user": "John", "id": 123, "flagged": True})
        agent_run_metadata({"user": {"id": "123", "name": "John"}, "config": {"model": "gpt-4"}})
    """
    try:
        tracer = get_tracer()
        if tracer.is_disabled():
            return
        agent_run_id = tracer.get_current_agent_run_id()
        if not agent_run_id:
            logger.warning("No active agent run context. Metadata will not be sent.")
            return

        tracer.send_agent_run_metadata(agent_run_id, metadata)
    except Exception as e:
        logger.error(f"Failed to send metadata: {e}")


def transcript_metadata(
    name: Optional[str] = None,
    description: Optional[str] = None,
    transcript_group_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Send transcript metadata directly to the backend for the current transcript.

    Args:
        name: Optional transcript name
        description: Optional transcript description
        parent_transcript_id: Optional parent transcript ID
        metadata: Optional metadata to send

    Example:
        transcript_metadata(name="data_processing", description="Process user data")
        transcript_metadata(metadata={"user": "John", "model": "gpt-4"})
        transcript_metadata(name="validation", parent_transcript_id="parent-123")
    """
    try:
        tracer = get_tracer()
        if tracer.is_disabled():
            return
        transcript_id = tracer.get_current_transcript_id()
        if not transcript_id:
            logger.warning("No active transcript context. Metadata will not be sent.")
            return

        tracer.send_transcript_metadata(
            transcript_id, name, description, transcript_group_id, metadata
        )
    except Exception as e:
        logger.error(f"Failed to send transcript metadata: {e}")


class AgentRunContext:
    """Context manager that works in both sync and async contexts."""

    def __init__(
        self,
        agent_run_id: Optional[str] = None,
        transcript_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **attributes: Any,
    ):
        self.agent_run_id = agent_run_id
        self.transcript_id = transcript_id
        self.metadata = metadata
        self.attributes: dict[str, Any] = attributes
        self._sync_context: Optional[Any] = None
        self._async_context: Optional[Any] = None

    def __enter__(self) -> tuple[str, str]:
        """Sync context manager entry."""
        self._sync_context = get_tracer().agent_run_context(
            self.agent_run_id, self.transcript_id, metadata=self.metadata, **self.attributes
        )
        return self._sync_context.__enter__()

    def __exit__(self, exc_type: type[BaseException], exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit."""
        if self._sync_context:
            self._sync_context.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> tuple[str, str]:
        """Async context manager entry."""
        self._async_context = get_tracer().async_agent_run_context(
            self.agent_run_id, self.transcript_id, metadata=self.metadata, **self.attributes
        )
        return await self._async_context.__aenter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._async_context:
            await self._async_context.__aexit__(exc_type, exc_val, exc_tb)


def agent_run(
    func: Optional[Callable[..., Any]] = None, *, metadata: Optional[Dict[str, Any]] = None
):
    """
    Decorator to wrap a function in an agent_run_context (sync or async).
    Injects agent_run_id and transcript_id as function attributes.
    Optionally accepts metadata to attach to the agent run context.

    Example:
        @agent_run
        def my_func(x, y):
            print(my_func.docent.agent_run_id, my_func.docent.transcript_id)

        @agent_run(metadata={"user": "John", "model": "gpt-4"})
        def my_func_with_metadata(x, y):
            print(my_func_with_metadata.docent.agent_run_id)

        @agent_run(metadata={"config": {"model": "gpt-4", "temperature": 0.7}})
        async def my_async_func(z):
            print(my_async_func.docent.agent_run_id)
    """
    import functools
    import inspect

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(f):

            @functools.wraps(f)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                async with AgentRunContext(metadata=metadata) as (agent_run_id, transcript_id):
                    # Store docent data as function attributes
                    setattr(
                        async_wrapper,
                        "docent",
                        type(
                            "DocentData",
                            (),
                            {
                                "agent_run_id": agent_run_id,
                                "transcript_id": transcript_id,
                            },
                        )(),
                    )
                    return await f(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(f)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with AgentRunContext(metadata=metadata) as (agent_run_id, transcript_id):
                    # Store docent data as function attributes
                    setattr(
                        sync_wrapper,
                        "docent",
                        type(
                            "DocentData",
                            (),
                            {
                                "agent_run_id": agent_run_id,
                                "transcript_id": transcript_id,
                            },
                        )(),
                    )
                    return f(*args, **kwargs)

            return sync_wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def agent_run_context(
    agent_run_id: Optional[str] = None,
    transcript_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **attributes: Any,
) -> AgentRunContext:
    """
    Create an agent run context for tracing.

    Args:
        agent_run_id: Optional agent run ID (auto-generated if not provided)
        transcript_id: Optional transcript ID (auto-generated if not provided)
        metadata: Optional nested dictionary of metadata to attach as events
        **attributes: Additional attributes to add to the context

    Returns:
        A context manager that can be used with both 'with' and 'async with'

    Example:
        # Sync usage
        with agent_run_context() as (agent_run_id, transcript_id):
            pass

        # Async usage
        async with agent_run_context() as (agent_run_id, transcript_id):
            pass

        # With metadata
        with agent_run_context(metadata={"user": "John", "model": "gpt-4"}) as (agent_run_id, transcript_id):
            pass
    """
    return AgentRunContext(agent_run_id, transcript_id, metadata=metadata, **attributes)


class TranscriptContext:
    """Context manager for creating and managing transcripts."""

    def __init__(
        self,
        name: Optional[str] = None,
        transcript_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        transcript_group_id: Optional[str] = None,
    ):
        self.name = name
        self.transcript_id = transcript_id
        self.description = description
        self.metadata = metadata
        self.transcript_group_id = transcript_group_id
        self._sync_context: Optional[Any] = None
        self._async_context: Optional[Any] = None

    def __enter__(self) -> str:
        """Sync context manager entry."""
        self._sync_context = get_tracer().transcript_context(
            name=self.name,
            transcript_id=self.transcript_id,
            description=self.description,
            metadata=self.metadata,
            transcript_group_id=self.transcript_group_id,
        )
        return self._sync_context.__enter__()

    def __exit__(self, exc_type: type[BaseException], exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit."""
        if self._sync_context:
            self._sync_context.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> str:
        """Async context manager entry."""
        self._async_context = get_tracer().async_transcript_context(
            name=self.name,
            transcript_id=self.transcript_id,
            description=self.description,
            metadata=self.metadata,
            transcript_group_id=self.transcript_group_id,
        )
        return await self._async_context.__aenter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._async_context:
            await self._async_context.__aexit__(exc_type, exc_val, exc_tb)


def transcript(
    func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    transcript_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    transcript_group_id: Optional[str] = None,
):
    """
    Decorator to wrap a function in a transcript context.
    Injects transcript_id as a function attribute.

    Example:
        @transcript
        def my_func(x, y):
            print(my_func.docent.transcript_id)

        @transcript(name="data_processing", description="Process user data")
        def my_func_with_name(x, y):
            print(my_func_with_name.docent.transcript_id)

        @transcript(metadata={"user": "John", "model": "gpt-4"})
        async def my_async_func(z):
            print(my_async_func.docent.transcript_id)
    """
    import functools
    import inspect

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(f):

            @functools.wraps(f)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                async with TranscriptContext(
                    name=name,
                    transcript_id=transcript_id,
                    description=description,
                    metadata=metadata,
                    transcript_group_id=transcript_group_id,
                ) as transcript_id_result:
                    # Store docent data as function attributes
                    setattr(
                        async_wrapper,
                        "docent",
                        type(
                            "DocentData",
                            (),
                            {
                                "transcript_id": transcript_id_result,
                            },
                        )(),
                    )
                    return await f(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(f)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with TranscriptContext(
                    name=name,
                    transcript_id=transcript_id,
                    description=description,
                    metadata=metadata,
                    transcript_group_id=transcript_group_id,
                ) as transcript_id_result:
                    # Store docent data as function attributes
                    setattr(
                        sync_wrapper,
                        "docent",
                        type(
                            "DocentData",
                            (),
                            {
                                "transcript_id": transcript_id_result,
                            },
                        )(),
                    )
                    return f(*args, **kwargs)

            return sync_wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def transcript_context(
    name: Optional[str] = None,
    transcript_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    transcript_group_id: Optional[str] = None,
) -> TranscriptContext:
    """
    Create a transcript context for tracing.

    Args:
        name: Optional transcript name
        transcript_id: Optional transcript ID (auto-generated if not provided)
        description: Optional transcript description
        metadata: Optional metadata to attach to the transcript
        parent_transcript_id: Optional parent transcript ID

    Returns:
        A context manager that can be used with both 'with' and 'async with'

    Example:
        # Sync usage
        with transcript_context(name="data_processing") as transcript_id:
            pass

        # Async usage
        async with transcript_context(description="Process user data") as transcript_id:
            pass

        # With metadata
        with transcript_context(metadata={"user": "John", "model": "gpt-4"}) as transcript_id:
            pass
    """
    return TranscriptContext(name, transcript_id, description, metadata, transcript_group_id)


class TranscriptGroupContext:
    """Context manager for creating and managing transcript groups."""

    def __init__(
        self,
        name: Optional[str] = None,
        transcript_group_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_transcript_group_id: Optional[str] = None,
    ):
        self.name = name
        self.transcript_group_id = transcript_group_id
        self.description = description
        self.metadata = metadata
        self.parent_transcript_group_id = parent_transcript_group_id
        self._sync_context: Optional[Any] = None
        self._async_context: Optional[Any] = None

    def __enter__(self) -> str:
        """Sync context manager entry."""
        self._sync_context = get_tracer().transcript_group_context(
            name=self.name,
            transcript_group_id=self.transcript_group_id,
            description=self.description,
            metadata=self.metadata,
            parent_transcript_group_id=self.parent_transcript_group_id,
        )
        return self._sync_context.__enter__()

    def __exit__(self, exc_type: type[BaseException], exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit."""
        if self._sync_context:
            self._sync_context.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> str:
        """Async context manager entry."""
        self._async_context = get_tracer().async_transcript_group_context(
            name=self.name,
            transcript_group_id=self.transcript_group_id,
            description=self.description,
            metadata=self.metadata,
            parent_transcript_group_id=self.parent_transcript_group_id,
        )
        return await self._async_context.__aenter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._async_context:
            await self._async_context.__aexit__(exc_type, exc_val, exc_tb)


def transcript_group(
    func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    transcript_group_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_transcript_group_id: Optional[str] = None,
):
    """
    Decorator to wrap a function in a transcript group context.
    Injects transcript_group_id as a function attribute.

    Example:
        @transcript_group
        def my_func(x, y):
            print(my_func.docent.transcript_group_id)

        @transcript_group(name="data_processing", description="Process user data")
        def my_func_with_name(x, y):
            print(my_func_with_name.docent.transcript_group_id)

        @transcript_group(metadata={"user": "John", "model": "gpt-4"})
        async def my_async_func(z):
            print(my_async_func.docent.transcript_group_id)
    """
    import functools
    import inspect

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(f):

            @functools.wraps(f)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                async with TranscriptGroupContext(
                    name=name,
                    transcript_group_id=transcript_group_id,
                    description=description,
                    metadata=metadata,
                    parent_transcript_group_id=parent_transcript_group_id,
                ) as transcript_group_id_result:
                    # Store docent data as function attributes
                    setattr(
                        async_wrapper,
                        "docent",
                        type(
                            "DocentData",
                            (),
                            {
                                "transcript_group_id": transcript_group_id_result,
                            },
                        )(),
                    )
                    return await f(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(f)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with TranscriptGroupContext(
                    name=name,
                    transcript_group_id=transcript_group_id,
                    description=description,
                    metadata=metadata,
                    parent_transcript_group_id=parent_transcript_group_id,
                ) as transcript_group_id_result:
                    # Store docent data as function attributes
                    setattr(
                        sync_wrapper,
                        "docent",
                        type(
                            "DocentData",
                            (),
                            {
                                "transcript_group_id": transcript_group_id_result,
                            },
                        )(),
                    )
                    return f(*args, **kwargs)

            return sync_wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def transcript_group_context(
    name: Optional[str] = None,
    transcript_group_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    parent_transcript_group_id: Optional[str] = None,
) -> TranscriptGroupContext:
    """
    Create a transcript group context for tracing.

    Args:
        name: Optional transcript group name
        transcript_group_id: Optional transcript group ID (auto-generated if not provided)
        description: Optional transcript group description
        metadata: Optional metadata to attach to the transcript group
        parent_transcript_group_id: Optional parent transcript group ID

    Returns:
        A context manager that can be used with both 'with' and 'async with'

    Example:
        # Sync usage
        with transcript_group_context(name="data_processing") as transcript_group_id:
            pass

        # Async usage
        async with transcript_group_context(description="Process user data") as transcript_group_id:
            pass

        # With metadata
        with transcript_group_context(metadata={"user": "John", "model": "gpt-4"}) as transcript_group_id:
            pass
    """
    return TranscriptGroupContext(
        name, transcript_group_id, description, metadata, parent_transcript_group_id
    )


def _is_tracing_disabled() -> bool:
    """Check if tracing is disabled via environment variable."""
    return os.environ.get("DOCENT_DISABLE_TRACING", "").lower() == "true"


def _is_notebook() -> bool:
    """Check if we're running in a Jupyter notebook."""
    try:
        return "ipykernel" in sys.modules
    except Exception:
        return False
