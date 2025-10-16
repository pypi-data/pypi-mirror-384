"""
Additional components for the LLM Observability SDK
Includes cost calculation, configuration, and extended instrumentation
"""

import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum

from opentelemetry import trace
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor


# ===== COST CALCULATION =====

@dataclass
class ModelPricing:
    """Pricing information for a model"""
    input_cost_per_1k: float  # Cost per 1000 input tokens
    output_cost_per_1k: float  # Cost per 1000 output tokens
    model_name: str
    provider: str


class CostCalculator:
    """Calculate costs for LLM API calls"""
    
    # Pricing data (as of 2024 - update as needed)
    PRICING_DATA = {
        "openai": {
            "gpt-4o": ModelPricing(0.005, 0.015, "gpt-4o", "openai"),
            "gpt-4o-mini": ModelPricing(0.00015, 0.0006, "gpt-4o-mini", "openai"),
            "gpt-4-turbo": ModelPricing(0.01, 0.03, "gpt-4-turbo", "openai"),
            "gpt-3.5-turbo": ModelPricing(0.0005, 0.0015, "gpt-3.5-turbo", "openai"),
            "text-embedding-ada-002": ModelPricing(0.0001, 0.0, "text-embedding-ada-002", "openai"),
        },
        "anthropic": {
            "claude-3-opus": ModelPricing(0.015, 0.075, "claude-3-opus", "anthropic"),
            "claude-3-sonnet": ModelPricing(0.003, 0.015, "claude-3-sonnet", "anthropic"),
            "claude-3-haiku": ModelPricing(0.00025, 0.00125, "claude-3-haiku", "anthropic"),
        },
        "google": {
            "gemini-pro": ModelPricing(0.0005, 0.0015, "gemini-pro", "google"),
            "gemini-pro-vision": ModelPricing(0.0005, 0.0015, "gemini-pro-vision", "google"),
        }
    }
    
    @classmethod
    def calculate_cost(
        cls, 
        model: str, 
        input_tokens: int, 
        output_tokens: int,
        provider: str = "openai"
    ) -> float:
        """Calculate cost for an LLM API call"""
        pricing_data = cls.PRICING_DATA.get(provider, {})
        model_pricing = pricing_data.get(model)
        
        if not model_pricing:
            # Return 0 for unknown models, but log warning
            print(f"Warning: No pricing data for {provider}/{model}")
            return 0.0
        
        input_cost = (input_tokens / 1000) * model_pricing.input_cost_per_1k
        output_cost = (output_tokens / 1000) * model_pricing.output_cost_per_1k
        
        return input_cost + output_cost
    
    @classmethod
    def add_cost_to_span(
        cls,
        span: trace.Span,
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = "openai"
    ):
        """Add cost information to a span"""
        if not span or not span.is_recording():
            return
            
        cost = cls.calculate_cost(model, input_tokens, output_tokens, provider)
        span.set_attribute("llm.cost.total", cost)
        span.set_attribute("llm.cost.input", (input_tokens / 1000) * cls.PRICING_DATA[provider][model].input_cost_per_1k)
        span.set_attribute("llm.cost.output", (output_tokens / 1000) * cls.PRICING_DATA[provider][model].output_cost_per_1k)
        span.set_attribute("llm.cost.currency", "USD")


# ===== CONFIGURATION MANAGEMENT =====

@dataclass
class SDKConfig:
    """Configuration for the SDK"""
    project_api_key: str
    endpoint: Optional[str] = None
    service_name: str = "llm-application"
    service_version: str = "1.0.0"
    auto_instrument: bool = True
    enable_cost_tracking: bool = True
    sample_rate: float = 1.0  # 0.0 to 1.0
    max_span_attributes: int = 100
    enable_content_logging: bool = True
    content_logging_sample_rate: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'SDKConfig':
        """Create configuration from environment variables"""
        import os
        return cls(
            project_api_key=os.environ["LLM_OBSERVABILITY_API_KEY"],
            endpoint=os.environ.get("LLM_OBSERVABILITY_ENDPOINT"),
            service_name=os.environ.get("LLM_OBSERVABILITY_SERVICE_NAME", "llm-application"),
            service_version=os.environ.get("LLM_OBSERVABILITY_SERVICE_VERSION", "1.0.0"),
            auto_instrument=os.environ.get("LLM_OBSERVABILITY_AUTO_INSTRUMENT", "true").lower() == "true",
            enable_cost_tracking=os.environ.get("LLM_OBSERVABILITY_COST_TRACKING", "true").lower() == "true",
            sample_rate=float(os.environ.get("LLM_OBSERVABILITY_SAMPLE_RATE", "1.0")),
            enable_content_logging=os.environ.get("LLM_OBSERVABILITY_CONTENT_LOGGING", "true").lower() == "true",
        )


# ===== ENHANCED INSTRUMENTORS =====

class AnthropicInstrumentor(BaseInstrumentor):
    """Instrumentor for Anthropic Claude API calls"""
    
    def instrumentation_dependencies(self):
        return ["anthropic >= 0.3.0"]
    
    def _instrument(self, **kwargs):
        """Instrument Anthropic library"""
        try:
            import anthropic
            from wrapt import wrap_function_wrapper
            
            wrap_function_wrapper(
                "anthropic.resources.messages",
                "Messages.create",
                self._trace_anthropic_call
            )
            
        except ImportError:
            pass
    
    def _uninstrument(self, **kwargs):
        """Uninstrument Anthropic library"""
        pass
    
    def _trace_anthropic_call(self, wrapped, instance, args, kwargs):
        """Trace Anthropic API calls"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_span(
            "anthropic.messages.create",
            kind=trace.SpanKind.CLIENT
        ) as span:
            # Add request attributes
            span.set_attribute("llm.system", "anthropic")
            span.set_attribute("llm.request.model", kwargs.get("model", "unknown"))
            span.set_attribute("llm.request.max_tokens", kwargs.get("max_tokens", 0))
            
            # Add messages if content logging is enabled
            if kwargs.get("messages"):
                messages_json = json.dumps(kwargs["messages"])
                span.set_attribute("llm.request.messages", messages_json)
            
            try:
                start_time = time.time()
                response = wrapped(*args, **kwargs)
                end_time = time.time()
                
                # Add response attributes
                span.set_attribute("llm.response.model", getattr(response, "model", "unknown"))
                span.set_attribute("llm.latency", (end_time - start_time) * 1000)
                
                # Add usage information if available
                if hasattr(response, "usage") and response.usage:
                    usage = response.usage
                    span.set_attribute("llm.usage.input_tokens", usage.input_tokens)
                    span.set_attribute("llm.usage.output_tokens", usage.output_tokens)
                    
                    # Calculate and add cost
                    CostCalculator.add_cost_to_span(
                        span, kwargs.get("model", "unknown"),
                        usage.input_tokens, usage.output_tokens, "anthropic"
                    )
                
                return response
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise


class GoogleAIInstrumentor(BaseInstrumentor):
    """Instrumentor for Google AI (Gemini) API calls"""
    
    def instrumentation_dependencies(self):
        return ["google-generativeai >= 0.3.0"]
    
    def _instrument(self, **kwargs):
        """Instrument Google AI library"""
        try:
            import google.generativeai as genai
            from wrapt import wrap_function_wrapper
            
            wrap_function_wrapper(
                "google.generativeai.generative_models",
                "GenerativeModel.generate_content",
                self._trace_google_ai_call
            )
            
        except ImportError:
            pass
    
    def _uninstrument(self, **kwargs):
        """Uninstrument Google AI library"""
        pass
    
    def _trace_google_ai_call(self, wrapped, instance, args, kwargs):
        """Trace Google AI API calls"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_span(
            "google.generativeai.generate_content",
            kind=trace.SpanKind.CLIENT
        ) as span:
            # Add request attributes
            span.set_attribute("llm.system", "google")
            span.set_attribute("llm.request.model", getattr(instance, "_model_name", "unknown"))
            
            try:
                start_time = time.time()
                response = wrapped(*args, **kwargs)
                end_time = time.time()
                
                # Add response attributes
                span.set_attribute("llm.latency", (end_time - start_time) * 1000)
                
                # Add usage information if available
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    span.set_attribute("llm.usage.input_tokens", usage.prompt_token_count)
                    span.set_attribute("llm.usage.output_tokens", usage.candidates_token_count)
                    
                    # Calculate and add cost
                    CostCalculator.add_cost_to_span(
                        span, getattr(instance, "_model_name", "gemini-pro"),
                        usage.prompt_token_count, usage.candidates_token_count, "google"
                    )
                
                return response
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise


# ===== ENHANCED SDK WITH ADDITIONAL FEATURES =====

class EnhancedObservabilitySDK:
    """Enhanced SDK with additional features"""
    
    def __init__(self):
        self._config: Optional[SDKConfig] = None
        self._instrumentors = {}
        self._cost_calculator = CostCalculator()
        
    def initialize_from_config(self, config: SDKConfig):
        """Initialize from configuration object"""
        self._config = config
        
        # Initialize base SDK
        from llm_observability import initialize
        initialize(
            project_api_key=config.project_api_key,
            endpoint=config.endpoint,
            service_name=config.service_name,
            service_version=config.service_version,
            auto_instrument=False  # We'll handle instrumentation manually
        )
        
        # Setup instrumentors
        if config.auto_instrument:
            self._setup_instrumentors()
    
    def _setup_instrumentors(self):
        """Setup all available instrumentors"""
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor
        
        instrumentors = [
            ("openai", OpenAIInstrumentor()),
            ("anthropic", AnthropicInstrumentor()),
            ("google", GoogleAIInstrumentor()),
        ]
        
        for name, instrumentor in instrumentors:
            try:
                instrumentor.instrument()
                self._instrumentors[name] = instrumentor
                print(f"Successfully instrumented {name}")
            except Exception as e:
                print(f"Failed to instrument {name}: {e}")
    
    def add_cost_tracking_to_current_span(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int,
        provider: str = "openai"
    ):
        """Add cost tracking to current span"""
        if not self._config or not self._config.enable_cost_tracking:
            return
            
        span = trace.get_current_span()
        if span and span.is_recording():
            self._cost_calculator.add_cost_to_span(
                span, model, input_tokens, output_tokens, provider
            )
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of current trace"""
        span = trace.get_current_span()
        if not span or not span.is_recording():
            return {}
        
        span_context = span.get_span_context()
        return {
            "trace_id": format(span_context.trace_id, "032x"),
            "span_id": format(span_context.span_id, "016x"),
            "trace_flags": span_context.trace_flags,
        }


# ===== METRICS COLLECTION =====

class MetricsCollector:
    """Collect and aggregate metrics from traces"""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_latency": 0.0,
            "error_count": 0,
        }
    
    def record_llm_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost: float = 0.0,
        error: bool = False
    ):
        """Record metrics for an LLM call"""
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens"] += input_tokens + output_tokens
        self.metrics["total_cost"] += cost
        
        # Update average latency
        self.metrics["average_latency"] = (
            (self.metrics["average_latency"] * (self.metrics["total_requests"] - 1) + latency_ms)
            / self.metrics["total_requests"]
        )
        
        if error:
            self.metrics["error_count"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_latency": 0.0,
            "error_count": 0,
        }


# ===== UTILITY FUNCTIONS =====

def get_trace_url(trace_id: str, base_url: str = "https://your-platform.com") -> str:
    """Generate URL to view trace in UI"""
    return f"{base_url}/traces/{trace_id}"


def export_trace_data(trace_id: str, format: str = "json") -> str:
    """Export trace data in specified format"""
    # This would integrate with your backend to fetch trace data
    # For now, return placeholder
    return json.dumps({
        "trace_id": trace_id,
        "exported_at": time.time(),
        "format": format
    })


class TraceAnalyzer:
    """Analyze traces for insights"""
    
    @staticmethod
    def analyze_performance(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance across multiple traces"""
        if not traces:
            return {}
        
        total_latency = sum(t.get("latency", 0) for t in traces)
        total_cost = sum(t.get("cost", 0) for t in traces)
        error_count = sum(1 for t in traces if t.get("error", False))
        
        return {
            "total_traces": len(traces),
            "average_latency": total_latency / len(traces),
            "total_cost": total_cost,
            "error_rate": error_count / len(traces),
            "cost_per_trace": total_cost / len(traces)
        }
    
    @staticmethod
    def find_bottlenecks(trace_spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find performance bottlenecks in trace spans"""
        # Sort spans by duration
        sorted_spans = sorted(
            trace_spans, 
            key=lambda x: x.get("duration", 0), 
            reverse=True
        )
        
        # Return top 5 slowest spans
        return sorted_spans[:5]


# Export all components
__all__ = [
    'CostCalculator', 'SDKConfig', 'AnthropicInstrumentor', 
    'GoogleAIInstrumentor', 'EnhancedObservabilitySDK',
    'MetricsCollector', 'TraceAnalyzer', 'get_trace_url', 'export_trace_data'
]