from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import json
import asyncio
from collections import defaultdict
from urllib.parse import urlparse
import ssl
import socket
from concurrent.futures import ThreadPoolExecutor


@dataclass
class SecurityAnalysis:
    ssl_grade: str
    security_headers: Dict[str, str]
    vulnerabilities: List[str]
    risk_score: float


@dataclass
class PerformanceMetrics:
    load_time: float
    response_size: int
    requests_count: int
    performance_score: float


@dataclass
class AnalysisResult:
    url: str
    security: SecurityAnalysis
    performance: PerformanceMetrics
    technologies: List[str]
    seo_metrics: Dict[str, any]
    structure: Dict[str, List[str]]
    timestamp: float


class Analyzer:
    def __init__(self):
        self.technology_patterns = self._load_technology_patterns()
        self.security_checks = self._initialize_security_checks()
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _load_technology_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Load technology detection patterns"""
        return {
            'frameworks': {
                'Django': ['csrftoken', 'django'],
                'React': ['react', 'reactjs'],
                'Vue': ['vue', 'vuejs'],
                'Angular': ['ng-', 'angular'],
            },
            'servers': {
                'Nginx': ['nginx'],
                'Apache': ['apache'],
                'IIS': ['iis', 'asp.net'],
            },
            'analytics': {
                'Google Analytics': ['ga.js', 'analytics'],
                'Hotjar': ['hotjar'],
                'Mixpanel': ['mixpanel'],
            }
        }

    def _initialize_security_checks(self) -> List[callable]:
        """Initialize security check functions"""
        return [
            self._check_ssl_configuration,
            self._check_security_headers,
            self._check_common_vulnerabilities
        ]

    async def analyze_target(self, scan_results: List[dict]) -> AnalysisResult:
        """Perform comprehensive analysis of scan results"""
        base_url = scan_results[0]['url']

        # Parallel analysis tasks
        security_task = asyncio.create_task(self._analyze_security(base_url))
        performance_task = asyncio.create_task(self._analyze_performance(scan_results))
        tech_task = asyncio.create_task(self._analyze_technologies(scan_results))
        seo_task = asyncio.create_task(self._analyze_seo(scan_results))
        structure_task = asyncio.create_task(self._analyze_structure(scan_results))

        # Gather all results
        security, performance, technologies, seo, structure = await asyncio.gather(
            security_task,
            performance_task,
            tech_task,
            seo_task,
            structure_task
        )

        return AnalysisResult(
            url=base_url,
            security=security,
            performance=performance,
            technologies=technologies,
            seo_metrics=seo,
            structure=structure,
            timestamp=scan_results[0]['timestamp']
        )

    async def _analyze_security(self, url: str) -> SecurityAnalysis:
        """Analyze security aspects"""
        ssl_grade = await self._check_ssl_configuration(url)
        headers = await self._check_security_headers(url)
        vulns = await self._check_common_vulnerabilities(url)

        # Calculate risk score based on findings
        risk_score = self._calculate_risk_score(ssl_grade, headers, vulns)

        return SecurityAnalysis(
            ssl_grade=ssl_grade,
            security_headers=headers,
            vulnerabilities=vulns,
            risk_score=risk_score
        )

    async def _check_ssl_configuration(self, url: str) -> str:
        """Check SSL/TLS configuration"""
        try:
            hostname = urlparse(url).netloc
            context = ssl.create_default_context()

            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()

            # Grade based on protocol version and cipher strength
            if cipher[1] >= 256 and cert.get('version') == 3:
                return 'A+'
            elif cipher[1] >= 128:
                return 'A'
            return 'B'
        except:
            return 'F'

    async def _analyze_performance(self, results: List[dict]) -> PerformanceMetrics:
        """Analyze performance metrics"""
        total_size = sum(r.get('size', 0) for r in results)
        avg_load_time = sum(r.get('response_time', 0) for r in results) / len(results)

        # Calculate performance score
        score = self._calculate_performance_score(avg_load_time, total_size, len(results))

        return PerformanceMetrics(
            load_time=avg_load_time,
            response_size=total_size,
            requests_count=len(results),
            performance_score=score
        )

    async def _analyze_technologies(self, results: List[dict]) -> List[str]:
        """Detect technologies used"""
        technologies = set()

        for result in results:
            content = result.get('content', '')
            headers = result.get('headers', {})

            # Check headers
            server = headers.get('Server', '')
            if server:
                technologies.add(f"Server: {server}")

            # Check patterns
            for category, tech_patterns in self.technology_patterns.items():
                for tech, patterns in tech_patterns.items():
                    if any(pattern in content.lower() for pattern in patterns):
                        technologies.add(f"{category}: {tech}")

        return sorted(list(technologies))

    async def _analyze_seo(self, results: List[dict]) -> Dict[str, any]:
        """Analyze SEO aspects"""
        seo_metrics = {
            'meta_tags': defaultdict(int),
            'heading_structure': defaultdict(int),
            'image_alt_texts': 0,
            'broken_links': 0
        }

        for result in results:
            # Analyze meta tags
            meta_tags = result.get('meta_tags', {})
            for tag in meta_tags:
                seo_metrics['meta_tags'][tag] += 1

            # Analyze headings
            headings = result.get('headings', {})
            for level, count in headings.items():
                seo_metrics['heading_structure'][level] += count

            # Count images with alt text
            seo_metrics['image_alt_texts'] += result.get('images_with_alt', 0)

            # Count broken links
            if result.get('status_code', 200) >= 400:
                seo_metrics['broken_links'] += 1

        return dict(seo_metrics)

    async def _analyze_structure(self, results: List[dict]) -> Dict[str, List[str]]:
        """Analyze site structure"""
        structure = {
            'pages': [],
            'assets': [],
            'endpoints': [],
            'dynamic_routes': []
        }

        for result in results:
            url = result['url']
            parsed = urlparse(url)

            # Categorize URLs
            if any(ext in parsed.path for ext in ['.jpg', '.png', '.css', '.js']):
                structure['assets'].append(url)
            elif '?' in url:
                structure['dynamic_routes'].append(url)
            elif parsed.path.startswith('/api/'):
                structure['endpoints'].append(url)
            else:
                structure['pages'].append(url)

        return structure

    def _calculate_risk_score(self, ssl_grade: str, headers: Dict[str, str], vulns: List[str]) -> float:
        """Calculate security risk score"""
        score = 10.0  # Start with perfect score

        # SSL penalties
        ssl_penalties = {'A+': 0, 'A': 0.5, 'B': 1, 'C': 2, 'F': 5}
        score -= ssl_penalties.get(ssl_grade, 5)

        # Header penalties
        for header, value in headers.items():
            if value == 'missing':
                score -= 0.5

        # Vulnerability penalties
        score -= len(vulns) * 1.5

        return max(0, min(10, score))

    def _calculate_performance_score(self, load_time: float, size: int, requests: int) -> float:
        """Calculate performance score"""
        score = 10.0

        # Time penalties
        if load_time > 2.0:
            score -= (load_time - 2.0) * 2

        # Size penalties
        size_mb = size / (1024 * 1024)
        if size_mb > 1.0:
            score -= (size_mb - 1.0)

        # Request penalties
        if requests > 30:
            score -= (requests - 30) * 0.1

        return max(0, min(10, score))

    def get_recommendations(self, analysis: AnalysisResult) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Security recommendations
        if analysis.security.risk_score < 7:
            recommendations.append("Improve security headers implementation")
            if analysis.security.ssl_grade != 'A+':
                recommendations.append("Upgrade SSL/TLS configuration")

        # Performance recommendations
        if analysis.performance.performance_score < 7:
            if analysis.performance.load_time > 2.0:
                recommendations.append("Optimize page load times")
            if analysis.performance.response_size > 1024 * 1024:
                recommendations.append("Reduce page size")

        # SEO recommendations
        if not analysis.seo_metrics['meta_tags'].get('description'):
            recommendations.append("Add meta descriptions")

        return recommendations
