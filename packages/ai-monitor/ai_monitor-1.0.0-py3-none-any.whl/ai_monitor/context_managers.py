"""
Context managers for AI monitoring.
"""
import time
import uuid
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

class LLMCallMonitor:
    """Context manager for monitoring individual LLM calls."""
    
    def __init__(self, 
                 model: str,
                 prompt: str = "",
                 metadata: Optional[Dict[str, Any]] = None):
        self.model = model
        self.prompt = prompt
        self.metadata = metadata or {}
        self.start_time = None
        self.call_id = None
        
    def __enter__(self):
        from . import get_monitor
        self.monitor = get_monitor()
        self.start_time = time.time()
        self.call_id = str(uuid.uuid4())
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Normal completion - record the call if we have response data
            if hasattr(self, '_response_recorded'):
                pass  # Already recorded via record_response()
            else:
                # Record minimal call info
                latency = time.time() - self.start_time
                self.monitor.record_llm_call(
                    model=self.model,
                    prompt=self.prompt,
                    response="",
                    input_tokens=0,
                    output_tokens=0,
                    latency=latency,
                    cost=0.0,
                    metadata=self.metadata
                )
        else:
            # Error occurred
            latency = time.time() - self.start_time
            self.monitor.record_metric(f"llm.{self.model}.errors", 1)
            self.monitor.record_metric(f"llm.{self.model}.error_latency", latency)
    
    def record_response(self, 
                       response: str,
                       input_tokens: int = 0,
                       output_tokens: int = 0,
                       cost: float = 0.0):
        """Record the LLM response within the context."""
        latency = time.time() - self.start_time
        
        self.monitor.record_llm_call(
            model=self.model,
            prompt=self.prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=latency,
            cost=cost,
            metadata=self.metadata
        )
        self._response_recorded = True

class AgentSessionMonitor:
    """Context manager for monitoring AI agent sessions."""
    
    def __init__(self, 
                 agent_name: str,
                 session_metadata: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        self.session_metadata = session_metadata or {}
        self.session_id = str(uuid.uuid4())
        self.start_time = None
        self.llm_calls = []
        self.tool_uses = []
        
    def __enter__(self):
        from . import get_monitor
        self.monitor = get_monitor()
        self.start_time = time.time()
        
        # Record session start
        self.monitor.record_metric(f"agent.{self.agent_name}.sessions_started", 1)
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.monitor.record_metric(f"agent.{self.agent_name}.sessions_completed", 1)
            self.monitor.record_metric(f"agent.{self.agent_name}.session_duration", duration)
        else:
            self.monitor.record_metric(f"agent.{self.agent_name}.sessions_failed", 1)
            self.monitor.record_metric(f"agent.{self.agent_name}.error_duration", duration)
        
        # Record session summary
        self._record_session_summary(duration, exc_type is None)
    
    def record_llm_call(self, 
                       model: str,
                       prompt: str,
                       response: str,
                       input_tokens: int = 0,
                       output_tokens: int = 0,
                       cost: float = 0.0):
        """Record an LLM call within this agent session."""
        call_metadata = self.session_metadata.copy()
        call_metadata.update({
            'agent_name': self.agent_name,
            'session_id': self.session_id
        })
        
        call_id = self.monitor.record_llm_call(
            model=model,
            prompt=prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency=0,  # Will be calculated by the monitor
            cost=cost,
            metadata=call_metadata
        )
        
        self.llm_calls.append(call_id)
        return call_id
    
    def record_tool_use(self, 
                       tool_name: str,
                       input_data: Any = None,
                       output_data: Any = None,
                       success: bool = True,
                       duration: float = 0.0):
        """Record a tool use within this agent session."""
        tool_use_id = str(uuid.uuid4())
        
        # Record metrics
        self.monitor.record_metric(f"tool.{tool_name}.calls", 1)
        if success:
            self.monitor.record_metric(f"tool.{tool_name}.success_calls", 1)
            self.monitor.record_metric(f"tool.{tool_name}.success_duration", duration)
        else:
            self.monitor.record_metric(f"tool.{tool_name}.error_calls", 1)
            self.monitor.record_metric(f"tool.{tool_name}.error_duration", duration)
        
        self.tool_uses.append({
            'id': tool_use_id,
            'tool_name': tool_name,
            'input_data': str(input_data) if input_data else "",
            'output_data': str(output_data) if output_data else "",
            'success': success,
            'duration': duration,
            'timestamp': time.time()
        })
        
        return tool_use_id
    
    def _record_session_summary(self, duration: float, success: bool):
        """Record session summary metrics."""
        summary_metadata = self.session_metadata.copy()
        summary_metadata.update({
            'session_id': self.session_id,
            'agent_name': self.agent_name,
            'duration': duration,
            'success': success,
            'llm_calls_count': len(self.llm_calls),
            'tool_uses_count': len(self.tool_uses),
            'llm_calls': self.llm_calls,
            'tool_uses': self.tool_uses
        })
        
        # Record as a special session metric
        self.monitor.record_metric(
            f"agent.{self.agent_name}.session_summary", 
            1.0
        )
        
        # Store metadata separately if needed
        # Could extend record_metric to support metadata in the future

@contextmanager
def monitor_llm_call(model: str, 
                     prompt: str = "",
                     metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for monitoring LLM calls.
    
    Usage:
        with monitor_llm_call("gpt-4", "Hello world") as monitor:
            response = call_llm("Hello world")
            monitor.record_response(response, input_tokens=2, output_tokens=5)
    """
    monitor = LLMCallMonitor(model, prompt, metadata)
    with monitor:
        yield monitor

@contextmanager  
def monitor_agent_session(agent_name: str,
                         session_metadata: Optional[Dict[str, Any]] = None):
    """
    Context manager for monitoring agent sessions.
    
    Usage:
        with monitor_agent_session("my_agent") as session:
            # Your agent code
            session.record_llm_call("gpt-4", "prompt", "response")
            session.record_tool_use("web_search", "query", "results")
    """
    monitor = AgentSessionMonitor(agent_name, session_metadata)
    with monitor:
        yield monitor
