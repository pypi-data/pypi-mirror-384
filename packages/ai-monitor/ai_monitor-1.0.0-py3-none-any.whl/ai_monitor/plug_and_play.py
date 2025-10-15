"""
AI Monitor - Enhanced with Traceloop Integration
===============================================

Simple plug & play setup that combines custom AI monitoring with Traceloop OpenTelemetry.

Usage Examples:
    # Ultra-simple one-liner
    import ai_monitor
    ai_monitor.ultra_simple_setup()
    
    # With Traceloop
    import ai_monitor  
    ai_monitor.setup_with_traceloop()
    
    # For Flask apps
    import ai_monitor
    ai_monitor.flask_plug_and_play(app)
    
    # For any AI agent
    import ai_monitor
    ai_monitor.agent_plug_and_play("my_agent")
"""

def ultra_simple_setup():
    """
    🚀 Ultra-simple one-line setup - just works!
    
    This gives you:
    - HTTP interception of OpenAI/Azure calls
    - Prometheus metrics on port 8000
    - Quality analysis & drift detection
    """
    try:
        from . import one_line_setup
        return one_line_setup()
    except ImportError:
        # Fallback to basic setup
        from .core import AIMonitor
        from .http_interceptor import enable_http_monitoring
        
        print("🤖 Starting AI monitoring...")
        monitor = AIMonitor()
        enable_http_monitoring()
        print("✅ Monitoring active! Metrics at http://localhost:8000/metrics")
        return monitor

def setup_with_traceloop(app_name="ai_monitor_app", traceloop_endpoint=None):
    """
    🔗 Setup with Traceloop for OpenTelemetry traces
    
    Args:
        app_name: Name for your application in traces
        traceloop_endpoint: Optional OTLP endpoint URL
        
    Returns:
        (monitor, traceloop_success)
    """
    # Setup your custom monitoring
    monitor = ultra_simple_setup()
    
    # Add Traceloop
    traceloop_success = False
    try:
        from traceloop.sdk import Traceloop
        
        config = {"app_name": app_name}
        if traceloop_endpoint:
            config["exporter_endpoint"] = traceloop_endpoint
            
        Traceloop.init(**config)
        print("✅ Traceloop OpenTelemetry tracing enabled")
        print("🔗 You now have: Custom metrics + OpenTelemetry traces")
        traceloop_success = True
        
    except ImportError:
        print("⚠️ Traceloop not installed. Run: pip install traceloop-sdk")
    except Exception as e:
        print(f"⚠️ Traceloop setup failed: {e}")
    
    return monitor, traceloop_success

def flask_plug_and_play(app, with_traceloop=True):
    """
    🌐 Plug & play setup for Flask applications
    
    Usage:
        from flask import Flask
        import ai_monitor
        
        app = Flask(__name__)
        ai_monitor.flask_plug_and_play(app)
    """
    if with_traceloop:
        monitor, _ = setup_with_traceloop("flask_app")
    else:
        monitor = ultra_simple_setup()
    
    # Add Flask request tracking
    @app.before_request
    def track_request():
        import time
        from flask import g
        g.start_time = time.time()
    
    @app.after_request  
    def log_request(response):
        import time
        from flask import g, request
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            print(f"🌐 [{request.method}] {request.path} - {response.status_code} ({duration:.3f}s)")
        return response
    
    print("✅ Flask monitoring enabled")
    return monitor

def agent_plug_and_play(agent_name, with_traceloop=True):
    """
    🤖 Plug & play setup for any AI agent
    
    Usage:
        import ai_monitor
        ai_monitor.agent_plug_and_play("my_langchain_agent")
        
        # Now all OpenAI calls are automatically monitored
    """
    if with_traceloop:
        return setup_with_traceloop(agent_name)
    else:
        return ultra_simple_setup()

def langchain_plug_and_play():
    """🦜 Optimized setup for LangChain agents"""
    return agent_plug_and_play("langchain_agent", with_traceloop=True)

def multi_agent_setup(agent_names):
    """
    🏢 Setup monitoring for multiple agents
    
    Usage:
        ai_monitor.multi_agent_setup(["planner", "executor", "reviewer"])
    """
    monitors = {}
    for name in agent_names:
        monitors[name] = agent_plug_and_play(name, with_traceloop=True)
        print(f"✅ Agent '{name}' monitoring ready")
    
    return monitors

# Quick aliases for convenience
setup = ultra_simple_setup
quick_setup = ultra_simple_setup
plug_and_play = setup_with_traceloop
