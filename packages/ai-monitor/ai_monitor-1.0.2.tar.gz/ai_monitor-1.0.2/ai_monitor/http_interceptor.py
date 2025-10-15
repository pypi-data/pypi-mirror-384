#!/usr/bin/env python3
"""
AI Monitor Interceptor - Monitors existing HTTP calls without changing source code
This module automatically intercepts requests to OpenAI/Azure OpenAI endpoints
"""

import requests
import time
import json
from functools import wraps
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Store original requests methods
_original_post = requests.post
_original_request = requests.request

def extract_openai_data(url, json_data, headers, response):
    """Extract OpenAI call data from HTTP request/response"""
    try:
        # Check if this is an OpenAI/Azure OpenAI API call
        if not any(domain in url.lower() for domain in ['openai.azure.com', 'api.openai.com', 'chat/completions']):
            return None
        
        print(f"🔍 [Monitor] Intercepted OpenAI API call to: {url}")
        
        # Extract model from request (Azure OpenAI uses URL path, not JSON)
        model = "unknown"
        
        # First try to get model from JSON (standard OpenAI)
        if json_data:
            if isinstance(json_data, dict):
                model = json_data.get('model', 'unknown')
            elif isinstance(json_data, str):
                try:
                    parsed = json.loads(json_data)
                    model = parsed.get('model', 'unknown')
                except:
                    pass
        
        # If model is still unknown, extract from Azure OpenAI URL path
        if model == "unknown" and 'deployments/' in url:
            try:
                # Extract model from URL like: /deployments/gpt-4o/chat/completions
                url_parts = url.split('/deployments/')
                if len(url_parts) > 1:
                    deployment_part = url_parts[1].split('/')[0]  # Get gpt-4o
                    model = deployment_part
                    print(f"🔍 [Monitor] Extracted model from Azure URL: {model}")
            except Exception as e:
                print(f"⚠️ [Monitor] Could not extract model from URL: {e}")
        
        # Extract prompt/messages from request
        prompt = ""
        if json_data and isinstance(json_data, dict):
            messages = json_data.get('messages', [])
            if messages and isinstance(messages, list):
                # Combine all user messages
                prompt_parts = []
                for msg in messages:
                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        prompt_parts.append(msg.get('content', ''))
                prompt = ' '.join(prompt_parts)
            else:
                prompt = json_data.get('prompt', str(json_data)[:200])
        
        # Extract response data
        response_text = ""
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        
        try:
            if response and hasattr(response, 'json'):
                resp_json = response.json()
                
                # Extract response text
                choices = resp_json.get('choices', [])
                if choices and len(choices) > 0:
                    choice = choices[0]
                    if 'message' in choice:
                        response_text = choice['message'].get('content', '')
                    elif 'text' in choice:
                        response_text = choice.get('text', '')
                
                # Extract token usage
                usage = resp_json.get('usage', {})
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
                
        except Exception as e:
            logger.debug(f"Error extracting response data: {e}")
        
        return {
            'model': model,
            'prompt': prompt,
            'response': response_text,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens
        }
        
    except Exception as e:
        logger.error(f"Error extracting OpenAI data: {e}")
        return None

def monitored_post(*args, **kwargs):
    """Monitored version of requests.post"""
    url = args[0] if args else kwargs.get('url', '')
    json_data = kwargs.get('json')
    headers = kwargs.get('headers', {})
    
    # Start timing
    start_time = time.time()
    
    # Make the original request
    response = _original_post(*args, **kwargs)
    
    # End timing
    end_time = time.time()
    latency = end_time - start_time
    
    # Try to extract OpenAI data and monitor it
    try:
        openai_data = extract_openai_data(url, json_data, headers, response)
        
        if openai_data:
            # Import here to avoid circular imports
            from .core import get_default_monitor
            monitor = get_default_monitor()
            
            if monitor:
                print(f"📊 [Monitor] Recording LLM call:")
                print(f"   Model: {openai_data['model']}")
                print(f"   Tokens: {openai_data['input_tokens']}→{openai_data['output_tokens']}")
                print(f"   Latency: {latency:.2f}s")
                
                # Enhance with quality analysis
                try:
                    from .quality_analyzer import enhance_llm_call_with_quality_analysis
                    
                    # Prepare call data for quality analysis
                    call_data = {
                        'prompt': openai_data['prompt'],
                        'response': openai_data['response'],
                        'model': openai_data['model'],
                        'input_tokens': openai_data['input_tokens'],
                        'output_tokens': openai_data['output_tokens'],
                        'latency': latency,
                        'metadata': {
                            'intercepted': True,
                            'url': url,
                            'method': 'POST'
                        }
                    }
                    
                    # Perform quality analysis
                    enhanced_data = enhance_llm_call_with_quality_analysis(call_data)
                    
                    # Print quality metrics
                    print(f"🎯 [Quality] Score: {enhanced_data['quality_score']:.2f}")
                    print(f"🚨 [Quality] Hallucination Risk: {enhanced_data['hallucination_risk']}")
                    if enhanced_data['drift_detected']:
                        print(f"⚠️ [Quality] Drift detected!")
                    if enhanced_data['quality_issues']:
                        print(f"❌ [Quality] Issues: {', '.join(enhanced_data['quality_issues'])}")
                    
                    # Update metadata with quality info
                    openai_data['quality_analysis'] = enhanced_data['quality_analysis']
                    
                except Exception as quality_error:
                    print(f"⚠️ [Quality] Analysis failed: {quality_error}")
                
                # Record the call
                call_id = monitor.record_llm_call(
                    model=openai_data['model'],
                    prompt=openai_data['prompt'],
                    response=openai_data['response'],
                    input_tokens=openai_data['input_tokens'],
                    output_tokens=openai_data['output_tokens'],
                    latency=latency,
                    metadata={
                        'intercepted': True,
                        'url': url,
                        'method': 'POST',
                        'quality_analysis': openai_data.get('quality_analysis', {})
                    }
                )
                
                print(f"🎯 [Monitor] LLM call recorded with ID: {call_id}")
                
                # Force immediate export by checking exporters
                if hasattr(monitor, '_exporters'):
                    print(f"🔍 [Monitor] Available exporters: {len(monitor._exporters)}")
                    for i, exporter in enumerate(monitor._exporters):
                        exporter_type = type(exporter).__name__
                        print(f"   Exporter {i}: {exporter_type}")
                
                # Try to trigger immediate metrics export for debugging
                try:
                    monitor._export_metrics()
                    print(f"✅ [Monitor] Forced metrics export completed")
                except Exception as export_error:
                    print(f"⚠️ [Monitor] Metrics export failed: {export_error}")
                    
    except Exception as e:
        logger.error(f"Error monitoring request: {e}")
    
    return response

def monitored_request(*args, **kwargs):
    """Monitored version of requests.request"""
    method = args[0] if args else kwargs.get('method', '')
    url = args[1] if len(args) > 1 else kwargs.get('url', '')
    
    # Only monitor POST requests to OpenAI endpoints
    if method.upper() == 'POST':
        return monitored_post(url, **{k: v for k, v in kwargs.items() if k != 'method'})
    else:
        return _original_request(*args, **kwargs)

def enable_http_monitoring():
    """Enable HTTP request monitoring by monkey-patching requests"""
    print("🔧 [HTTP Monitor] Enabling HTTP request monitoring...")
    
    # Monkey patch requests module
    requests.post = monitored_post
    requests.request = monitored_request
    
    print("✅ [HTTP Monitor] HTTP monitoring enabled!")
    print("📊 [HTTP Monitor] All requests.post() calls will be monitored")
    print("🎯 [HTTP Monitor] OpenAI API calls will be automatically detected and recorded")

def disable_http_monitoring():
    """Disable HTTP request monitoring"""
    print("🔧 [HTTP Monitor] Disabling HTTP request monitoring...")
    
    # Restore original methods
    requests.post = _original_post
    requests.request = _original_request
    
    print("✅ [HTTP Monitor] HTTP monitoring disabled")

# Auto-enable monitoring when imported
if __name__ != "__main__":
    # Auto-enable will be handled by one_line_setup
    pass
