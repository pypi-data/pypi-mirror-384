import asyncio
import os
import functools
import threading
import atexit
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

from opentelemetry import trace, context as otel_context
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from palantyra.api import BatchedAPIExporter, CustomAPIExporter


class TracingLevel(Enum):
    """Control the level of data captured in traces"""
    FULL = "full"          # Capture inputs, outputs, and metadata
    META_ONLY = "meta"     # Only metadata, no content
    DISABLED = "disabled"  # No tracing


@dataclass
class LLMMetrics:
    """Container for LLM-specific metrics"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    model: str = ""


class ObservabilitySDK:
    """Main SDK class that provides Laminar-like functionality built on OpenTelemetry"""
    
    def __init__(self):
        self._tracer = None
        self._instrumented = False
        self._project_api_key = None
        self._endpoint = None
        self._tracing_level = TracingLevel.FULL
        self._local_context = threading.local()
        self._tracer_provider = None
        self._shutdown_registered = False
        self._exporter = None # store reference to exporter
        
    def initialize(
        self,
        project_api_key: str,
        endpoint: Optional[str] = None,
        service_name: str = "llm-application",
        service_version: str = "1.0.0",
        auto_instrument: bool = True,
        use_batching: bool = True,
        auto_shutdown: bool = True,
        shutdown_timeout: int = 5000,
        tracing_level: TracingLevel = TracingLevel.FULL,
        **exporter_kwargs
    ):
        """Initialize the observability SDK"""
        self._project_api_key = project_api_key
        self._endpoint = endpoint or "http://localhost:8080/api/v1"
        self._tracing_level = tracing_level
        
        # Configure OpenTelemetry with custom resource
        # This is required to use our api with the open telemetry sdk
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "project.api_key": project_api_key
        })
        
        tracer_provider = TracerProvider(resource=resource)
        self._tracer_provider = tracer_provider

        # use custom exporter instead of OTLP
        if use_batching:
            exporter = BatchedAPIExporter(
                endpoint=self._endpoint,
                api_key=project_api_key,
                sdk_instance=self,
                **exporter_kwargs
            )
        else:
            exporter = CustomAPIExporter(
                endpoint=self._endpoint,
                api_key=project_api_key,
                sdk_instance=self,
                **exporter_kwargs
            )
        
        self._exporter = exporter # store reference
        
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)
        
        trace.set_tracer_provider(tracer_provider)
        self._tracer = trace.get_tracer(__name__)
        
        # Auto-instrument OpenAI and other LLM libraries
        if auto_instrument:
            self._instrument_libraries()
            
        self._instrumented = True

        # register automatic shutdown handler
        if auto_shutdown and not self._shutdown_registered:
            atexit.register(self._shutdown, shutdown_timeout)
            self._shutdown_registered = True
    

    def _shutdown(self, timeout_ms: int = 5000):
        """
        Shutdown the SDK and flush all pending spans.
        This is automatically called on program exit.
        """
        if not self._tracer_provider:
            return

        try:
            # force flush all pending spans
            self._tracer_provider.force_flush(timeout_millis=timeout_ms)

            # shutdown the tracer provider
            self._tracer_provider.shutdown()
            print(f"[Palantyra] Successfully flushed all traces.")
        except Exception as e:
            print(f"[Palantyra] Warning: Failed to flush traces on shutdown: {e}")
    

    def manual_shutdown(self, timeout_ms: int = 5000):
        """
        Manually trigger shutdown and flush.
        Useful for testing or when you want explicit control.
        """
        self._shutdown(timeout_ms=timeout_ms)
        
        
    def _instrument_libraries(self):
        """Automatically instrument supported LLM libraries"""
        # OpenAI instrumentation
        OpenAIInstrumentor().instrument()
        
        # Add other instrumentations as needed
        # AnthropicInstrumentor().instrument()
        # LangChainInstrumentor().instrument()
        
    def observe(
        self,
        name: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        ignore_input: bool = False,
        ignore_output: bool = False,
        ignore_inputs: Optional[List[str]] = None
    ):
        """Decorator to observe function execution (similar to Laminar's @observe)"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._execute_with_observation(
                    func, args, kwargs, name, session_id, user_id, 
                    metadata, tags, ignore_input, ignore_output, ignore_inputs
                )
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_with_observation_async(
                    func, args, kwargs, name, session_id, user_id,
                    metadata, tags, ignore_input, ignore_output, ignore_inputs
                )
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _execute_with_observation(
        self, func, args, kwargs, name, session_id, user_id, 
        metadata, tags, ignore_input, ignore_output, ignore_inputs
    ):
        """Execute function with observation (sync version)"""
        span_name = name or func.__name__
        
        with self.start_as_current_span(
            name=span_name,
            input=self._prepare_input(args, kwargs, ignore_input, ignore_inputs),
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
            tags=tags
        ) as span:
            try:
                result = func(*args, **kwargs)
                if not ignore_output:
                    self.set_span_output(result)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    
    async def _execute_with_observation_async(
        self, func, args, kwargs, name, session_id, user_id,
        metadata, tags, ignore_input, ignore_output, ignore_inputs
    ):
        """Execute function with observation (async version)"""
        span_name = name or func.__name__
        
        with self.start_as_current_span(
            name=span_name,
            input=self._prepare_input(args, kwargs, ignore_input, ignore_inputs),
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
            tags=tags
        ) as span:
            try:
                result = await func(*args, **kwargs)
                if not ignore_output:
                    self.set_span_output(result)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    
    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        input: Any = None,
        span_type: str = "DEFAULT",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """Start a span as current span (similar to Laminar's manual span creation)"""
        if not self._instrumented:
            raise RuntimeError("SDK not initialized. Call initialize() first.")
            
        span = self._tracer.start_span(
            name=name,
            kind=SpanKind.INTERNAL
        )
        
        # Set span attributes
        if input is not None and self._tracing_level != TracingLevel.META_ONLY:
            span.set_attribute("input", self._serialize_data(input))
            
        if span_type:
            span.set_attribute("span.type", span_type)
            
        if session_id:
            span.set_attribute("session.id", session_id)
            
        if user_id:
            span.set_attribute("user.id", user_id)
            
        if metadata:
            for key, value in metadata.items():
                span.set_attribute(f"metadata.{key}", str(value))
                
        if tags:
            span.set_attribute("tags", ",".join(tags))
        
        # Store span in context for later reference
        token = otel_context.attach(trace.set_span_in_context(span))
        
        try:
            yield span
        finally:
            otel_context.detach(token)
            span.end()
    
    def set_trace_session_id(self, session_id: str):
        """Set session ID for the current trace"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("session.id", session_id)
    
    def set_trace_user_id(self, user_id: str):
        """Set user ID for the current trace"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("user.id", user_id)
    
    def set_span_metadata(self, **metadata):
        """Set metadata for the current span"""
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in metadata.items():
                span.set_attribute(f"metadata.{key}", str(value))
    
    def set_span_output(self, output: Any):
        """Set output for the current span"""
        print("-----------------")
        print(self._tracing_level)
        if self._tracing_level == TracingLevel.META_ONLY:
            return
            
        span = trace.get_current_span()
        if span and span.is_recording():
            span.set_attribute("output", self._serialize_data(output))
    
    def set_span_attributes(self, attributes: Dict[str, Any]):
        """Set custom attributes on the current span"""
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
    
    @contextmanager
    def set_tracing_level(self, level: TracingLevel):
        """Temporarily change tracing level"""
        original_level = self._tracing_level
        self._tracing_level = level
        print("from set_tracing_level in __init__.py: ", self._tracing_level)
        # NEW: Also update exporter's reference
        if self._exporter:
            self._exporter._update_tracing_level(level)
        try:
            yield
        finally:
            self._tracing_level = original_level
            # NEW: Restore exporter's level
            if self._exporter:
                self._exporter._update_tracing_level(original_level)
    
    def _prepare_input(self, args, kwargs, ignore_input, ignore_inputs):
        """Prepare input data for span"""
        if ignore_input or self._tracing_level == TracingLevel.META_ONLY:
            return None
            
        input_data = {}
        
        # Add positional arguments
        if args:
            for i, arg in enumerate(args):
                if not ignore_inputs or f"arg_{i}" not in ignore_inputs:
                    input_data[f"arg_{i}"] = arg
        
        # Add keyword arguments
        if kwargs:
            for key, value in kwargs.items():
                if not ignore_inputs or key not in ignore_inputs:
                    input_data[key] = value
                    
        return input_data
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for storage in spans"""
        try:
            import json
            return json.dumps(data, default=str)
        except Exception:
            return str(data)


# Global SDK instance
_sdk = ObservabilitySDK()

# Convenience functions that mirror Laminar's API
def initialize(project_api_key: str, **kwargs):
    """Initialize the SDK (mirrors Laminar.initialize)"""
    return _sdk.initialize(project_api_key, **kwargs)

def shutdown(timeout_ms: int = 5000):
    """
    Manually shutdown the SDK and flush all traces.
    This is automatically called on program exit, but you can call it manually if needed.
    """
    return _sdk.manual_shutdown(timeout_ms)

def observe(**kwargs):
    """Observe decorator (mirrors Laminar's @observe)"""
    return _sdk.observe(**kwargs)

def start_as_current_span(**kwargs):
    """Start span as current (mirrors Laminar.start_as_current_span)"""
    return _sdk.start_as_current_span(**kwargs)

def set_trace_session_id(session_id: str):
    """Set session ID (mirrors Laminar.set_trace_session_id)"""
    return _sdk.set_trace_session_id(session_id)

def set_trace_user_id(user_id: str):
    """Set user ID (mirrors Laminar.set_trace_user_id)"""
    return _sdk.set_trace_user_id(user_id)

def set_span_metadata(**metadata):
    """Set metadata (mirrors Laminar.set_span_metadata)"""
    return _sdk.set_span_metadata(**metadata)

def set_span_output(output: Any):
    """Set span output (mirrors Laminar.set_span_output)"""
    return _sdk.set_span_output(output)

def set_span_attributes(attributes: Dict[str, Any]):
    """Set span attributes (mirrors Laminar.set_span_attributes)"""
    return _sdk.set_span_attributes(attributes)

def set_tracing_level(level: TracingLevel):
    """Set tracing level (mirrors Laminar.set_tracing_level)"""
    return _sdk.set_tracing_level(level)


# Export main classes and functions
__all__ = [
    'ObservabilitySDK', 'TracingLevel', 'LLMMetrics',
    'initialize', 'observe', 'start_as_current_span',
    'set_trace_session_id', 'set_trace_user_id', 'set_span_metadata',
    'set_span_output', 'set_span_attributes', 'set_tracing_level', 'shutdown'
]