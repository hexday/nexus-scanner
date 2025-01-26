from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
from rich.progress import Progress, TaskID
from urllib.parse import urlparse, urljoin

from ..utils.config import Config
from ..monitoring.stats import ScanStats
from ..utils.helpers import normalize_url


@dataclass
class ScanResult:
    url: str
    status_code: int
    response_time: float
    content_type: str
    headers: Dict[str, str]
    technologies: List[str]
    security_headers: Dict[str, str]
    links: List[str]
    timestamp: float


class Scanner:
    def __init__(self, config: Config):
        self.config = config
        self.stats = ScanStats()
        self.results: List[ScanResult] = []
        self.visited_urls: set = set()
        self.session: Optional[aiohttp.ClientSession] = None
        self.progress: Optional[Progress] = None
        self.scan_task_id: Optional[TaskID] = None

    async def initialize(self):
        """Initialize scanner components and validate target"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Nexus-Scanner/1.0',
                'Accept': '*/*'
            }
        )

        # Validate target URL
        parsed = urlparse(self.config.target)
        if not parsed.scheme:
            self.config.target = f'http://{self.config.target}'

        # Initialize progress bars
        self.progress = Progress()
        self.scan_task_id = self.progress.add_task(
            "[cyan]Scanning...", total=None
        )

    async def scan_url(self, url: str) -> ScanResult:
        """Scan a single URL and return detailed results"""
        start_time = time.time()

        try:
            async with self.session.get(url) as response:
                content = await response.text()
                elapsed = time.time() - start_time

                result = ScanResult(
                    url=url,
                    status_code=response.status,
                    response_time=elapsed,
                    content_type=response.headers.get('content-type', ''),
                    headers=dict(response.headers),
                    technologies=self.detect_technologies(content, response.headers),
                    security_headers=self.analyze_security_headers(response.headers),
                    links=self.extract_links(content, url),
                    timestamp=time.time()
                )

                self.stats.update(result)
                return result

        except Exception as e:
            # Log error and return partial result
            return ScanResult(
                url=url,
                status_code=-1,
                response_time=-1,
                content_type='',
                headers={},
                technologies=[],
                security_headers={},
                links=[],
                timestamp=time.time()
            )

    def detect_technologies(self, content: str, headers: Dict[str, str]) -> List[str]:
        """Detect technologies used by the target"""
        technologies = []

        # Server software
        if 'Server' in headers:
            technologies.append(headers['Server'])

        # Common frameworks
        tech_signatures = {
            'Django': 'csrftoken',
            'Laravel': 'laravel_session',
            'React': 'react-root',
            'Vue': 'vue-app'
        }

        for tech, signature in tech_signatures.items():
            if signature in content.lower():
                technologies.append(tech)

        return technologies

    def analyze_security_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Analyze security-related headers"""
        security_headers = {
            'X-XSS-Protection': headers.get('X-XSS-Protection', 'Not Set'),
            'X-Frame-Options': headers.get('X-Frame-Options', 'Not Set'),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options', 'Not Set'),
            'Strict-Transport-Security': headers.get('Strict-Transport-Security', 'Not Set'),
            'Content-Security-Policy': headers.get('Content-Security-Policy', 'Not Set')
        }
        return security_headers

    def extract_links(self, content: str, base_url: str) -> List[str]:
        """Extract and normalize links from content"""
        from bs4 import BeautifulSoup

        links = []
        soup = BeautifulSoup(content, 'html.parser')

        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self.should_scan_url(absolute_url):
                    links.append(absolute_url)

        return links

    def should_scan_url(self, url: str) -> bool:
        """Determine if URL should be scanned based on configuration"""
        parsed = urlparse(url)
        base_domain = urlparse(self.config.target).netloc

        return (
                parsed.netloc == base_domain and
                url not in self.visited_urls and
                len(self.visited_urls) < self.config.max_urls
        )

    async def run(self) -> List[ScanResult]:
        """Execute the complete scan"""
        await self.initialize()

        try:
            # Start with the target URL
            urls_to_scan = [self.config.target]

            while urls_to_scan and len(self.visited_urls) < self.config.max_urls:
                # Create tasks for batch of URLs
                tasks = []
                for _ in range(min(self.config.threads, len(urls_to_scan))):
                    if not urls_to_scan:
                        break
                    url = urls_to_scan.pop(0)
                    if url not in self.visited_urls:
                        self.visited_urls.add(url)
                        tasks.append(self.scan_url(url))

                # Execute batch
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Process results
                    for result in batch_results:
                        if isinstance(result, ScanResult):
                            self.results.append(result)
                            urls_to_scan.extend(result.links)

                    # Update progress
                    self.progress.update(
                        self.scan_task_id,
                        completed=len(self.visited_urls)
                    )

            return self.results

        finally:
            await self.session.close()
            if self.progress:
                self.progress.stop()

    def get_statistics(self) -> Dict[str, Any]:
        """Return scan statistics"""
        return self.stats.get_summary()
