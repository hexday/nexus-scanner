from typing import Dict, List, Optional, Set
import aiohttp
import asyncio
import json
from pathlib import Path
import logging
from dataclasses import dataclass
import random
import time


@dataclass
class WAFDetection:
    name: str
    confidence: float
    version: Optional[str] = None
    details: Optional[Dict[str, str]] = None


class WAFDetector:
    def __init__(self, signatures_path: Optional[str] = None):
        self.logger = logging.getLogger("nexus.wafdetector")
        self.signatures = self._load_signatures(signatures_path)
        self.user_agents = self._load_user_agents()

        # Test payloads for WAF detection
        self.test_payloads = [
            "' OR '1'='1",
            "<script>alert(1)</script>",
            "../../../etc/passwd",
            "/?exec=/bin/bash",
            "/?param=<img/src=x onerror=alert(1)>",
            "/?param=/*!50000SELECT*/",
            "/?param=union select password from users",
            "/?param=eval(base64_decode('PHN2Zy9vbmxvYWQ9YWxlcnQoMSk+'))"
        ]

    def _load_signatures(self, signatures_path: Optional[str]) -> Dict[str, Dict]:
        """Load WAF signatures from file"""
        if signatures_path:
            path = Path(signatures_path)
        else:
            path = Path(__file__).parent / "data" / "waf_signatures.json"

        with open(path) as f:
            return json.load(f)

    def _load_user_agents(self) -> List[str]:
        """Load list of user agents for detection"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Nexus Security Scanner/1.0"
        ]

    async def detect_waf(self, url: str) -> Optional[WAFDetection]:
        """Detect WAF presence and type"""
        detected_wafs: Set[WAFDetection] = set()

        # Perform passive detection first
        passive_detection = await self._passive_detection(url)
        if passive_detection:
            detected_wafs.add(passive_detection)

        # Perform active detection if needed
        if not detected_wafs:
            active_detections = await self._active_detection(url)
            detected_wafs.update(active_detections)

        # Return the detection with highest confidence
        if detected_wafs:
            return max(detected_wafs, key=lambda x: x.confidence)
        return None

    async def _passive_detection(self, url: str) -> Optional[WAFDetection]:
        """Perform passive WAF detection through headers"""
        async with aiohttp.ClientSession() as session:
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                async with session.get(url, headers=headers) as response:
                    headers = dict(response.headers)

                    for waf_name, signature in self.signatures.items():
                        if 'headers' in signature:
                            confidence = self._check_headers(headers, signature['headers'])
                            if confidence > 0:
                                return WAFDetection(
                                    name=waf_name,
                                    confidence=confidence,
                                    details={'detected_by': 'headers'}
                                )

            except Exception as e:
                self.logger.debug(f"Passive detection error: {str(e)}")
        return None

    async def _active_detection(self, url: str) -> Set[WAFDetection]:
        """Perform active WAF detection through test payloads"""
        detections = set()
        tasks = []

        for payload in self.test_payloads:
            task = asyncio.create_task(
                self._test_payload(url, payload)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, WAFDetection):
                detections.add(result)

        return detections

    async def _test_payload(self, url: str, payload: str) -> Optional[WAFDetection]:
        """Test a single payload against the target"""
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'X-Requested-With': 'XMLHttpRequest'
                }

                test_url = f"{url}{payload}"
                async with session.get(test_url, headers=headers) as response:
                    status = response.status
                    headers = dict(response.headers)
                    body = await response.text()

                    return self._analyze_response(status, headers, body)

            except aiohttp.ClientError as e:
                # Connection errors might indicate WAF blocking
                return self._analyze_error(e)

            except Exception as e:
                self.logger.debug(f"Payload test error: {str(e)}")

        return None

    def _check_headers(self, headers: Dict[str, str], signatures: Dict[str, str]) -> float:
        """Check response headers against WAF signatures"""
        confidence = 0.0

        for header, pattern in signatures.items():
            header_lower = header.lower()
            if header_lower in headers:
                if pattern.lower() in headers[header_lower].lower():
                    confidence += 0.3

        return min(confidence, 1.0)

    def _analyze_response(self, status: int, headers: Dict[str, str], body: str) -> Optional[WAFDetection]:
        """Analyze response for WAF fingerprints"""
        for waf_name, signature in self.signatures.items():
            confidence = 0.0

            # Check status code
            if status in signature.get('status_codes', []):
                confidence += 0.3

            # Check response headers
            if 'headers' in signature:
                confidence += self._check_headers(headers, signature['headers'])

            # Check response body
            if 'body_patterns' in signature:
                for pattern in signature['body_patterns']:
                    if pattern.lower() in body.lower():
                        confidence += 0.3

            if confidence > 0.5:
                return WAFDetection(
                    name=waf_name,
                    confidence=confidence,
                    details={
                        'detected_by': 'active_test',
                        'status_code': str(status)
                    }
                )

        return None

    def _analyze_error(self, error: Exception) -> Optional[WAFDetection]:
        """Analyze connection errors for WAF detection"""
        error_str = str(error).lower()

        # Common WAF blocking patterns
        if 'connection reset' in error_str:
            return WAFDetection(
                name='Unknown WAF',
                confidence=0.7,
                details={'detected_by': 'connection_reset'}
            )
        elif 'timeout' in error_str:
            return WAFDetection(
                name='Unknown WAF',
                confidence=0.5,
                details={'detected_by': 'timeout'}
            )

        return None
