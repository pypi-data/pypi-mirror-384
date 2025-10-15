"""
Exporters for sending monitoring data to various backends.
"""
import json
import time
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self, config):
        self.config = config
        
    @abstractmethod
    def export_llm_call(self, llm_call):
        """Export an LLM call."""
        pass
        
    @abstractmethod
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics."""
        pass

class LogExporter(BaseExporter):
    """Export monitoring data to logs."""
    
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger("ai_monitor.export")
        
        # Configure logger
        if config.log_file:
            handler = logging.FileHandler(config.log_file)
        else:
            handler = logging.StreamHandler()
            
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
    
    def export_llm_call(self, llm_call):
        """Export LLM call to logs."""
        log_data = {
            'type': 'llm_call',
            'id': llm_call.id,
            'timestamp': llm_call.timestamp.isoformat(),
            'model': llm_call.model,
            'input_tokens': llm_call.input_tokens,
            'output_tokens': llm_call.output_tokens,
            'total_tokens': llm_call.total_tokens,
            'latency': llm_call.latency,
            'cost': llm_call.cost,
            'prompt_length': len(llm_call.prompt),
            'response_length': len(llm_call.response),
            'metadata': llm_call.metadata
        }
        
        self.logger.info(f"LLM_CALL: {json.dumps(log_data)}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics to logs."""
        for metric_name, values in metrics.items():
            if values:  # Only export if we have data
                latest_value = values[-1]  # Get most recent value
                log_data = {
                    'type': 'metric',
                    'name': metric_name,
                    'value': latest_value[1],
                    'timestamp': latest_value[0]
                }
                self.logger.debug(f"METRIC: {json.dumps(log_data)}")

class PrometheusExporter(BaseExporter):
    """Export monitoring data to Prometheus."""
    
    _instance = None
    _metrics_initialized = False
    
    def __new__(cls, config):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config):
        if hasattr(self, '_initialized'):
            return
        super().__init__(config)
        self._setup_prometheus()
        self._initialized = True
        
    def _setup_prometheus(self):
        """Setup Prometheus metrics."""
        if self._metrics_initialized:
            return
            
        try:
            from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry, REGISTRY
            
            # Check if metrics already exist
            existing_names = {collector._name for collector in REGISTRY._collector_to_names.keys() 
                            if hasattr(collector, '_name')}
            
            if 'ai_monitor_llm_calls_total' in existing_names:
                logger.info("Prometheus metrics already initialized, reusing existing metrics")
                self._metrics_initialized = True
                return
            
            # Define metrics
            self.llm_calls_total = Counter(
                'ai_monitor_llm_calls_total',
                'Total number of LLM calls',
                ['model']
            )
            
            self.llm_latency = Histogram(
                'ai_monitor_llm_latency_seconds',
                'LLM call latency',
                ['model'],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
            )
            
            self.llm_tokens = Counter(
                'ai_monitor_tokens_total',
                'Total tokens processed',
                ['model', 'type']  # type: input/output
            )
            
            self.llm_cost = Counter(
                'ai_monitor_cost_total',
                'Total cost',
                ['model']
            )
            
            self.agent_sessions = Counter(
                'ai_monitor_agent_sessions_total',
                'Total agent sessions',
                ['agent', 'status']  # status: started/completed/failed
            )
            
            self.tool_calls = Counter(
                'ai_monitor_tool_calls_total', 
                'Total tool calls',
                ['tool', 'status']  # status: success/error
            )
            
            # AI Quality Metrics
            self.quality_scores = Histogram(
                'ai_monitor_quality_score',
                'AI response quality scores',
                ['model'],
                buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0]
            )
            
            self.hallucination_risk = Counter(
                'ai_monitor_hallucination_risk_total',
                'Hallucination risk detections',
                ['model', 'risk_level']  # risk_level: low/medium/high
            )
            
            self.drift_detections = Counter(
                'ai_monitor_drift_detections_total',
                'Response drift detections',
                ['model', 'drift_type']  # drift_type: detected/not_detected
            )
            
            self.quality_issues = Counter(
                'ai_monitor_quality_issues_total',
                'Quality issues detected',
                ['model', 'issue_type']
            )
            
            # Start HTTP server (only if not already started)
            if not hasattr(self, '_server_started') or not self._server_started:
                start_http_server(self.config.prometheus_port)
                self._server_started = True
                logger.info(f"Prometheus metrics server started on port {self.config.prometheus_port}")
            
            self._metrics_initialized = True
            
        except ImportError:
            logger.warning("prometheus_client not installed, Prometheus export disabled")
            self.llm_calls_total = None
        except Exception as e:
            logger.error(f"Error setting up Prometheus metrics: {e}")
            # Don't mark as initialized if there was an error
            return
    
    def export_llm_call(self, llm_call):
        """Export LLM call to Prometheus."""
        print(f"🎯 [Prometheus] export_llm_call called with model: {llm_call.model}")
        
        if not self.llm_calls_total:
            print(f"❌ [Prometheus] Metrics not initialized, skipping export")
            logger.warning("Prometheus metrics not initialized, skipping export")
            return
            
        model = llm_call.model
        print(f"📊 [Prometheus] Exporting metrics for model: {model}")
        
        # Debug logging
        logger.info(f"Exporting LLM call to Prometheus: model={model}, tokens={llm_call.input_tokens}→{llm_call.output_tokens}")
        
        # Update counters and histograms
        self.llm_calls_total.labels(model=model).inc()
        self.llm_latency.labels(model=model).observe(llm_call.latency)
        self.llm_tokens.labels(model=model, type='input').inc(llm_call.input_tokens)
        self.llm_tokens.labels(model=model, type='output').inc(llm_call.output_tokens)
        self.llm_cost.labels(model=model).inc(llm_call.cost)
        
        # Export quality metrics if available
        try:
            quality_analysis = llm_call.metadata.get('quality_analysis', {})
            if quality_analysis:
                # Quality score
                quality_score = quality_analysis.get('quality_score', 0.0)
                self.quality_scores.labels(model=model).observe(quality_score)
                
                # Hallucination risk
                hallucination_risk = quality_analysis.get('hallucination_risk', 'unknown')
                self.hallucination_risk.labels(model=model, risk_level=hallucination_risk).inc()
                
                # Drift detection
                drift_detected = quality_analysis.get('drift_detected', False)
                drift_type = 'detected' if drift_detected else 'not_detected'
                self.drift_detections.labels(model=model, drift_type=drift_type).inc()
                
                # Quality issues
                quality_issues = quality_analysis.get('quality_issues', [])
                for issue in quality_issues:
                    # Normalize issue names for Prometheus labels
                    issue_type = issue.lower().replace(' ', '_')
                    self.quality_issues.labels(model=model, issue_type=issue_type).inc()
                
                print(f"📈 [Prometheus] Quality metrics exported: score={quality_score:.2f}, risk={hallucination_risk}")
                
        except Exception as quality_error:
            print(f"⚠️ [Prometheus] Quality metrics export failed: {quality_error}")
        
        print(f"✅ [Prometheus] Successfully exported metrics for model: {model}")
        logger.info(f"Successfully exported LLM call metrics for model: {model}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export custom metrics to Prometheus."""
        if not self.llm_calls_total:
            return
            
        # Handle agent and tool metrics
        for metric_name, values in metrics.items():
            if not values:
                continue
                
            latest_value = values[-1][1]
            
            if metric_name.startswith('agent.') and 'sessions_started' in metric_name:
                agent_name = metric_name.split('.')[1]
                self.agent_sessions.labels(agent=agent_name, status='started').inc(latest_value)
            elif metric_name.startswith('agent.') and 'sessions_completed' in metric_name:
                agent_name = metric_name.split('.')[1] 
                self.agent_sessions.labels(agent=agent_name, status='completed').inc(latest_value)
            elif metric_name.startswith('agent.') and 'sessions_failed' in metric_name:
                agent_name = metric_name.split('.')[1]
                self.agent_sessions.labels(agent=agent_name, status='failed').inc(latest_value)
            elif metric_name.startswith('tool.') and 'success_calls' in metric_name:
                tool_name = metric_name.split('.')[1]
                self.tool_calls.labels(tool=tool_name, status='success').inc(latest_value)
            elif metric_name.startswith('tool.') and 'error_calls' in metric_name:
                tool_name = metric_name.split('.')[1]
                self.tool_calls.labels(tool=tool_name, status='error').inc(latest_value)

class JaegerExporter(BaseExporter):
    """Export monitoring data to Jaeger for distributed tracing."""
    
    def __init__(self, config):
        super().__init__(config)
        self._setup_jaeger()
        
    def _setup_jaeger(self):
        """Setup Jaeger tracing."""
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter as JaegerThriftExporter
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            
            # Configure resource
            resource = Resource.create({"service.name": "ai-monitor"})
            
            # Setup tracer
            trace.set_tracer_provider(TracerProvider(resource=resource))
            tracer_provider = trace.get_tracer_provider()
            
            # Setup Jaeger exporter
            jaeger_exporter = JaegerThriftExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            self.tracer = trace.get_tracer(__name__)
            logger.info("Jaeger exporter configured successfully")
            
        except ImportError:
            logger.warning("OpenTelemetry not installed, Jaeger export disabled")
            self.tracer = None
    
    def export_llm_call(self, llm_call):
        """Export LLM call as Jaeger trace."""
        if not self.tracer:
            return
            
        with self.tracer.start_as_current_span(f"llm_call_{llm_call.model}") as span:
            span.set_attributes({
                "llm.call_id": llm_call.id,
                "llm.model": llm_call.model,
                "llm.input_tokens": llm_call.input_tokens,
                "llm.output_tokens": llm_call.output_tokens,
                "llm.total_tokens": llm_call.total_tokens,
                "llm.latency": llm_call.latency,
                "llm.cost": llm_call.cost,
                "llm.prompt_length": len(llm_call.prompt),
                "llm.response_length": len(llm_call.response)
            })
            
            # Add metadata as attributes
            for key, value in llm_call.metadata.items():
                span.set_attribute(f"llm.metadata.{key}", str(value))
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics as Jaeger spans."""
        if not self.tracer:
            return
            
        # Create spans for significant metrics
        with self.tracer.start_as_current_span("metrics_batch") as span:
            for metric_name, values in metrics.items():
                if values:
                    latest_value = values[-1][1]
                    span.set_attribute(f"metric.{metric_name}", latest_value)

class ConsoleExporter(BaseExporter):
    """Export monitoring data to console for debugging."""
    
    def export_llm_call(self, llm_call):
        """Export LLM call to console."""
        print(f"[LLM CALL] {llm_call.model} | "
              f"Tokens: {llm_call.input_tokens}→{llm_call.output_tokens} | "
              f"Latency: {llm_call.latency:.2f}s | "
              f"Cost: ${llm_call.cost:.4f}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics to console."""
        for metric_name, values in metrics.items():
            if values and len(values) > 0:
                latest = values[-1]
                print(f"[METRIC] {metric_name}: {latest[1]}")

class JSONFileExporter(BaseExporter):
    """Export monitoring data to JSON files."""
    
    def __init__(self, config, file_prefix="ai_monitor"):
        super().__init__(config)
        self.file_prefix = file_prefix
        
    def export_llm_call(self, llm_call):
        """Export LLM call to JSON file."""
        filename = f"{self.file_prefix}_llm_calls.jsonl"
        
        data = {
            'id': llm_call.id,
            'timestamp': llm_call.timestamp.isoformat(),
            'model': llm_call.model,
            'input_tokens': llm_call.input_tokens,
            'output_tokens': llm_call.output_tokens,
            'total_tokens': llm_call.total_tokens,
            'latency': llm_call.latency,
            'cost': llm_call.cost,
            'prompt': llm_call.prompt[:500],  # Truncate for file size
            'response': llm_call.response[:500],
            'metadata': llm_call.metadata
        }
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write LLM call to file: {e}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics to JSON file."""
        filename = f"{self.file_prefix}_metrics.jsonl"
        
        timestamp = time.time()
        data = {
            'timestamp': timestamp,
            'metrics': {name: values[-1] if values else None for name, values in metrics.items()}
        }
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write metrics to file: {e}")
