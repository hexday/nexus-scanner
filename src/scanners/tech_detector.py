from typing import Dict, List, Optional, Set
import re
import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import concurrent.futures


@dataclass
class Technology:
    name: str
    category: str
    version: Optional[str] = None
    confidence: float = 0.0
    website: Optional[str] = None
    cpe: Optional[str] = None


class TechDetector:
    def __init__(self, signatures_path: Optional[str] = None):
        self.logger = logging.getLogger("nexus.techdetector")
        self.signatures = self._load_signatures(signatures_path)
        self._pattern_cache: Dict[str, re.Pattern] = {}
        self.headers = {
            'User-Agent': 'Nexus-Scanner/1.0',
            'Accept': '*/*'
        }

    def _load_signatures(self, signatures_path: Optional[str]) -> Dict:
        """Load technology signatures database"""
        if signatures_path:
            path = Path(signatures_path)
        else:
            path = Path(__file__).parent / "data" / "tech_signatures.json"

        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load signatures: {str(e)}")
            return {}

    async def detect_technologies(self, url: str) -> List[Technology]:
        """Detect technologies used on a website"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            detected: Set[Technology] = set()

            # Extract all scripts
            scripts = [script.get('src', '') for script in soup.find_all('script')]

            # Extract meta tags
            meta_tags = {
                meta.get('name', '').lower(): meta.get('content', '')
                for meta in soup.find_all('meta')
            }

            # Check headers
            self._check_headers(response.headers, detected)

            # Check cookies
            self._check_cookies(response.cookies, detected)

            # Check HTML patterns
            self._check_html_patterns(response.text, detected)

            # Check script patterns
            self._check_script_patterns(self.signatures.get('script_patterns', []), scripts, detected)

            # Check meta patterns
            self._check_meta_patterns(meta_tags, detected)

            return list(detected)

        except Exception as e:
            self.logger.error(f"Error detecting technologies for {url}: {str(e)}")
            return []

    def _check_headers(self, headers: Dict, detected: Set[Technology]):
        """Check response headers for technology signatures"""
        for tech_name, signature in self.signatures.get('headers', {}).items():
            for header, pattern in signature.items():
                if header.lower() in headers:
                    if self._match_pattern(pattern, headers[header.lower()]):
                        version = self._extract_version(headers[header.lower()], signature.get('version_pattern'))
                        detected.add(Technology(
                            name=tech_name,
                            category='Server',
                            version=version,
                            confidence=0.9
                        ))

    def _check_cookies(self, cookies: Dict, detected: Set[Technology]):
        """Check cookies for technology signatures"""
        for tech_name, signature in self.signatures.get('cookies', {}).items():
            for cookie_name in signature:
                if cookie_name in cookies:
                    detected.add(Technology(
                        name=tech_name,
                        category='Framework',
                        confidence=0.8
                    ))

    def _check_html_patterns(self, html: str, detected: Set[Technology]):
        """Check HTML content for technology patterns"""
        for tech_name, signature in self.signatures.get('html_patterns', {}).items():
            for pattern in signature:
                if self._match_pattern(pattern, html):
                    version = self._extract_version(html, signature.get('version_pattern'))
                    detected.add(Technology(
                        name=tech_name,
                        category='Frontend',
                        version=version,
                        confidence=0.7
                    ))

    def _check_script_patterns(self, script_patterns: List[str], scripts: List[str], detected: Set[Technology]):
        """Check script sources for technology patterns"""
        for pattern in script_patterns:
            if pattern not in self._pattern_cache:
                self._pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)

            for script in scripts:
                if self._pattern_cache[pattern].search(script):
                    detected.add(Technology(
                        name=self._get_script_tech_name(pattern),
                        category='JavaScript',
                        confidence=0.8
                    ))

    def _check_meta_patterns(self, meta_tags: Dict, detected: Set[Technology]):
        """Check meta tags for technology signatures"""
        for tech_name, signature in self.signatures.get('meta_patterns', {}).items():
            for meta_name, pattern in signature.items():
                if meta_name in meta_tags and self._match_pattern(pattern, meta_tags[meta_name]):
                    detected.add(Technology(
                        name=tech_name,
                        category='Meta',
                        confidence=0.6
                    ))

    def _match_pattern(self, pattern: str, text: str) -> bool:
        """Match pattern against text"""
        if pattern not in self._pattern_cache:
            self._pattern_cache[pattern] = re.compile(pattern, re.IGNORECASE)
        return bool(self._pattern_cache[pattern].search(text))

    def _extract_version(self, text: str, version_pattern: Optional[str]) -> Optional[str]:
        """Extract version information using pattern"""
        if not version_pattern:
            return None

        if version_pattern not in self._pattern_cache:
            self._pattern_cache[version_pattern] = re.compile(version_pattern)

        match = self._pattern_cache[version_pattern].search(text)
        return match.group(1) if match else None

    def _get_script_tech_name(self, pattern: str) -> str:
        """Get technology name from script pattern"""
        for tech_name, signature in self.signatures.get('script_technologies', {}).items():
            if pattern in signature:
                return tech_name
        return "Unknown Technology"

    def get_cpe_identifier(self, tech: Technology) -> Optional[str]:
        """Get CPE identifier for detected technology"""
        if tech.name in self.signatures.get('cpe_mapping', {}):
            return self.signatures['cpe_mapping'][tech.name]
        return None
