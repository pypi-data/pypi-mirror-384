"""
Collectors module for metrics and trace collection.
"""

# Re-export from utils for backward compatibility
from .utils import MetricsCollector, TraceCollector

__all__ = ['MetricsCollector', 'TraceCollector']
