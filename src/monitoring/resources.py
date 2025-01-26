import psutil
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
import time
from pathlib import Path
import logging

@dataclass
class ResourceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, int]
    thread_count: int
    open_files: int
    timestamp: float

class ResourceMonitor:
    def __init__(self, interval: float = 1.0):
        self.logger = logging.getLogger("webscout.resources")
        self.interval = interval
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history_size = 3600  # 1 hour at 1-second intervals
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self):
        """Start resource monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Resource monitoring started")

    def stop(self):
        """Stop resource monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Resource monitoring stopped")

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics"""
        return ResourceMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage('/').percent,
            network_io=self._get_network_io(),
            thread_count=threading.active_count(),
            open_files=self._count_open_files(),
            timestamp=time.time()
        )

    def get_metrics_history(self) -> List[ResourceMetrics]:
        """Get historical metrics"""
        with self._lock:
            return self.metrics_history.copy()

    def get_resource_summary(self) -> Dict:
        """Get summary of resource usage"""
        metrics = self.get_current_metrics()
        return {
            "cpu": {
                "current": metrics.cpu_percent,
                "cores": psutil.cpu_count(),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            "memory": {
                "used_percent": metrics.memory_percent,
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available
            },
            "disk": {
                "used_percent": metrics.disk_usage,
                "io_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
            },
            "network": metrics.network_io,
            "process": {
                "threads": metrics.thread_count,
                "open_files": metrics.open_files,
                "connections": len(psutil.Process().connections())
            }
        }

    def get_alerts(self) -> List[Dict]:
        """Get resource usage alerts"""
        alerts = []
        metrics = self.get_current_metrics()

        if metrics.cpu_percent > 90:
            alerts.append({
                "level": "CRITICAL",
                "resource": "CPU",
                "message": f"High CPU usage: {metrics.cpu_percent}%"
            })

        if metrics.memory_percent > 85:
            alerts.append({
                "level": "WARNING",
                "resource": "Memory",
                "message": f"High memory usage: {metrics.memory_percent}%"
            })

        if metrics.disk_usage > 90:
            alerts.append({
                "level": "WARNING",
                "resource": "Disk",
                "message": f"High disk usage: {metrics.disk_usage}%"
            })

        return alerts

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = self.get_current_metrics()
                with self._lock:
                    self.metrics_history.append(metrics)
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history.pop(0)
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")

    def _get_network_io(self) -> Dict[str, int]:
        """Get network I/O statistics"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }

    def _count_open_files(self) -> int:
        """Count number of open files"""
        try:
            return len(psutil.Process().open_files())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    def get_process_tree(self) -> Dict:
        """Get process hierarchy tree"""
        def get_process_info(proc):
            try:
                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "cpu_percent": proc.cpu_percent(),
                    "memory_percent": proc.memory_percent(),
                    "children": [get_process_info(child) for child in proc.children()]
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return {}

        return get_process_info(psutil.Process())

    def get_resource_limits(self) -> Dict:
        """Get system resource limits"""
        return {
            "max_threads": threading.Thread._counter,
            "max_files": self._get_file_limit(),
            "memory_limit": self._get_memory_limit()
        }

    def _get_file_limit(self) -> int:
        """Get system file limit"""
        try:
            import resource
            return resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        except ImportError:
            return 0

    def _get_memory_limit(self) -> int:
        """Get system memory limit"""
        try:
            import resource
            return resource.getrlimit(resource.RLIMIT_AS)[0]
        except ImportError:
            return 0
