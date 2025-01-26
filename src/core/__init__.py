from .scanner import Scanner
from .crawler import Crawler
from .analyzer import Analyzer

__all__ = [
    'Scanner',
    'Crawler',
    'Analyzer'
]

# Version information
VERSION = '1.0.0'
AUTHOR = 'Nexus Security Team'
LICENSE = 'MIT'

# Module configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = f'Nexus-Scanner/{VERSION}'
