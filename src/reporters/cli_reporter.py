from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.tree import Tree
from dataclasses import dataclass
import time
from pathlib import Path



from ..utils.config import Config


class CLIReporter:
    def __init__(self,  config: Config):
        self.config = config
        self.console = Console()
        self.start_time = time.time()

    def print_banner(self):
        """Display Nexus banner"""
        banner = """
        ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
        ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
        ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
        ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
        ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
        ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
        """
        self.console.print(Panel(
            banner,
            title="Security Scanner",
            subtitle="v1.0.0",

        ))

    def print_scan_info(self, target: str, scan_type: str, options: Dict):
        """Display scan information"""
        info_table = Table(title="Scan Configuration")
        info_table.add_column("Setting")
        info_table.add_column("Value")

        info_table.add_row("Target", target)
        info_table.add_row("Scan Type", scan_type)

        for key, value in options.items():
            info_table.add_row(key, str(value))

        self.console.print(info_table)

    def print_findings(self, findings: List[Dict]):
        """Display scan findings"""
        if not findings:
            self.console.print("\n[yellow]No security findings detected.[/yellow]")
            return

        findings_table = Table(
            title=f"Security Findings ({len(findings)})",
            title_style=self.colors.get_color("primary")
        )

        findings_table.add_column("Severity", style="bold")
        findings_table.add_column("Category")
        findings_table.add_column("Description")
        findings_table.add_column("Location")

        for finding in findings:
            findings_table.add_row(
                self._get_severity_style(finding['severity']),
                finding['category'],
                finding['description'],
                finding.get('location', 'N/A')
            )

        self.console.print(findings_table)

    def print_statistics(self, stats: Dict):
        """Display scan statistics"""
        stats_table = Table(title="Scan Statistics")
        stats_table.add_column("Metric", style=self.colors.get_color("primary"))
        stats_table.add_column("Value")

        duration = time.time() - self.start_time
        stats_table.add_row("Duration", f"{duration:.2f} seconds")

        for key, value in stats.items():
            stats_table.add_row(key, str(value))

        self.console.print(stats_table)

    def print_vulnerabilities(self, vulns: List[Dict]):
        """Display detailed vulnerability information"""
        vuln_tree = Tree("🔍 Vulnerabilities")

        for vuln in vulns:
            severity_color = self._get_severity_color(vuln['severity'])
            vuln_node = vuln_tree.add(
                f"[{severity_color}]{vuln['title']}[/{severity_color}]"
            )

            vuln_node.add(f"Severity: {vuln['severity']}")
            vuln_node.add(f"CVSS: {vuln.get('cvss', 'N/A')}")
            vuln_node.add(f"Description: {vuln['description']}")

            if 'remediation' in vuln:
                rem_node = vuln_node.add("Remediation")
                rem_node.add(Markdown(vuln['remediation']))

            if 'references' in vuln:
                ref_node = vuln_node.add("References")
                for ref in vuln['references']:
                    ref_node.add(ref)

        self.console.print(vuln_tree)

    def print_code_snippet(self, code: str, language: str, line_numbers: bool = True):
        """Display formatted code snippet"""
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=line_numbers,
            word_wrap=True
        )
        self.console.print(syntax)

    def print_summary(self, summary: Dict):
        """Display scan summary"""
        panel = Panel(
            self._format_summary(summary),
            title="Scan Summary",
            style=self.colors.get_color("primary")
        )
        self.console.print(panel)

    def save_report(self, findings: List[Dict], output_file: Path):
        """Save report to file"""
        with open(output_file, 'w') as f:
            self.console.file = f
            self.print_banner()
            self.print_findings(findings)
            self.print_statistics({
                'Duration': f"{time.time() - self.start_time:.2f} seconds",
                'Total Findings': len(findings)
            })
            self.console.file = None

    def _get_severity_style(self, severity: str) -> str:
        """Get styled severity text"""
        styles = {
            'CRITICAL': 'bold red',
            'HIGH': 'red',
            'MEDIUM': 'yellow',
            'LOW': 'blue',
            'INFO': 'green'
        }
        return f"[{styles.get(severity.upper(), 'white')}]{severity}[/]"

    def _get_severity_color(self, severity: str) -> str:
        """Get severity color"""
        colors = {
            'CRITICAL': 'red1',
            'HIGH': 'red3',
            'MEDIUM': 'yellow',
            'LOW': 'blue',
            'INFO': 'green'
        }
        return colors.get(severity.upper(), 'white')

    def _format_summary(self, summary: Dict) -> str:
        """Format summary text"""
        lines = []
        for key, value in summary.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
