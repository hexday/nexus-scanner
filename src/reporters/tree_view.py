from typing import Dict, List, Optional, Any
from rich.tree import Tree
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from dataclasses import dataclass
import time


@dataclass
class TreeNode:
    name: str
    type: str
    children: List['TreeNode']
    data: Optional[Dict] = None
    severity: Optional[str] = None


class TreeViewReporter:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.severity_icons = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🔵',
            'INFO': '🟢'
        }

    def generate_tree(self, scan_data: Dict[str, Any]) -> Tree:
        """Generate main tree view of scan results"""
        root = Tree(
            f"[bold blue]Scan Results - {scan_data.get('target', 'Unknown Target')}[/]",
            guide_style="bold bright_blue"
        )

        # Add metadata section
        self._add_metadata_branch(root, scan_data.get('metadata', {}))

        # Add findings section
        self._add_findings_branch(root, scan_data.get('findings', []))

        # Add vulnerabilities section
        self._add_vulnerabilities_branch(root, scan_data.get('vulnerabilities', []))

        # Add statistics section
        self._add_statistics_branch(root, scan_data.get('statistics', {}))

        return root

    def _add_metadata_branch(self, root: Tree, metadata: Dict):
        """Add metadata information to tree"""
        meta_branch = root.add("[bold cyan]Metadata[/]")
        for key, value in metadata.items():
            meta_branch.add(f"[cyan]{key}:[/] {value}")

    def _add_findings_branch(self, root: Tree, findings: List[Dict]):
        """Add findings information to tree"""
        findings_branch = root.add(
            f"[bold red]Findings ({len(findings)})[/]"
        )

        # Group findings by severity
        findings_by_severity = self._group_by_severity(findings)

        for severity, severity_findings in findings_by_severity.items():
            severity_branch = findings_branch.add(
                f"{self.severity_icons.get(severity, '•')} {severity} ({len(severity_findings)})"
            )

            for finding in severity_findings:
                finding_node = severity_branch.add(
                    f"[bold]{finding.get('title', 'Untitled Finding')}[/]"
                )
                self._add_finding_details(finding_node, finding)

    def _add_vulnerabilities_branch(self, root: Tree, vulnerabilities: List[Dict]):
        """Add vulnerabilities information to tree"""
        if not vulnerabilities:
            return

        vuln_branch = root.add(
            f"[bold red]Vulnerabilities ({len(vulnerabilities)})[/]"
        )

        for vuln in vulnerabilities:
            vuln_node = vuln_branch.add(
                f"{self.severity_icons.get(vuln.get('severity', 'INFO'), '•')} "
                f"[bold]{vuln.get('title', 'Untitled Vulnerability')}[/]"
            )
            self._add_vulnerability_details(vuln_node, vuln)

    def _add_statistics_branch(self, root: Tree, statistics: Dict):
        """Add statistics information to tree"""
        stats_branch = root.add("[bold green]Statistics[/]")

        # Add coverage information
        coverage = statistics.get('coverage', {})
        coverage_node = stats_branch.add("[cyan]Coverage[/]")
        coverage_node.add(f"Total Components: {coverage.get('total', 0)}")
        coverage_node.add(f"Coverage Rate: {coverage.get('rate', 0)}%")

        # Add timing information
        timing = statistics.get('timing', {})
        timing_node = stats_branch.add("[cyan]Timing[/]")
        timing_node.add(f"Duration: {timing.get('duration', 0)}s")
        timing_node.add(f"Start Time: {timing.get('start_time', 'Unknown')}")

    def _add_finding_details(self, node: Tree, finding: Dict):
        """Add detailed finding information"""
        node.add(f"Description: {finding.get('description', 'No description')}")
        node.add(f"Location: {finding.get('location', 'Unknown')}")

        if 'evidence' in finding:
            evidence_node = node.add("Evidence")
            self._add_code_snippet(evidence_node, finding['evidence'])

        if 'remediation' in finding:
            node.add(f"Remediation: {finding['remediation']}")

    def _add_vulnerability_details(self, node: Tree, vuln: Dict):
        """Add detailed vulnerability information"""
        node.add(f"CVSS Score: {vuln.get('cvss_score', 'N/A')}")
        node.add(f"Description: {vuln.get('description', 'No description')}")

        if 'affected_components' in vuln:
            components_node = node.add("Affected Components")
            for component in vuln['affected_components']:
                components_node.add(component)

        if 'remediation' in vuln:
            node.add(f"Remediation: {vuln['remediation']}")

    def _add_code_snippet(self, node: Tree, code: str):
        """Add formatted code snippet"""
        syntax = Syntax(
            code,
            "python",
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
        node.add(Panel(syntax))

    def _group_by_severity(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Group findings by severity level"""
        grouped = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': [],
            'INFO': []
        }

        for finding in findings:
            severity = finding.get('severity', 'INFO').upper()
            if severity in grouped:
                grouped[severity].append(finding)

        return grouped

    def display_tree(self, tree: Tree):
        """Display the generated tree"""
        self.console.print(tree)
