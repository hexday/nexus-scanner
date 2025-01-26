from typing import Dict, List, Optional, Set
import aiohttp
import dns.resolver
import ipaddress
import socket
from dataclasses import dataclass
import json
from pathlib import Path
import logging
import asyncio


@dataclass
class CDNDetection:
    name: str
    confidence: float
    cname_records: List[str]
    ip_ranges: List[str]
    headers: Dict[str, str]


class CDNDetector:
    def __init__(self, signatures_path: Optional[str] = None):
        self.logger = logging.getLogger("nexus.cdndetector")
        self.signatures = self._load_signatures(signatures_path)
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 3
        self.dns_resolver.lifetime = 3

    def _load_signatures(self, signatures_path: Optional[str]) -> Dict[str, Dict]:
        """Load CDN signatures database"""
        if signatures_path:
            path = Path(signatures_path)
        else:
            path = Path(__file__).parent / "data" / "cdn_signatures.json"

        with open(path) as f:
            return json.load(f)

    async def detect_cdn(self, hostname: str) -> Optional[CDNDetection]:
        """Perform comprehensive CDN detection"""
        detections: Set[CDNDetection] = set()

        # DNS-based detection
        cname_records = await self._get_cname_records(hostname)
        ip_addresses = await self._resolve_ip_addresses(hostname)

        # HTTP-based detection
        headers = await self._get_http_headers(hostname)

        for cdn_name, signature in self.signatures.items():
            confidence = 0.0
            matched_cnames = []
            matched_ranges = []
            matched_headers = {}

            # Check CNAME patterns
            if 'cname_patterns' in signature:
                for cname in cname_records:
                    for pattern in signature['cname_patterns']:
                        if pattern.lower() in cname.lower():
                            confidence += 0.4
                            matched_cnames.append(cname)

            # Check IP ranges
            if 'ip_ranges' in signature:
                for ip in ip_addresses:
                    for ip_range in signature['ip_ranges']:
                        if self._ip_in_range(ip, ip_range):
                            confidence += 0.3
                            matched_ranges.append(ip_range)

            # Check headers
            if 'headers' in signature:
                for header, pattern in signature['headers'].items():
                    if header.lower() in headers:
                        if pattern.lower() in headers[header.lower()].lower():
                            confidence += 0.3
                            matched_headers[header] = headers[header.lower()]

            if confidence > 0:
                detections.add(CDNDetection(
                    name=cdn_name,
                    confidence=min(confidence, 1.0),
                    cname_records=matched_cnames,
                    ip_ranges=matched_ranges,
                    headers=matched_headers
                ))

        return max(detections, key=lambda x: x.confidence) if detections else None

    async def _get_cname_records(self, hostname: str) -> List[str]:
        """Get CNAME records for hostname"""
        try:
            answers = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.dns_resolver.resolve(hostname, 'CNAME')
            )
            return [str(answer.target).rstrip('.') for answer in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return []
        except Exception as e:
            self.logger.debug(f"CNAME resolution error: {str(e)}")
            return []

    async def _resolve_ip_addresses(self, hostname: str) -> List[str]:
        """Resolve hostname to IP addresses"""
        try:
            answers = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.dns_resolver.resolve(hostname, 'A')
            )
            return [str(answer) for answer in answers]
        except Exception as e:
            self.logger.debug(f"IP resolution error: {str(e)}")
            return []

    async def _get_http_headers(self, hostname: str) -> Dict[str, str]:
        """Get HTTP response headers"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"https://{hostname}", timeout=5) as response:
                    return {k.lower(): v for k, v in response.headers.items()}
            except Exception as e:
                self.logger.debug(f"HTTP header retrieval error: {str(e)}")
                return {}

    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP address is in CIDR range"""
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range)
        except ValueError:
            return False

    async def get_cdn_features(self, hostname: str) -> Dict[str, any]:
        """Get detailed CDN features for analysis"""
        cdn_detection = await self.detect_cdn(hostname)
        if not cdn_detection:
            return {}

        return {
            'cdn_name': cdn_detection.name,
            'confidence': cdn_detection.confidence,
            'features': {
                'cname_records': cdn_detection.cname_records,
                'ip_ranges': cdn_detection.ip_ranges,
                'headers': cdn_detection.headers
            }
        }

    async def check_cdn_security(self, hostname: str) -> Dict[str, any]:
        """Check CDN security features"""
        headers = await self._get_http_headers(hostname)
        security_features = {
            'https': await self._check_https(hostname),
            'hsts': 'strict-transport-security' in headers,
            'xss_protection': 'x-xss-protection' in headers,
            'content_security': 'content-security-policy' in headers,
            'frame_options': 'x-frame-options' in headers
        }

        return security_features

    async def _check_https(self, hostname: str) -> bool:
        """Check HTTPS availability"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://{hostname}", timeout=5) as response:
                    return response.url.scheme == 'https'
        except:
            return False
