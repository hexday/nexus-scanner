#!/usr/bin/env python3

import typer
import rich
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from typing import Optional, List

from src.core.scanner import Scanner
from src.utils.config import Config
from src.ui.animations import LoadingAnimation
from src.reporters.cli_reporter import CLIReporter

app = typer.Typer(
    name="nexus",
    help="Advanced Web Scanner with Beautiful CLI Interface",
    add_completion=False,
)

console = Console()


def version_callback(value: bool):
    if value:
        console.print("[bold cyan]Nexus[/] version 1.0.0")
        raise typer.Exit()


@app.command()
def scan(
        target: str = typer.Argument(..., help="Target URL or domain to scan"),
        depth: int = typer.Option(3, "--depth", "-d", help="Scan depth level"),
        threads: int = typer.Option(10, "--threads", "-t", help="Number of threads"),
        output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
        version: Optional[bool] = typer.Option(
            None, "--version", callback=version_callback, help="Show version information"
        ),
):
    """
    Perform comprehensive scan on target website with beautiful animations
    """
    # Display banner
    banner = """
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
    """
    console.print(Panel.fit(banner, border_style="cyan"))
    console.print(f"[bold green]Target:[/] {target}")

    # Initialize components
    config = Config(
        target=target,
        depth=depth,
        threads=threads,
        verbose=verbose
    )

    scanner = Scanner(config)
    reporter = CLIReporter()
    loading = LoadingAnimation()

    try:
        # Start scanning with animation
        with loading.start("Initializing scan..."):
            scanner.initialize()

        with loading.start("Performing scan..."):
            results = scanner.run()

        # Display results
        reporter.display_results(results)

        # Export if output specified
        if output:
            reporter.export_results(results, output)
            console.print(f"[green]Results exported to:[/] {output}")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)


@app.command()
def monitor(
        target: str = typer.Argument(..., help="Target URL to monitor"),
        interval: int = typer.Option(60, "--interval", "-i", help="Monitoring interval in seconds"),
):
    """
    Monitor target website performance and availability
    """
    console.print(f"Starting monitoring for {target}")
    # Monitoring implementation will be added here


@app.command()
def analyze(
        results: Path = typer.Argument(..., help="Path to scan results file"),
):
    """
    Analyze previous scan results
    """
    console.print(f"Analyzing results from {results}")
    # Analysis implementation will be added here


def main():
    """
    Main entry point for Nexus CLI
    """
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan interrupted by user[/]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Fatal Error:[/] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
