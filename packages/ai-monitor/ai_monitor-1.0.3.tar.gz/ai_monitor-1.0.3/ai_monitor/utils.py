"""
Utility functions and collectors for AI monitoring.
"""
import time
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect and aggregate metrics data."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = threading.Lock()
    
    def record(self, name: str, value: float, timestamp: Optional[float] = None):
        """Record a metric value."""
        if timestamp is None:
            timestamp = time.time()
            
        with self._lock:
            self.metrics[name].append((timestamp, value))
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, List[tuple]]:
        """Get metrics data."""
        with self._lock:
            if name:
                return {name: list(self.metrics.get(name, []))}
            return {k: list(v) for k, v in self.metrics.items()}
    
    def get_latest(self, name: str) -> Optional[tuple]:
        """Get latest value for a metric."""
        with self._lock:
            values = self.metrics.get(name)
            return values[-1] if values else None
    
    def get_average(self, name: str, window_size: int = 100) -> Optional[float]:
        """Get average value over a window."""
        with self._lock:
            values = self.metrics.get(name)
            if not values:
                return None
                
            recent_values = list(values)[-window_size:]
            return sum(v[1] for v in recent_values) / len(recent_values)
    
    def clear(self):
        """Clear all metrics."""
        with self._lock:
            self.metrics.clear()

class TraceCollector:
    """Collect trace/span data for distributed tracing."""
    
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self.traces = deque(maxlen=max_traces)
        self._lock = threading.Lock()
    
    def start_trace(self, trace_id: str, operation_name: str, metadata: Optional[Dict] = None):
        """Start a new trace."""
        trace_data = {
            'trace_id': trace_id,
            'operation_name': operation_name,
            'start_time': time.time(),
            'end_time': None,
            'duration': None,
            'metadata': metadata or {},
            'spans': []
        }
        
        with self._lock:
            self.traces.append(trace_data)
            
        return trace_data
    
    def end_trace(self, trace_id: str):
        """End a trace."""
        with self._lock:
            for trace in reversed(self.traces):
                if trace['trace_id'] == trace_id:
                    trace['end_time'] = time.time()
                    trace['duration'] = trace['end_time'] - trace['start_time']
                    break
    
    def add_span(self, trace_id: str, span_name: str, start_time: float, end_time: float, metadata: Optional[Dict] = None):
        """Add a span to a trace."""
        span_data = {
            'span_name': span_name,
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'metadata': metadata or {}
        }
        
        with self._lock:
            for trace in reversed(self.traces):
                if trace['trace_id'] == trace_id:
                    trace['spans'].append(span_data)
                    break
    
    def get_traces(self, limit: Optional[int] = None) -> List[Dict]:
        """Get trace data."""
        with self._lock:
            traces = list(self.traces)
            if limit:
                traces = traces[-limit:]
            return traces

def setup_monitoring(config_dict: Optional[Dict[str, Any]] = None):
    """
    Setup AI monitoring with configuration.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        AIMonitor instance
    """
    from .core import AIMonitor, MonitoringConfig
    
    if config_dict:
        config = MonitoringConfig(**config_dict)
    else:
        config = MonitoringConfig()
    
    monitor = AIMonitor(config)
    monitor.start_monitoring()
    
    logger.info("AI monitoring setup completed")
    return monitor

def configure_exporters(monitor, exporters_config: List[Dict[str, Any]]):
    """
    Configure additional exporters for a monitor.
    
    Args:
        monitor: AIMonitor instance
        exporters_config: List of exporter configurations
    """
    from .exporters import ConsoleExporter, JSONFileExporter
    
    for exporter_config in exporters_config:
        exporter_type = exporter_config.get('type')
        
        if exporter_type == 'console':
            exporter = ConsoleExporter(monitor.config)
            monitor._exporters.append(exporter)
            
        elif exporter_type == 'json_file':
            file_prefix = exporter_config.get('file_prefix', 'ai_monitor')
            exporter = JSONFileExporter(monitor.config, file_prefix)
            monitor._exporters.append(exporter)
            
        else:
            logger.warning(f"Unknown exporter type: {exporter_type}")

def calculate_token_cost(tokens: int, model: str, token_type: str = 'output') -> float:
    """
    Calculate token cost based on model and token count.
    
    Args:
        tokens: Number of tokens
        model: Model name
        token_type: 'input' or 'output'
        
    Returns:
        Cost in USD
    """
    # Simplified pricing (update with actual pricing)
    pricing = {
        'gpt-4': {'input': 0.03 / 1000, 'output': 0.06 / 1000},
        'gpt-3.5-turbo': {'input': 0.0015 / 1000, 'output': 0.002 / 1000},
        'claude-3': {'input': 0.025 / 1000, 'output': 0.075 / 1000},
        'gemini-pro': {'input': 0.00025 / 1000, 'output': 0.0005 / 1000}
    }
    
    # Normalize model name
    model_key = model.lower()
    for key in pricing.keys():
        if key in model_key:
            model_key = key
            break
    else:
        model_key = 'gpt-3.5-turbo'  # Default
    
    rate = pricing[model_key].get(token_type, pricing[model_key]['output'])
    return tokens * rate

def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    # Rough estimation: ~4 characters per token for English
    return max(1, len(text) // 4)

def format_metrics_summary(metrics: Dict[str, List[tuple]], 
                          window_minutes: int = 60) -> str:
    """
    Format metrics into a readable summary.
    
    Args:
        metrics: Metrics data
        window_minutes: Time window for aggregation
        
    Returns:
        Formatted summary string
    """
    current_time = time.time()
    window_start = current_time - (window_minutes * 60)
    
    summary_lines = [f"AI Monitor Summary (Last {window_minutes} minutes)"]
    summary_lines.append("=" * 50)
    
    # Filter metrics to time window
    windowed_metrics = {}
    for name, values in metrics.items():
        windowed_values = [(t, v) for t, v in values if t >= window_start]
        if windowed_values:
            windowed_metrics[name] = windowed_values
    
    # LLM metrics
    llm_metrics = {k: v for k, v in windowed_metrics.items() if k.startswith('llm.')}
    if llm_metrics:
        summary_lines.append("\nLLM Metrics:")
        for name, values in llm_metrics.items():
            if values:
                latest_value = values[-1][1]
                avg_value = sum(v[1] for v in values) / len(values)
                summary_lines.append(f"  {name}: {latest_value:.3f} (avg: {avg_value:.3f})")
    
    # Agent metrics
    agent_metrics = {k: v for k, v in windowed_metrics.items() if k.startswith('agent.')}
    if agent_metrics:
        summary_lines.append("\nAgent Metrics:")
        for name, values in agent_metrics.items():
            if values:
                total_value = sum(v[1] for v in values)
                summary_lines.append(f"  {name}: {total_value}")
    
    # Tool metrics
    tool_metrics = {k: v for k, v in windowed_metrics.items() if k.startswith('tool.')}
    if tool_metrics:
        summary_lines.append("\nTool Metrics:")
        for name, values in tool_metrics.items():
            if values:
                total_value = sum(v[1] for v in values)
                summary_lines.append(f"  {name}: {total_value}")
    
    # System metrics
    system_metrics = {k: v for k, v in windowed_metrics.items() if k.startswith('system.')}
    if system_metrics:
        summary_lines.append("\nSystem Metrics:")
        for name, values in system_metrics.items():
            if values:
                latest_value = values[-1][1]
                summary_lines.append(f"  {name}: {latest_value:.2f}")
    
    return "\n".join(summary_lines)

class PerformanceProfiler:
    """Profile performance of AI operations."""
    
    def __init__(self):
        self.profiles = defaultdict(list)
        self._lock = threading.Lock()
    
    def profile_operation(self, operation_name: str):
        """Context manager for profiling operations."""
        return _ProfileContext(self, operation_name)
    
    def record_profile(self, operation_name: str, duration: float, metadata: Optional[Dict] = None):
        """Record a performance profile."""
        profile_data = {
            'duration': duration,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        with self._lock:
            self.profiles[operation_name].append(profile_data)
    
    def get_performance_summary(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary."""
        with self._lock:
            if operation_name:
                profiles = self.profiles.get(operation_name, [])
                return self._summarize_profiles(operation_name, profiles)
            
            summary = {}
            for name, profiles in self.profiles.items():
                summary[name] = self._summarize_profiles(name, profiles)
            
            return summary
    
    def _summarize_profiles(self, name: str, profiles: List[Dict]) -> Dict[str, Any]:
        """Summarize profiles for an operation."""
        if not profiles:
            return {'count': 0}
        
        durations = [p['duration'] for p in profiles]
        
        return {
            'count': len(profiles),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_duration': sum(durations),
            'latest_timestamp': max(p['timestamp'] for p in profiles)
        }

class _ProfileContext:
    """Context manager for profiling."""
    
    def __init__(self, profiler: PerformanceProfiler, operation_name: str):
        self.profiler = profiler
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        metadata = {'success': exc_type is None}
        if exc_type:
            metadata['error_type'] = exc_type.__name__
        
        self.profiler.record_profile(self.operation_name, duration, metadata)
