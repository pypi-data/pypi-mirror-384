"""
Decorators for AI monitoring - plug and play solution.
"""
import time
import functools
from typing import Callable, Any, Optional, Dict
import inspect

def monitor_llm_call(model: Optional[str] = None, 
                     track_tokens: bool = True,
                     track_cost: bool = True,
                     metadata: Optional[Dict[str, Any]] = None):
    """
    Decorator to monitor LLM calls automatically.
    
    Usage:
        @monitor_llm_call(model="gpt-4")
        def call_openai(prompt):
            # Your LLM call code
            return response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from . import get_monitor
            
            monitor = get_monitor()
            start_time = time.time()
            
            # Extract prompt from arguments
            prompt = _extract_prompt(args, kwargs, func)
            detected_model = model or _detect_model(args, kwargs) or "unknown"
            
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                
                # Extract response data
                response_text, input_tokens, output_tokens, cost = _extract_response_data(
                    result, track_tokens, track_cost
                )
                
                # Record the call
                call_id = monitor.record_llm_call(
                    model=detected_model,
                    prompt=prompt,
                    response=response_text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency=latency,
                    cost=cost,
                    metadata=metadata
                )
                
                # Add monitoring metadata to result if possible
                if hasattr(result, '__dict__'):
                    result.__dict__['_monitor_call_id'] = call_id
                
                return result
                
            except Exception as e:
                latency = time.time() - start_time
                monitor.record_metric(f"llm.{detected_model}.errors", 1)
                monitor.record_metric(f"llm.{detected_model}.error_latency", latency)
                raise
                
        return wrapper
    return decorator

def monitor_agent(name: Optional[str] = None, 
                  track_tools: bool = True,
                  track_decisions: bool = True):
    """
    Decorator to monitor AI agent sessions.
    
    Usage:
        @monitor_agent(name="my_agent")
        def run_agent_task():
            # Your agent code
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from . import get_monitor
            
            monitor = get_monitor()
            agent_name = name or func.__name__
            session_id = f"{agent_name}_{int(time.time())}"
            
            start_time = time.time()
            monitor.record_metric(f"agent.{agent_name}.sessions_started", 1)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                monitor.record_metric(f"agent.{agent_name}.session_duration", duration)
                monitor.record_metric(f"agent.{agent_name}.sessions_completed", 1)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                monitor.record_metric(f"agent.{agent_name}.sessions_failed", 1)
                monitor.record_metric(f"agent.{agent_name}.error_duration", duration)
                raise
                
        return wrapper
    return decorator

def monitor_tool_use(tool_name: Optional[str] = None):
    """
    Decorator to monitor AI tool usage.
    
    Usage:
        @monitor_tool_use(tool_name="web_search")
        def search_web(query):
            # Your tool code
            return results
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from . import get_monitor
            
            monitor = get_monitor()
            name = tool_name or func.__name__
            
            start_time = time.time()
            monitor.record_metric(f"tool.{name}.calls", 1)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                monitor.record_metric(f"tool.{name}.success_duration", duration)
                monitor.record_metric(f"tool.{name}.success_calls", 1)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                monitor.record_metric(f"tool.{name}.error_duration", duration)
                monitor.record_metric(f"tool.{name}.error_calls", 1)
                raise
                
        return wrapper
    return decorator

def _extract_prompt(args, kwargs, func):
    """Extract prompt from function arguments."""
    # Try common prompt parameter names
    prompt_keys = ['prompt', 'message', 'messages', 'input', 'text', 'query']
    
    # Check kwargs first
    for key in prompt_keys:
        if key in kwargs:
            value = kwargs[key]
            if isinstance(value, str):
                return value
            elif isinstance(value, list) and len(value) > 0:
                # Handle messages format
                return str(value)
    
    # Check positional arguments
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    
    for i, arg in enumerate(args):
        if i < len(param_names):
            param_name = param_names[i]
            if param_name in prompt_keys:
                return str(arg)
    
    # Fallback to first string argument
    for arg in args:
        if isinstance(arg, str) and len(arg) > 0:
            return arg
    
    return "unknown"

def _detect_model(args, kwargs):
    """Detect model from function arguments."""
    model_keys = ['model', 'engine', 'model_name', 'model_id']
    
    for key in model_keys:
        if key in kwargs:
            return str(kwargs[key])
    
    # Check if it's an OpenAI-style call
    if 'messages' in kwargs or 'prompt' in kwargs:
        return "openai-api"
    
    return None

def _extract_response_data(result, track_tokens=True, track_cost=True):
    """Extract response data from function result."""
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    cost = 0.0
    
    if isinstance(result, str):
        response_text = result
        if track_tokens:
            # Rough token estimation
            output_tokens = len(result.split()) * 1.3  # Rough approximation
    
    elif isinstance(result, dict):
        # Handle OpenAI-style response
        if 'choices' in result:
            choice = result['choices'][0]
            if 'message' in choice:
                response_text = choice['message'].get('content', '')
            elif 'text' in choice:
                response_text = choice['text']
        
        # Extract usage information
        if 'usage' in result and track_tokens:
            usage = result['usage']
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            
        # Extract cost if available
        if track_cost and 'cost' in result:
            cost = result['cost']
    
    elif hasattr(result, 'content'):
        # Handle response objects with content attribute
        response_text = str(result.content)
        
        if hasattr(result, 'usage') and track_tokens:
            usage = result.usage
            input_tokens = getattr(usage, 'input_tokens', 0) or getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0) or getattr(usage, 'completion_tokens', 0)
    
    else:
        response_text = str(result)
    
    # Ensure we have token counts
    if track_tokens and output_tokens == 0 and response_text:
        output_tokens = max(1, len(response_text.split()) * 1.3)
    
    return response_text, int(input_tokens), int(output_tokens), float(cost)
