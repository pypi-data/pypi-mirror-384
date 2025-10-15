"""
AI Agent Monitor - Plug & Play Monitoring Solution
=================================================

A comprehensive monitoring library for AI agents that requires no source code changes.
Simply import and use decorators or context managers.

Usage:
    from ai_monitor import AIMonitor, monitor_llm_call, monitor_agent
    
    # Decorator usage
    @monitor_llm_call()
    def my_llm_function():
        pass
    
    # Context manager usage
    with AIMonitor() as monitor:
        # Your AI agent code here
        pass
"""

from .core import AIMonitor, MonitoringConfig
from .decorators import monitor_llm_call, monitor_agent, monitor_tool_use
from .context_managers import LLMCallMonitor, AgentSessionMonitor, monitor_agent_session
from .collectors import MetricsCollector, TraceCollector
from .exporters import PrometheusExporter, JaegerExporter, LogExporter
from .detectors import HallucinationDetector, DriftDetector
from .utils import setup_monitoring, configure_exporters
from .auto_integrate import enable_auto_monitoring, one_line_setup, quick_monitor
from .http_interceptor import enable_http_monitoring, disable_http_monitoring
from .version import __version__, __version_info__

# Import plug & play functions
try:
    from .plug_and_play import (
        ultra_simple_setup, 
        setup_with_traceloop,
        flask_plug_and_play,
        agent_plug_and_play,
        langchain_plug_and_play,
        multi_agent_setup,
        setup,
        quick_setup,
        plug_and_play
    )
except ImportError:
    # Fallback if plug_and_play module has issues
    def ultra_simple_setup():
        return one_line_setup()
    
    setup = ultra_simple_setup
    quick_setup = ultra_simple_setup

__author__ = "AI Monitor Team"

# Default monitoring instance for quick setup
default_monitor = None

def init_monitoring(config=None):
    """Initialize default monitoring with optional configuration."""
    global default_monitor
    if config is None:
        config = MonitoringConfig()
    default_monitor = AIMonitor(config)
    return default_monitor

def get_monitor():
    """Get the default monitoring instance."""
    global default_monitor
    if default_monitor is None:
        default_monitor = init_monitoring()
    return default_monitor

# Auto-setup for immediate use
init_monitoring()

__all__ = [
    'AIMonitor',
    'MonitoringConfig',
    'monitor_llm_call',
    'monitor_agent', 
    'monitor_tool_use',
    'LLMCallMonitor',
    'AgentSessionMonitor',
    'monitor_agent_session',
    'MetricsCollector',
    'TraceCollector',
    'PrometheusExporter',
    'JaegerExporter',
    'LogExporter',
    'HallucinationDetector',
    'DriftDetector',
    'setup_monitoring',
    'configure_exporters',
    'init_monitoring',
    'get_monitor',
    'enable_auto_monitoring',
    'one_line_setup',
    'quick_monitor'
]
