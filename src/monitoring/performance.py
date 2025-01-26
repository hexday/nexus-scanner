from typing import Dict, List, Optional, Tuple
import time
import psutil
import threading
from dataclasses import dataclass
from collections import deque
import statistics


@dataclass
class ResourceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_io: Tuple[float, float]  # read/write
    network_io: Tuple[float, float]  # sent/received
    thread_count: int
    timestamp: float


class PerformanceMonitor:
    def __init__(self, history_size: int = 60):
        self.history_size = history_size
        self.metrics_history: deque[ResourceMetrics] = deque(maxlen=history_size)
        self.start_time = time.time()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Initialize counters
        self.process = psutil.Process()
        self._last_disk_io = self.process.io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._last_check_time = time.time()

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous performance monitoring"""
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join()

    def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            self.collect_metrics()
            time.sleep(interval)

    def collect_metrics(self) -> ResourceMetrics:
        """Collect current performance metrics"""
        current_time = time.time()
        time_delta = current_time - self._last_check_time

        # CPU and Memory
        cpu_percent = self.process.cpu_percent()
        memory_percent = self.process.memory_percent()

        # Disk I/O
        current_disk_io = self.process.io_counters()
        disk_read = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta
        disk_write = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta
        self._last_disk_io = current_disk_io

        # Network I/O
        current_net_io = psutil.net_io_counters()
        net_sent = (current_net_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta
        net_recv = (current_net_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta
        self._last_net_io = current_net_io

        # Thread count
        thread_count = threading.active_count()

        metrics = ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_io=(disk_read, disk_write),
            network_io=(net_sent, net_recv),
            thread_count=thread_count,
            timestamp=current_time
        )

        self.metrics_history.append(metrics)
        self._last_check_time = current_time
        return metrics

    def get_average_metrics(self, window: int = None) -> ResourceMetrics:
        """Calculate average metrics over specified window"""
        if not self.metrics_history:
            return self._empty_metrics()

        window = window or len(self.metrics_history)
        recent_metrics = list(self.metrics_history)[-window:]

        return ResourceMetrics(
            cpu_percent=statistics.mean(m.cpu_percent for m in recent_metrics),
            memory_percent=statistics.mean(m.memory_percent for m in recent_metrics),
            disk_io=(
                statistics.mean(m.disk_io[0] for m in recent_metrics),
                statistics.mean(m.disk_io[1] for m in recent_metrics)
            ),
            network_io=(
                statistics.mean(m.network_io[0] for m in recent_metrics),
                statistics.mean(m.network_io[1] for m in recent_metrics)
            ),
            thread_count=int(statistics.mean(m.thread_count for m in recent_metrics)),
            timestamp=time.time()
        )

    def get_peak_metrics(self) -> ResourceMetrics:
        """Get peak resource usage metrics"""
        if not self.metrics_history:
            return self._empty_metrics()

        return ResourceMetrics(
            cpu_percent=max(m.cpu_percent for m in self.metrics_history),
            memory_percent=max(m.memory_percent for m in self.metrics_history),
            disk_io=(
                max(m.disk_io[0] for m in self.metrics_history),
                max(m.disk_io[1] for m in self.metrics_history)
            ),
            network_io=(
                max(m.network_io[0] for m in self.metrics_history),
                max(m.network_io[1] for m in self.metrics_history)
            ),
            thread_count=max(m.thread_count for m in self.metrics_history),
            timestamp=time.time()
        )

    def get_performance_report(self) -> Dict[str, any]:
        """Generate comprehensive performance report"""
        avg_metrics = self.get_average_metrics()
        peak_metrics = self.get_peak_metrics()

        return {
            "duration": time.time() - self.start_time,
            "average": {
                "cpu_usage": f"{avg_metrics.cpu_percent:.1f}%",
                "memory_usage": f"{avg_metrics.memory_percent:.1f}%",
                "disk_read": self._format_bytes(avg_metrics.disk_io[0]),
                "disk_write": self._format_bytes(avg_metrics.disk_io[1]),
                "network_sent": self._format_bytes(avg_metrics.network_io[0]),
                "network_received": self._format_bytes(avg_metrics.network_io[1]),
                "threads": avg_metrics.thread_count
            },
            "peak": {
                "cpu_usage": f"{peak_metrics.cpu_percent:.1f}%",
                "memory_usage": f"{peak_metrics.memory_percent:.1f}%",
                "disk_read": self._format_bytes(peak_metrics.disk_io[0]),
                "disk_write": self._format_bytes(peak_metrics.disk_io[1]),
                "network_sent": self._format_bytes(peak_metrics.network_io[0]),
                "network_received": self._format_bytes(peak_metrics.network_io[1]),
                "threads": peak_metrics.thread_count
            }
        }

    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bytes_value < 1024:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f} TB/s"

    def _empty_metrics(self) -> ResourceMetrics:
        """Create empty metrics object"""
        return ResourceMetrics(
            cpu_percent=0.0,
            memory_percent=0.0,
            disk_io=(0.0, 0.0),
            network_io=(0.0, 0.0),
            thread_count=0,
            timestamp=time.time()
        )

    def get_resource_usage_trends(self) -> Dict[str, List[float]]:
        """Calculate resource usage trends"""
        if not self.metrics_history:
            return {}

        return {
            "cpu": [m.cpu_percent for m in self.metrics_history],
            "memory": [m.memory_percent for m in self.metrics_history],
            "disk_read": [m.disk_io[0] for m in self.metrics_history],
            "disk_write": [m.disk_io[1] for m in self.metrics_history],
            "network_sent": [m.network_io[0] for m in self.metrics_history],
            "network_received": [m.network_io[1] for m in self.metrics_history],
            "threads": [m.thread_count for m in self.metrics_history]
        }
