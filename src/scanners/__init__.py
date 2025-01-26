from .port_scanner import PortScanner
from .tech_detector import TechDetector
from .ssl_checker import SSLChecker
from .waf_detector import WAFDetector
from .cdn_detector import CDNDetector

__all__ = [
    'PortScanner',
    'TechDetector',
    'SSLChecker',
    'WAFDetector',
    'CDNDetector'
]

# Scanner configuration
CONCURRENT_SCANS = 10
SCAN_TIMEOUT = 30
RETRY_COUNT = 3

# Scanner registry
AVAILABLE_SCANNERS = {
    'port': PortScanner,
    'tech': TechDetector,
    'ssl': SSLChecker,
    'waf': WAFDetector,
    'cdn': CDNDetector
}
