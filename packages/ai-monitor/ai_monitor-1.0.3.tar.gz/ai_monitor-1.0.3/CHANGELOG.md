# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Removed traceloop-sdk from `ai-monitor[all]` to resolve googleapis-common-protos conflicts
- **Installation Options**: `ai-monitor[all]` now includes tracing, prometheus, and system monitoring without conflicts

### Changed
- Separated traceloop from the all-in-one installation option

## [1.0.2] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Updated OpenTelemetry to v1.22+ for full compatibility with Traceloop SDK
- **googleapis-common-protos**: Resolved protobuf version conflicts in ai-monitor[all] installation

### Changed
- Updated tracing dependencies to OpenTelemetry v1.22.0+ for better compatibility

## [1.0.1] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Resolved OpenTelemetry version conflicts between Jaeger and Traceloop
- **Installation Options**: Separated `tracing` (v1.20+) and `jaeger` (v1.15) optional dependencies
- **Compatibility**: Fixed `ai-monitor[all]` installation issues

### Changed
- Updated OpenTelemetry dependencies to compatible versions
- Added separate `jaeger` optional dependency for legacy Jaeger support

### Installation
```bash
# All features (now works without conflicts)
pip install ai-monitor[all]

# Specific tracing options
pip install ai-monitor[tracing]        # Modern Jaeger (v1.20+)
pip install ai-monitor[jaeger]         # Legacy Jaeger (v1.15)
```
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
