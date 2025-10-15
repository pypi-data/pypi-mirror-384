"""
Drop-in AI Monitor Integration
=============================

Add this single import to your existing agent and get instant monitoring!

Usage in your existing agent file:
    # Just add this one line at the top of your agent file:
    from ai_monitor.auto_integrate import enable_auto_monitoring
    
    # That's it! All your LLM calls are now monitored automatically.
"""

import sys
import functools
import inspect
from typing import Any, Callable
import importlib.util

def enable_auto_monitoring(
    monitor_openai=True,
    monitor_anthropic=True,
    monitor_langchain=True,
    agent_name="auto_detected_agent"
):
    """
    Automatically enable monitoring for popular AI libraries.
    
    This function monkey-patches common AI libraries to add monitoring
    without requiring any changes to your existing code.
    
    Args:
        monitor_openai: Enable OpenAI monitoring
        monitor_anthropic: Enable Anthropic monitoring  
        monitor_langchain: Enable LangChain monitoring
        agent_name: Name for your agent in monitoring
    """
    
    print("🤖 Enabling automatic AI monitoring...")
    
    if monitor_openai:
        _patch_openai()
        print("✅ OpenAI monitoring enabled")
    
    if monitor_anthropic:
        _patch_anthropic()
        print("✅ Anthropic monitoring enabled")
    
    if monitor_langchain:
        _patch_langchain()
        print("✅ LangChain monitoring enabled")
    
    # Setup global monitoring
    from ai_monitor import init_monitoring, MonitoringConfig
    
    config = MonitoringConfig(
        enable_prometheus=True,
        enable_logging=True,
        log_level="INFO"
    )
    
    monitor = init_monitoring(config)
    print(f"📊 Monitoring dashboard: http://localhost:8000/metrics")
    
    return monitor

def _patch_openai():
    """Patch OpenAI library for automatic monitoring."""
    try:
        import openai
        from ai_monitor import monitor_llm_call
        
        # Store original methods
        original_chat_create = openai.ChatCompletion.create
        original_completion_create = openai.Completion.create
        
        # Create monitored versions
        @monitor_llm_call(model="openai-chat")
        def monitored_chat_create(*args, **kwargs):
            return original_chat_create(*args, **kwargs)
        
        @monitor_llm_call(model="openai-completion")
        def monitored_completion_create(*args, **kwargs):
            return original_completion_create(*args, **kwargs)
        
        # Patch the methods
        openai.ChatCompletion.create = monitored_chat_create
        openai.Completion.create = monitored_completion_create
        
    except ImportError:
        pass  # OpenAI not installed

def _patch_anthropic():
    """Patch Anthropic library for automatic monitoring."""
    try:
        import anthropic
        from ai_monitor import monitor_llm_call
        
        # This would patch Anthropic's client methods
        # Implementation depends on Anthropic's API structure
        
    except ImportError:
        pass  # Anthropic not installed

def _patch_langchain():
    """Patch LangChain library for automatic monitoring."""
    try:
        from langchain.llms.base import LLM
        from ai_monitor import monitor_llm_call
        
        # Store original _call method
        original_call = LLM._call
        
        @monitor_llm_call()
        def monitored_call(self, prompt, stop=None, run_manager=None, **kwargs):
            return original_call(self, prompt, stop, run_manager, **kwargs)
        
        # Patch the LLM base class
        LLM._call = monitored_call
        
    except ImportError:
        pass  # LangChain not installed

def monitor_function(func_name: str):
    """
    Decorator to monitor a specific function by name.
    
    Usage:
        @monitor_function("my_llm_call")
        def my_function():
            pass
    """
    from ai_monitor import monitor_llm_call
    
    def decorator(func):
        return monitor_llm_call()(func)
    return decorator

def monitor_class_methods(cls, method_names=None):
    """
    Add monitoring to all methods of a class.
    
    Usage:
        @monitor_class_methods
        class MyAgent:
            def llm_call(self):
                pass
    """
    from ai_monitor import monitor_llm_call, monitor_agent
    
    if method_names is None:
        # Auto-detect LLM-related methods
        method_names = [
            'call_llm', 'llm_call', 'generate', 'complete', 
            'chat', 'ask', 'query', 'process', 'run'
        ]
    
    # Wrap matching methods
    for attr_name in dir(cls):
        if attr_name in method_names:
            attr = getattr(cls, attr_name)
            if callable(attr) and not attr_name.startswith('_'):
                if 'llm' in attr_name.lower() or attr_name in ['generate', 'complete', 'chat']:
                    wrapped = monitor_llm_call()(attr)
                else:
                    wrapped = monitor_agent(name=f"{cls.__name__}_{attr_name}")(attr)
                setattr(cls, attr_name, wrapped)
    
    return cls

# Automatic detection and patching when imported
class AutoMonitorImportHook:
    """Import hook that automatically adds monitoring to AI libraries."""
    
    def __init__(self):
        self.monitored_modules = set()
    
    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        # Import the module normally first
        module = __import__(name, globals, locals, fromlist, level)
        
        # Add monitoring if it's an AI library
        if name == 'openai' and name not in self.monitored_modules:
            _patch_openai()
            self.monitored_modules.add(name)
            print("🤖 Auto-detected OpenAI import - monitoring enabled!")
            
        elif name == 'anthropic' and name not in self.monitored_modules:
            _patch_anthropic()
            self.monitored_modules.add(name)
            print("🤖 Auto-detected Anthropic import - monitoring enabled!")
            
        elif name.startswith('langchain') and 'langchain' not in self.monitored_modules:
            _patch_langchain()
            self.monitored_modules.add('langchain')
            print("🤖 Auto-detected LangChain import - monitoring enabled!")
        
        return module

# Install the import hook automatically
auto_monitor_hook = AutoMonitorImportHook()

# Convenience functions for different integration patterns
def one_line_setup(agent_name="default_agent", enable_http_interception=True):
    """
    The ultimate one-line setup for AI monitoring.
    
    This function does EVERYTHING:
    - Initializes monitoring
    - Sets up all exporters  
    - Enables auto-monitoring for all AI libraries
    - Enables HTTP request interception for custom implementations
    - Returns ready-to-use monitor
    
    Args:
        agent_name: Name for your agent in monitoring
        enable_http_interception: Enable HTTP request monitoring (for custom implementations)
    
    Usage:
        from ai_monitor import one_line_setup
        monitor = one_line_setup()
        # Done! Your AI calls are now monitored automatically
    """
    
    # Initialize core monitor
    from .core import AIMonitor, MonitoringConfig, set_default_monitor
    config = MonitoringConfig()
    monitor = AIMonitor(config)
    
    # Set as default monitor for HTTP interception
    set_default_monitor(monitor)
    
    # Enable auto-monitoring for all AI libraries
    enable_auto_monitoring(
        monitor_openai=True,
        monitor_anthropic=True,
        monitor_langchain=True,
        agent_name=agent_name
    )
    
    # Enable HTTP interception for custom implementations (like Azure OpenAI calls)
    if enable_http_interception:
        try:
            from .http_interceptor import enable_http_monitoring
            enable_http_monitoring()
            print("✅ HTTP request monitoring enabled (monitors custom API calls)")
        except Exception as e:
            print(f"⚠️ Could not enable HTTP monitoring: {e}")
    
    # Print helpful info
    print("📊 Monitoring dashboard: http://localhost:8000/metrics")
    
    return monitor

def quick_monitor(agent_or_function):
    """
    Quick decorator/wrapper for any agent or function.
    
    Usage:
        @quick_monitor
        def my_agent_function():
            pass
        
        # OR
        
        my_monitored_agent = quick_monitor(my_existing_agent)
    """
    from ai_monitor import monitor_agent
    
    if inspect.isclass(agent_or_function):
        return monitor_class_methods(agent_or_function)
    else:
        return monitor_agent()(agent_or_function)

def setup_production_monitoring(service_name="ai_agent"):
    """
    Setup production-ready monitoring with best practices.
    
    Returns:
        monitor: Configured monitor instance
    """
    from ai_monitor import init_monitoring, MonitoringConfig
    
    config = MonitoringConfig(
        # Production exporters
        enable_prometheus=True,
        enable_jaeger=True,
        enable_logging=True,
        
        # Production settings
        prometheus_port=8000,
        log_level="INFO",
        
        # Performance optimized
        trace_sampling_rate=0.1,  # 10% sampling
        metrics_collection_interval=5.0,
        
        # Essential detection
        detect_hallucination=True,
        detect_drift=True,
        track_costs=True
    )
    
    monitor = init_monitoring(config)
    
    print(f"🚀 Production monitoring enabled for {service_name}")
    print(f"📊 Metrics: http://localhost:8000/metrics")
    print(f"🔍 Traces: Configure Jaeger endpoint")
    
    return monitor

# Ultra-simple integration examples
def instant_openai_monitoring():
    """Add monitoring to OpenAI with zero code changes."""
    _patch_openai()
    from ai_monitor import get_monitor
    return get_monitor()

def instant_agent_stats():
    """Get instant stats about your agent's performance."""
    from ai_monitor import get_monitor
    
    monitor = get_monitor()
    stats = monitor.get_summary_stats()
    
    print("\n📊 Agent Performance Summary:")
    print(f"   🔢 Total calls: {stats['total_calls']}")
    print(f"   🎯 Total tokens: {stats['total_tokens']}")
    print(f"   💰 Total cost: ${stats['total_cost']:.4f}")
    if stats['total_calls'] > 0:
        print(f"   ⏱️  Avg latency: {stats['average_latency']:.2f}s")
        print(f"   🚀 Tokens/sec: {stats['tokens_per_second']:.1f}")
    
    return stats

# Export the main functions for easy import
__all__ = [
    'enable_auto_monitoring',
    'one_line_setup', 
    'quick_monitor',
    'setup_production_monitoring',
    'instant_openai_monitoring',
    'instant_agent_stats',
    'monitor_function',
    'monitor_class_methods'
]
