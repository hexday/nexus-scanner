from .performance import PerformanceMonitor
from .resources import ResourceMonitor
from .stats import StatsCollector

__all__ = [
    'PerformanceMonitor',
    'ResourceMonitor',
    'StatsCollector'
]

# Monitoring Configuration
METRICS_INTERVAL = 1.0
HISTORY_SIZE = 3600
ALERT_THRESHOLDS = {
    'cpu': 90,
    'memory': 85,
    'disk': 90,
    'latency': 1000
}

# Monitoring Registry
MONITORS = {
    'performance': PerformanceMonitor,
    'resources': ResourceMonitor,
    'stats': StatsCollector
}
