# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-14

### Added
- **Plug & Play Monitoring**: Zero-configuration monitoring for AI agents
- **HTTP Interception**: Automatic monitoring of OpenAI API calls
- **Quality Analysis**: Hallucination detection and drift analysis
- **Prometheus Metrics**: Comprehensive metrics export
- **OpenTelemetry Tracing**: Distributed tracing support
- **Traceloop Integration**: Enterprise-grade observability
- **Decorator API**: Easy-to-use decorators for monitoring
- **Context Managers**: Flexible monitoring contexts
- **Flask Integration**: One-line Flask app monitoring
- **Multi-Agent Support**: Monitor complex agent systems
- **LangChain Integration**: Seamless LangChain monitoring

### Features
- **Zero Source Code Changes**: Drop-in monitoring solution
- **Automatic LLM Detection**: Recognizes OpenAI, Anthropic, and custom APIs
- **Real-time Metrics**: Latency, tokens, costs, and quality scores
- **Comprehensive Tracing**: Request/response tracing with metadata
- **Quality Assurance**: Automated hallucination and drift detection
- **Multiple Export Options**: Prometheus, Jaeger, and Traceloop
- **System Metrics**: CPU, memory, and disk monitoring
- **Alert Integration**: Configurable thresholds and alerts

### Dependencies
- Core: `numpy>=1.20.0`
- Optional: Prometheus, OpenTelemetry, Traceloop SDK, psutil

### Installation
```bash
pip install ai-monitor
# For full features:
pip install ai-monitor[all]
```
