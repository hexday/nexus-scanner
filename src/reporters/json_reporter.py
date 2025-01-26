import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import dataclasses
from dataclasses import dataclass
import uuid


@dataclass
class ScanMetadata:
    scan_id: str
    timestamp: str
    duration: float
    target: str
    scan_type: str
    scanner_version: str


class JSONReporter:
    def __init__(self, pretty_print: bool = True):
        self.pretty_print = pretty_print
        self.scan_id = str(uuid.uuid4())
        self.start_time = datetime.now()

    def generate_report(self,
                        findings: List[Dict],
                        statistics: Dict,
                        metadata: Dict,
                        vulnerabilities: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate comprehensive JSON report"""
        scan_metadata = ScanMetadata(
            scan_id=self.scan_id,
            timestamp=self.start_time.isoformat(),
            duration=(datetime.now() - self.start_time).total_seconds(),
            target=metadata.get('target', ''),
            scan_type=metadata.get('scan_type', ''),
            scanner_version=metadata.get('version', '1.0.0')
        )

        report = {
            'metadata': dataclasses.asdict(scan_metadata),
            'summary': {
                'total_findings': len(findings),
                'severity_counts': self._count_severities(findings),
                'risk_score': self._calculate_risk_score(findings)
            },
            'statistics': statistics,
            'findings': self._process_findings(findings),
            'scan_coverage': self._generate_coverage_info(statistics)
        }

        if vulnerabilities:
            report['vulnerabilities'] = self._process_vulnerabilities(vulnerabilities)

        return report

    def save_report(self, report: Dict[str, Any], output_file: Path):
        """Save report to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            if self.pretty_print:
                json.dump(report, f, indent=2, ensure_ascii=False)
            else:
                json.dump(report, f, ensure_ascii=False)

    def _process_findings(self, findings: List[Dict]) -> List[Dict]:
        """Process and enrich findings data"""
        processed_findings = []

        for finding in findings:
            processed_finding = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'severity': finding.get('severity', 'UNKNOWN'),
                'category': finding.get('category', 'UNKNOWN'),
                'title': finding.get('title', ''),
                'description': finding.get('description', ''),
                'location': finding.get('location', ''),
                'evidence': finding.get('evidence', ''),
                'cvss_score': finding.get('cvss_score'),
                'cwe_id': finding.get('cwe_id'),
                'remediation': finding.get('remediation', ''),
                'references': finding.get('references', []),
                'tags': finding.get('tags', []),
                'metadata': finding.get('metadata', {})
            }
            processed_findings.append(processed_finding)

        return processed_findings

    def _process_vulnerabilities(self, vulnerabilities: List[Dict]) -> List[Dict]:
        """Process vulnerability data"""
        processed_vulns = []

        for vuln in vulnerabilities:
            processed_vuln = {
                'id': str(uuid.uuid4()),
                'title': vuln.get('title', ''),
                'description': vuln.get('description', ''),
                'severity': vuln.get('severity', 'UNKNOWN'),
                'cvss_vector': vuln.get('cvss_vector', ''),
                'cvss_score': vuln.get('cvss_score'),
                'cwe_id': vuln.get('cwe_id'),
                'affected_components': vuln.get('affected_components', []),
                'proof_of_concept': vuln.get('proof_of_concept', ''),
                'remediation': vuln.get('remediation', ''),
                'references': vuln.get('references', []),
                'exploitation_status': vuln.get('exploitation_status', 'unknown')
            }
            processed_vulns.append(processed_vuln)

        return processed_vulns

    def _count_severities(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity"""
        severity_counts = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'INFO': 0
        }

        for finding in findings:
            severity = finding.get('severity', 'UNKNOWN').upper()
            if severity in severity_counts:
                severity_counts[severity] += 1

        return severity_counts

    def _calculate_risk_score(self, findings: List[Dict]) -> float:
        """Calculate overall risk score"""
        severity_weights = {
            'CRITICAL': 10.0,
            'HIGH': 8.0,
            'MEDIUM': 5.0,
            'LOW': 2.0,
            'INFO': 0.5
        }

        total_score = 0.0
        total_findings = len(findings)

        if total_findings == 0:
            return 0.0

        for finding in findings:
            severity = finding.get('severity', 'UNKNOWN').upper()
            total_score += severity_weights.get(severity, 0.0)

        return min(10.0, total_score / total_findings)

    def _generate_coverage_info(self, statistics: Dict) -> Dict[str, Any]:
        """Generate scan coverage information"""
        return {
            'scanned_components': statistics.get('scanned_components', []),
            'excluded_components': statistics.get('excluded_components', []),
            'scan_depth': statistics.get('scan_depth', 'unknown'),
            'coverage_percentage': statistics.get('coverage_percentage', 0),
            'total_tests_run': statistics.get('total_tests', 0),
            'successful_tests': statistics.get('successful_tests', 0),
            'failed_tests': statistics.get('failed_tests', 0)
        }
