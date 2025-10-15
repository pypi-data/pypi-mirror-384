"""
Core AI Monitoring Classes
"""
import time
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for AI monitoring."""
    # Exporters
    enable_prometheus: bool = True
    enable_jaeger: bool = True
    enable_logging: bool = True
    
    # Prometheus config
    prometheus_port: int = 8000
    prometheus_host: str = "localhost"
    
    # Jaeger config
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    
    # Logging config
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Monitoring features
    track_tokens: bool = True
    track_latency: bool = True
    detect_hallucination: bool = True
    detect_drift: bool = True
    track_costs: bool = True
    
    # Sampling
    trace_sampling_rate: float = 1.0
    metrics_collection_interval: float = 1.0
    
    # Storage
    max_trace_history: int = 10000
    max_metrics_history: int = 100000

@dataclass
class LLMCall:
    """Represents an LLM call for monitoring."""
    id: str
    timestamp: datetime
    model: str
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency: float
    cost: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
class AIMonitor:
    """Main AI monitoring class that can be used as context manager or singleton."""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()
        
        # Storage
        self.llm_calls: deque = deque(maxlen=self.config.max_trace_history)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config.max_metrics_history))
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Exporters
        self._exporters = []
        self._setup_exporters()
        
        # Background monitoring
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        
    def _setup_exporters(self):
        """Setup configured exporters."""
        if self.config.enable_prometheus:
            try:
                from .exporters import PrometheusExporter
                self._exporters.append(PrometheusExporter(self.config))
            except ImportError:
                logger.warning("Prometheus exporter not available")
                
        if self.config.enable_jaeger:
            try:
                from .exporters import JaegerExporter
                self._exporters.append(JaegerExporter(self.config))
            except ImportError:
                logger.warning("Jaeger exporter not available")
                
        if self.config.enable_logging:
            try:
                from .exporters import LogExporter
                self._exporters.append(LogExporter(self.config))
            except ImportError:
                logger.warning("Log exporter not available")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()
        
    def start_monitoring(self):
        """Start background monitoring."""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self._monitoring_thread.daemon = True
            self._monitoring_thread.start()
            
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._stop_monitoring.set()
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                self._collect_system_metrics()
                self._export_metrics()
                time.sleep(self.config.metrics_collection_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
    
    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        timestamp = time.time()
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            self.record_metric("system.memory_mb", memory_mb, timestamp)
            self.record_metric("system.cpu_percent", cpu_percent, timestamp)
        except ImportError:
            pass
    
    def record_llm_call(self, 
                       model: str,
                       prompt: str, 
                       response: str,
                       input_tokens: int,
                       output_tokens: int,
                       latency: float,
                       cost: float = 0.0,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record an LLM call for monitoring."""
        
        call_id = str(uuid.uuid4())
        llm_call = LLMCall(
            id=call_id,
            timestamp=datetime.now(),
            model=model,
            prompt=prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency=latency,
            cost=cost,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.llm_calls.append(llm_call)
            
        # Record metrics
        timestamp = time.time()
        self.record_metric(f"llm.{model}.latency", latency, timestamp)
        self.record_metric(f"llm.{model}.input_tokens", input_tokens, timestamp)
        self.record_metric(f"llm.{model}.output_tokens", output_tokens, timestamp)
        self.record_metric(f"llm.{model}.total_tokens", input_tokens + output_tokens, timestamp)
        self.record_metric(f"llm.{model}.cost", cost, timestamp)
        
        # Export to configured exporters
        self._export_llm_call(llm_call)
        
        return call_id
    
    def record_metric(self, name: str, value: float, timestamp: Optional[float] = None):
        """Record a metric value."""
        if timestamp is None:
            timestamp = time.time()
            
        with self._lock:
            self.metrics[name].append((timestamp, value))
    
    def _export_llm_call(self, llm_call: LLMCall):
        """Export LLM call to all configured exporters."""
        for exporter in self._exporters:
            try:
                exporter.export_llm_call(llm_call)
            except Exception as e:
                logger.error(f"Exporter {type(exporter).__name__} error: {e}")
    
    def _export_metrics(self):
        """Export metrics to all configured exporters."""
        for exporter in self._exporters:
            try:
                exporter.export_metrics(dict(self.metrics))
            except Exception as e:
                logger.error(f"Exporter {type(exporter).__name__} error: {e}")
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, List[tuple]]:
        """Get collected metrics."""
        with self._lock:
            if name:
                return {name: list(self.metrics.get(name, []))}
            return {k: list(v) for k, v in self.metrics.items()}
    
    def get_llm_calls(self, limit: Optional[int] = None) -> List[LLMCall]:
        """Get recorded LLM calls."""
        with self._lock:
            calls = list(self.llm_calls)
            if limit:
                calls = calls[-limit:]
            return calls
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        with self._lock:
            total_calls = len(self.llm_calls)
            if total_calls == 0:
                return {"total_calls": 0}
            
            total_tokens = sum(call.total_tokens for call in self.llm_calls)
            total_cost = sum(call.cost for call in self.llm_calls)
            avg_latency = sum(call.latency for call in self.llm_calls) / total_calls
            
            return {
                "session_id": self.session_id,
                "uptime_seconds": time.time() - self.start_time,
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "average_latency": avg_latency,
                "tokens_per_second": total_tokens / (time.time() - self.start_time)
            }

# Global monitor instance for HTTP interception
_default_monitor = None

def get_default_monitor():
    """Get the default monitor instance."""
    return _default_monitor

def set_default_monitor(monitor):
    """Set the default monitor instance."""
    global _default_monitor
    _default_monitor = monitor

