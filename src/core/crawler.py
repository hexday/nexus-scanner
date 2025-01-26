from __future__ import annotations
import asyncio
import aiohttp
from typing import Set, List, Dict, Optional, AsyncGenerator
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from bs4 import BeautifulSoup
from rich.progress import Progress


@dataclass
class CrawlResult:
    url: str
    depth: int
    links: List[str]
    assets: Dict[str, List[str]]
    status_code: int
    content_type: str
    size: int


class Crawler:
    def __init__(self,
                 base_url: str,
                 max_depth: int = 3,
                 max_urls: int = 1000,
                 concurrent_requests: int = 20,
                 respect_robots: bool = True):

        self.base_url = base_url
        self.max_depth = max_depth
        self.max_urls = max_urls
        self.concurrent_requests = concurrent_requests
        self.respect_robots = respect_robots

        self.visited: Set[str] = set()
        self.queued: Set[str] = set()
        self.robots_rules: Set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None
        self.progress: Optional[Progress] = None

        # Statistics
        self.total_size = 0
        self.start_time = 0
        self.request_count = 0

    async def initialize(self):
        """Initialize crawler components and session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Nexus-Crawler/1.0',
                'Accept': '*/*'
            }
        )

        if self.respect_robots:
            await self.fetch_robots_txt()

        self.progress = Progress()
        self.crawl_task = self.progress.add_task(
            "[cyan]Crawling...",
            total=self.max_urls
        )

    async def fetch_robots_txt(self):
        """Fetch and parse robots.txt"""
        robots_url = urljoin(self.base_url, '/robots.txt')
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    self.parse_robots_txt(content)
        except Exception:
            pass

    def parse_robots_txt(self, content: str):
        """Parse robots.txt content"""
        current_agent = None
        for line in content.split('\n'):
            line = line.strip().lower()
            if line.startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                if agent == '*' or 'nexus' in agent:
                    current_agent = agent
            elif line.startswith('disallow:') and current_agent:
                path = line.split(':', 1)[1].strip()
                self.robots_rules.add(path)

    def is_allowed(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        if not self.respect_robots:
            return True

        parsed = urlparse(url)
        path = parsed.path or '/'

        for rule in self.robots_rules:
            if path.startswith(rule):
                return False
        return True

    async def process_page(self, url: str, depth: int) -> CrawlResult:
        """Process a single page and extract information"""
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                size = len(content.encode('utf-8'))
                self.total_size += size
                self.request_count += 1

                soup = BeautifulSoup(content, 'html.parser')

                # Extract links and assets
                links = self.extract_links(soup, url)
                assets = {
                    'images': self.extract_assets(soup, 'img', 'src', url),
                    'scripts': self.extract_assets(soup, 'script', 'src', url),
                    'styles': self.extract_assets(soup, 'link', 'href', url),
                }

                return CrawlResult(
                    url=url,
                    depth=depth,
                    links=links,
                    assets=assets,
                    status_code=response.status,
                    content_type=response.headers.get('content-type', ''),
                    size=size
                )

        except Exception as e:
            return CrawlResult(
                url=url,
                depth=depth,
                links=[],
                assets={},
                status_code=-1,
                content_type='',
                size=0
            )

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract and normalize all links from page"""
        links = []
        for anchor in soup.find_all('a'):
            href = anchor.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                if self.should_crawl(absolute_url):
                    links.append(absolute_url)
        return links

    def extract_assets(self, soup: BeautifulSoup, tag: str, attr: str, base_url: str) -> List[str]:
        """Extract and normalize asset URLs"""
        assets = []
        for element in soup.find_all(tag):
            url = element.get(attr)
            if url:
                absolute_url = urljoin(base_url, url)
                assets.append(absolute_url)
        return assets

    def should_crawl(self, url: str) -> bool:
        """Determine if URL should be crawled"""
        parsed = urlparse(url)
        base_domain = urlparse(self.base_url).netloc

        return (
                parsed.netloc == base_domain and
                url not in self.visited and
                url not in self.queued and
                len(self.visited) < self.max_urls and
                self.is_allowed(url)
        )

    async def crawl(self) -> AsyncGenerator[CrawlResult, None]:
        """Main crawling logic"""
        await self.initialize()

        try:
            # Start with base URL
            self.queued.add(self.base_url)
            queue = [(self.base_url, 0)]

            while queue and len(self.visited) < self.max_urls:
                # Process batch of URLs
                batch = []
                for _ in range(min(self.concurrent_requests, len(queue))):
                    if not queue:
                        break
                    url, depth = queue.pop(0)
                    if url not in self.visited and depth <= self.max_depth:
                        batch.append(self.process_page(url, depth))
                        self.visited.add(url)

                if batch:
                    results = await asyncio.gather(*batch)

                    for result in results:
                        # Update progress
                        self.progress.update(
                            self.crawl_task,
                            completed=len(self.visited)
                        )

                        # Queue new URLs
                        if result.depth < self.max_depth:
                            for link in result.links:
                                if self.should_crawl(link):
                                    queue.append((link, result.depth + 1))
                                    self.queued.add(link)

                        yield result

        finally:
            await self.session.close()
            if self.progress:
                self.progress.stop()

    def get_statistics(self) -> Dict[str, int]:
        """Return crawling statistics"""
        return {
            'urls_crawled': len(self.visited),
            'total_size_bytes': self.total_size,
            'total_requests': self.request_count
        }
