"""
Custom API Exporter for sending traces to your specific API endpoint
This replaces the OTLP exporter with a custom one that formats data for your API
"""

import json
import time
import requests
import threading
from typing import Dict, Any, List, Optional, Sequence
from dataclasses import dataclass
from queue import Queue, Empty

from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import Span
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace.status import StatusCode


@dataclass
class TraceData:
    """Structured trace data for API submission"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: float
    end_time: float
    duration_ms: float
    status: str
    attributes: Dict[str, Any]
    events: List[Dict[str, Any]]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None


class CustomAPIExporter(SpanExporter):
    """Custom exporter that sends trace data to your API endpoint"""

    # NEW: List of attributes to filter out in META_ONLY mode
    SENSITIVE_ATTRIBUTES = [
        "input",                          # Palantyra input
        "output",                         # Palantyra output
        "llm.request.messages",          # OpenAI request messages
        "llm.response.content",          # Response content
        "gen_ai.prompt",                 # Generic AI prompt
        "gen_ai.completion",             # Generic AI completion
        "gen_ai.response.text",          # Response text
        "llm.prompts",                   # Alternative prompt field
        "llm.completions",               # Alternative completion field
    ]
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        timeout: int = 30,
        max_export_batch_size: int = 512,
        headers: Optional[Dict[str, str]] = None,
        sdk_instance = None
    ):
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_export_batch_size = max_export_batch_size
        self._sdk_instance = sdk_instance
        self._current_tracing_level = None
        
        # Setup headers
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": f"{api_key}",
            "User-Agent": "LLM-Observability-SDK/1.0.0"
        }
        if headers:
            self.headers.update(headers)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _update_tracing_level(self, level):
        """NEW: Update cached tracing level"""
        print("from _update_tracing_level in api.py: ", level)
        self._current_tracing_level = level
    
    def _get_tracing_level(self):
        print("from _current_tracing_level in api.py: ", self._current_tracing_level)
        """NEW: Get current tracing level"""
        if self._current_tracing_level:
            return self._current_tracing_level
        # print(self._sdk_instance._tracing_level)
        if self._sdk_instance:
            return self._sdk_instance._tracing_level
        # Import here to avoid circular dependency
        from palantyra import TracingLevel
        return TracingLevel.FULL

    def _filter_sensitive_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """NEW: Filter out sensitive content based on tracing level"""
        from palantyra import TracingLevel
        
        tracing_level = self._get_tracing_level()
        
        if tracing_level == TracingLevel.FULL:
            # No filtering needed
            return attributes
        
        if tracing_level == TracingLevel.META_ONLY:
            # Remove all sensitive attributes
            filtered = {}
            for key, value in attributes.items():
                # Check if this is a sensitive attribute
                is_sensitive = any(
                    key == sensitive_attr or key.startswith(sensitive_attr + ".")
                    for sensitive_attr in self.SENSITIVE_ATTRIBUTES
                )
                
                if not is_sensitive:
                    filtered[key] = value
                else:
                    # Optionally log what we're filtering (for debugging)
                    # print(f"[TracingLevel.META_ONLY] Filtering attribute: {key}")
                    pass
            
            return filtered
        
        # DISABLED - return empty attributes
        return {}

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to the API"""
        if not spans:
            return SpanExportResult.SUCCESS
        
        try:
            # Convert spans to our format
            trace_data = self._convert_spans_to_trace_data(spans)
            
            # Group by trace_id for better organization
            traces_by_id = self._group_spans_by_trace(trace_data)
            
            # Send each trace
            for trace_id, spans_data in traces_by_id.items():
                success = self._send_trace_to_api(trace_id, spans_data)
                if not success:
                    return SpanExportResult.FAILURE
            
            return SpanExportResult.SUCCESS
            
        except Exception as e:
            print(f"Error exporting spans: {e}")
            return SpanExportResult.FAILURE
    
    def _convert_spans_to_trace_data(self, spans: Sequence[ReadableSpan]) -> List[TraceData]:
        """Convert OpenTelemetry spans to our TraceData format"""
        trace_data_list = []

        # first pass: build span lookup map
        span_map = {}
        for span in spans:
            span_context = span.get_span_context()
            span_id = format(span_context.span_id, "016x")
            span_map[span_id] = span
        
        for span in spans:
            # Extract basic span information
            span_context = span.get_span_context()
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
            
            # Get parent span ID if exists
            parent_span_id = None
            if span.parent and span.parent.span_id:
                parent_span_id = format(span.parent.span_id, "016x")
            
            # Calculate duration
            start_time = span.start_time / 1_000_000  # Convert to milliseconds
            end_time = span.end_time / 1_000_000 if span.end_time else time.time() * 1000
            duration_ms = end_time - start_time
            
            # Convert status
            status = "ok"
            if span.status.status_code == StatusCode.ERROR:
                status = "error"
            elif span.status.status_code == StatusCode.UNSET:
                status = "unset"
            
            # Extract attributes and separate our custom ones
            attributes = dict(span.attributes) if span.attributes else {}

            # Fitler sensitive attributes based on tracing level
            attributes = self._filter_sensitive_attributes(attributes=attributes)

            session_id = attributes.pop("session.id", None)
            user_id = attributes.pop("user.id", None)
            
            # Extract metadata (attributes starting with "metadata.")
            metadata = {}
            for key in list(attributes.keys()):
                if key.startswith("metadata."):
                    metadata[key[9:]] = attributes.pop(key)  # Remove "metadata." prefix
            

            # Inherit from paren span if not set
            if parent_span_id and parent_span_id in span_map:
                parent_span = span_map[parent_span_id]
                parent_attrs = dict(parent_span.attributes) if parent_span.attributes else {}

                # inherit session_id if not set
                if not session_id and "session.id" in parent_attrs:
                    session_id = parent_attrs["session.id"]
                
                # inherit user_id if not set
                if not user_id and "user.id" in parent_attrs:
                    user_id = parent_attrs["user.id"]
                
                # inherit metadata if not set
                if not metadata:
                    for key, value in parent_attrs.items():
                        if key.startswith("metadata."):
                            metadata[key[9:]] = value
            
            # Convert events
            events = []
            if span.events:
                for event in span.events:
                    
                    event_attributes = dict(event.attributes) if event.attributes else {}

                    # filter event attribute
                    event_attributes = self._filter_sensitive_attributes(event_attributes)

                    events.append({
                        "name": event.name,
                        "timestamp": event.timestamp / 1_000_000,  # Convert to milliseconds
                        "attributes": dict(event.attributes) if event.attributes else {}
                    })
            
            trace_data = TraceData(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=span.name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status=status,
                attributes=attributes,
                events=events,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )
            
            trace_data_list.append(trace_data)
        
        return trace_data_list
    
    def _group_spans_by_trace(self, trace_data_list: List[TraceData]) -> Dict[str, List[TraceData]]:
        """Group spans by trace ID"""
        traces = {}
        for trace_data in trace_data_list:
            if trace_data.trace_id not in traces:
                traces[trace_data.trace_id] = []
            traces[trace_data.trace_id].append(trace_data)
        return traces
    
    def _send_trace_to_api(self, trace_id: str, spans_data: List[TraceData]) -> bool:
        """Send a complete trace to the API"""
        try:
            # Build the payload in the format your API expects
            payload = {
                "trace_id": trace_id,
                "timestamp": time.time(),
                "spans": [self._span_to_dict(span_data) for span_data in spans_data],
                "metadata": {
                    "sdk_version": "1.0.0",
                    "exported_at": time.time()
                }
            }

            # find the root span (no parent) to extract trace-level session/user
            root_span = None
            for span_data in spans_data:
                if span_data.parent_span_id is None:
                    root_span = span_data
                    break
            
            # if not root found, fall back to first span
            if not root_span and spans_data:
                root_span = spans_data[0]
            
            # Add trace-level session and user if available
            if root_span:
                if root_span.session_id:
                    payload["session_id"] = root_span.session_id
                if root_span.user_id:
                    payload["user_id"] = root_span.user_id
            
            
            print(payload)
            
            # Send to API
            response = self.session.post(
                f"{self.endpoint}/traces",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"API returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to send trace {trace_id}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending trace {trace_id}: {e}")
            return False
    
    def _span_to_dict(self, span_data: TraceData) -> Dict[str, Any]:
        """Convert TraceData to dictionary for API"""
        return {
            "span_id": span_data.span_id,
            "parent_span_id": span_data.parent_span_id,
            "name": span_data.name,
            "start_time": span_data.start_time,
            "end_time": span_data.end_time,
            "duration_ms": span_data.duration_ms,
            "status": span_data.status,
            "attributes": span_data.attributes,
            "events": span_data.events,
            "metadata": span_data.metadata or {}
        }
    
    def shutdown(self):
        """Shutdown the exporter"""
        self.session.close()


class BatchedAPIExporter(CustomAPIExporter):
    """
    Batched version that collects spans and sends them in batches
    Better for high-volume applications
    """
    
    def __init__(self, *args, batch_size: int = 100, flush_interval: int = 5, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.span_queue = Queue()
        self.shutdown_event = threading.Event()
        
        # Start background thread for batching
        self.batch_thread = threading.Thread(target=self._batch_worker, daemon=True)
        self.batch_thread.start()
    
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Add spans to batch queue"""
        try:
            for span in spans:
                self.span_queue.put(span)
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Error queuing spans: {e}")
            return SpanExportResult.FAILURE
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """
        Force flush all queued spans immediately.
        Waits for the queue to be empty or timeout.
        """
        import time
        start_time = time.time()
        timeout_seconds = timeout_millis / 1000.0
        
        # Wait for queue to be empty
        while not self.span_queue.empty():
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                print(f"[Palantyra] Warning: force_flush timed out with {self.span_queue.qsize()} spans remaining")
                return False
            time.sleep(0.1)  # Check every 100ms
        
        return True
    
    def _batch_worker(self):
        """Background worker that processes batches"""
        batch = []
        last_flush = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                # Try to get span with timeout
                span = self.span_queue.get(timeout=1.0)
                batch.append(span)
                
                # Flush if batch is full or enough time has passed
                current_time = time.time()
                should_flush = (
                    len(batch) >= self.batch_size or 
                    (current_time - last_flush) >= self.flush_interval
                )
                
                if should_flush and batch:
                    super().export(batch)
                    batch = []
                    last_flush = current_time
                    
            except Empty:
                # Timeout occurred, flush if we have spans and enough time passed
                current_time = time.time()
                if batch and (current_time - last_flush) >= self.flush_interval:
                    super().export(batch)
                    batch = []
                    last_flush = current_time
        
        # Flush remaining spans on shutdown
        if batch:
            super().export(batch)
    
    def shutdown(self):
        """Shutdown the batched exporter"""
        # First, flush any remaining spans
        self.force_flush(timeout_millis=5000)
        
        # Then stop the worker thread
        self.shutdown_event.set()
        self.batch_thread.join(timeout=5)
        super().shutdown()


# # Updated SDK initialization to use custom exporter
# def initialize_with_custom_api(
#     project_api_key: str,
#     api_endpoint: str,
#     service_name: str = "llm-application",
#     service_version: str = "1.0.0",
#     use_batching: bool = True,
#     **exporter_kwargs
# ):
#     """Initialize SDK with custom API exporter"""
#     from opentelemetry import trace
#     from opentelemetry.sdk.trace import TracerProvider
#     from opentelemetry.sdk.trace.export import BatchSpanProcessor
#     from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    
#     # Configure OpenTelemetry with custom resource
#     resource = Resource.create({
#         SERVICE_NAME: service_name,
#         SERVICE_VERSION: service_version,
#         "project.api_key": project_api_key
#     })
    
#     tracer_provider = TracerProvider(resource=resource)
    
#     # Use custom exporter instead of OTLP
#     if use_batching:
#         exporter = BatchedAPIExporter(
#             endpoint=api_endpoint,
#             api_key=project_api_key,
#             **exporter_kwargs
#         )
#     else:
#         exporter = CustomAPIExporter(
#             endpoint=api_endpoint,
#             api_key=project_api_key,
#             **exporter_kwargs
#         )
    
#     # Add span processor
#     span_processor = BatchSpanProcessor(exporter)
#     tracer_provider.add_span_processor(span_processor)
    
#     # Set global tracer provider
#     trace.set_tracer_provider(tracer_provider)
    
#     return tracer_provider


# # Example usage
# if __name__ == "__main__":
#     # Initialize with your actual API endpoint
#     initialize_with_custom_api(
#         project_api_key="your-api-key-here",
#         api_endpoint="https://your-api.com/v1",  # Your actual API endpoint
#         service_name="my-llm-app",
#         use_batching=True,
#         batch_size=50,
#         flush_interval=3
#     )
    
#     # Now all traces will be sent to your API
#     from openai import OpenAI
#     client = OpenAI()
    
#     # This will be traced and sent to your API
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": "Hello!"}]
#     )