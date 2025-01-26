import tempfile
import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from datetime import datetime
import logging
import platform
from urllib.parse import urlparse, urljoin, urlunparse
import re
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

class URLHelper:
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL format"""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'http://' + url
            parsed = urlparse(url)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''
        ))
        if not parsed.path:
            normalized += '/'
        return normalized

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def join_urls(base: str, url: str) -> str:
        """Join base URL with relative URL"""
        return urljoin(base, url)

    @staticmethod
    def extract_urls(content: str) -> List[str]:
        """Extract URLs from content"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, content)

class NetworkHelper:
    @staticmethod
    def resolve_dns(domain: str) -> List[str]:
        """Resolve DNS records"""
        try:
            return socket.gethostbyname_ex(domain)[2]
        except socket.gaierror:
            return []

    @staticmethod
    def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
        """Check if port is open"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                return sock.connect_ex((host, port)) == 0
        except Exception:
            return False

    @staticmethod
    def get_http_headers(url: str) -> Dict:
        """Get HTTP headers from URL"""
        try:
            response = requests.head(url, allow_redirects=True)
            return dict(response.headers)
        except Exception:
            return {}

class FileHelper:
    @staticmethod
    def create_temp_dir() -> Path:
        """Create temporary directory"""
        temp_dir = tempfile.mkdtemp(prefix='nexus_')
        return Path(temp_dir)

    @staticmethod
    def create_temp_file(content: str = '') -> Path:
        """Create temporary file with optional content"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            prefix='nexus_',
            delete=False
        )
        if content:
            temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)

    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
        """Safely delete file or directory"""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True
        except Exception:
            return False

    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> bool:
        """Ensure directory exists"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False

class HashHelper:
    @staticmethod
    def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
        """Calculate file hash"""
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def calculate_string_hash(text: str, algorithm: str = 'sha256') -> str:
        """Calculate string hash"""
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode())
        return hash_obj.hexdigest()

class ThreadHelper:
    @staticmethod
    def parallel_execute(func: callable, items: list, max_workers: int = 10) -> list:
        """Execute function in parallel"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(func, items))

class SystemHelper:
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get system information"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'hostname': platform.node()
        }

    @staticmethod
    def get_memory_usage() -> Dict[str, int]:
        """Get memory usage"""
        import psutil
        process = psutil.Process(os.getpid())
        return {
            'rss': process.memory_info().rss,
            'vms': process.memory_info().vms
        }

class TimeHelper:
    @staticmethod
    def get_timestamp() -> float:
        """Get current timestamp"""
        return datetime.now().timestamp()

    @staticmethod
    def format_timestamp(timestamp: float, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format timestamp"""
        return datetime.fromtimestamp(timestamp).strftime(format_str)

class JsonHelper:
    @staticmethod
    def save_json(data: Any, file_path: Union[str, Path], pretty: bool = True) -> bool:
        """Save JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4 if pretty else None)
            return True
        except Exception:
            return False

    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Optional[Any]:
        """Load JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

# Create helper instances
url_helper = URLHelper()
network_helper = NetworkHelper()
file_helper = FileHelper()
hash_helper = HashHelper()
thread_helper = ThreadHelper()
system_helper = SystemHelper()
time_helper = TimeHelper()
json_helper = JsonHelper()

# Export helper functions
normalize_url = url_helper.normalize_url
is_valid_url = url_helper.is_valid_url
join_urls = url_helper.join_urls
extract_urls = url_helper.extract_urls
resolve_dns = network_helper.resolve_dns
check_port = network_helper.check_port
get_http_headers = network_helper.get_http_headers
create_temp_dir = file_helper.create_temp_dir
create_temp_file = file_helper.create_temp_file
safe_delete = file_helper.safe_delete
ensure_dir = file_helper.ensure_dir
calculate_file_hash = hash_helper.calculate_file_hash
calculate_string_hash = hash_helper.calculate_string_hash
parallel_execute = thread_helper.parallel_execute
get_system_info = system_helper.get_system_info
get_memory_usage = system_helper.get_memory_usage
get_timestamp = time_helper.get_timestamp
format_timestamp = time_helper.format_timestamp
save_json = json_helper.save_json
load_json = json_helper.load_json
