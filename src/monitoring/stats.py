from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
import time
import logging
from collections import deque


@dataclass
class ScanStats:
    total_scans: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    total_urls: int = 0
    total_vulnerabilities: int = 0
    scan_duration: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class PerformanceStats:
    average_response_time: float = 0.0
    requests_per_second: float = 0.0
    success_rate: float = 0.0
    error_rate: float = 0.0


class StatsCollector:
    def __init__(self, history_size: int = 1000):
        self.logger = logging.getLogger("nexus.stats")
        self.history_size = history_size
        self.scan_stats = ScanStats()
        self.performance_stats = PerformanceStats()

        # History tracking
        self.response_times: deque[float] = deque(maxlen=history_size)
        self.error_counts: deque[int] = deque(maxlen=history_size)
        self.request_counts: deque[int] = deque(maxlen=history_size)

        # Thread safety
        self._lock = threading.Lock()

        # Real-time tracking
        self.current_requests = 0
        self.start_timestamp = time.time()

    def start_scan(self):
        """Record scan start"""
        with self._lock:
            self.scan_stats.start_time = time.time()
            self.scan_stats.total_scans += 1

    def end_scan(self, success: bool = True):
        """Record scan completion"""
        with self._lock:
            self.scan_stats.end_time = time.time()
            if success:
                self.scan_stats.successful_scans += 1
            else:
                self.scan_stats.failed_scans += 1

            if self.scan_stats.start_time:
                self.scan_stats.scan_duration = self.scan_stats.end_time - self.scan_stats.start_time

    def record_url(self):
        """Record URL discovery"""
        with self._lock:
            self.scan_stats.total_urls += 1

    def record_vulnerability(self):
        """Record vulnerability discovery"""
        with self._lock:
            self.scan_stats.total_vulnerabilities += 1

    def record_response_time(self, response_time: float):
        """Record request response time"""
        with self._lock:
            self.response_times.append(response_time)
            self._update_performance_stats()

    def record_request(self, success: bool = True):
        """Record request completion"""
        with self._lock:
            self.current_requests += 1
            self.request_counts.append(1)
            if not success:
                self.error_counts.append(1)
            self._update_performance_stats()

    def _update_performance_stats(self):
        """Update performance statistics"""
        if self.response_times:
            self.performance_stats.average_response_time = sum(self.response_times) / len(self.response_times)

        elapsed_time = time.time() - self.start_timestamp
        if elapsed_time > 0:
            self.performance_stats.requests_per_second = self.current_requests / elapsed_time

        total_requests = len(self.request_counts)
        if total_requests > 0:
            self.performance_stats.error_rate = len(self.error_counts) / total_requests
            self.performance_stats.success_rate = 1 - self.performance_stats.error_rate

    def get_scan_summary(self) -> Dict:
        """Get scan statistics summary"""
        with self._lock:
            return {
                "total_scans": self.scan_stats.total_scans,
                "successful_scans": self.scan_stats.successful_scans,
                "failed_scans": self.scan_stats.failed_scans,
                "total_urls": self.scan_stats.total_urls,
                "total_vulnerabilities": self.scan_stats.total_vulnerabilities,
                "scan_duration": self.scan_stats.scan_duration,
                "start_time": self.scan_stats.start_time,
                "end_time": self.scan_stats.end_time
            }

    def get_performance_summary(self) -> Dict:
        """Get performance statistics summary"""
        with self._lock:
            return {
                "average_response_time": self.performance_stats.average_response_time,
                "requests_per_second": self.performance_stats.requests_per_second,
                "success_rate": self.performance_stats.success_rate,
                "error_rate": self.performance_stats.error_rate,
                "total_requests": self.current_requests
            }

    def get_historical_data(self) -> Dict:
        """Get historical statistics data"""
        with self._lock:
            return {
                "response_times": list(self.response_times),
                "error_counts": list(self.error_counts),
                "request_counts": list(self.request_counts)
            }

    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self.scan_stats = ScanStats()
            self.performance_stats = PerformanceStats()
            self.response_times.clear()
            self.error_counts.clear()
            self.request_counts.clear()
            self.current_requests = 0
            self.start_timestamp = time.time()
