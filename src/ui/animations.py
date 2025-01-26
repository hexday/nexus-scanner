from typing import List, Optional, Dict
import time
import threading
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.panel import Panel
from .colors import NexusColors


class Animation:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.colors = NexusColors()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None


class LoadingAnimation(Animation):
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.spinners = {
            'dots': '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏',
            'line': '|/-\\',
            'pulse': '█▉▊▋▌▍▎▏▎▍▌▋▊▉',
            'points': '⣾⣽⣻⢿⡿⣟⣯⣷',
            'arc': '◜◠◝◞◡◟',
            'clock': '🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛'
        }

    def start(self, message: str, spinner_style: str = 'dots'):
        """Start loading animation with message"""
        spinner = Spinner(self.spinners[spinner_style], style=self.colors.scheme.primary)
        return Live(
            Panel(f"{spinner} {message}", border_style=self.colors.scheme.secondary),
            console=self.console,
            refresh_per_second=15
        )


class ProgressAnimation(Animation):
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style=self.colors.scheme.success),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        )
        self.tasks: Dict[str, TaskID] = {}

    def add_task(self, name: str, total: int) -> TaskID:
        """Add new progress task"""
        task_id = self.progress.add_task(name, total=total)
        self.tasks[name] = task_id
        return task_id

    def update(self, name: str, advance: int = 1):
        """Update task progress"""
        if name in self.tasks:
            self.progress.update(self.tasks[name], advance=advance)

    def start(self):
        """Start progress animation"""
        return self.progress


class ScanAnimation(Animation):
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.frames = [
            "🔍 Scanning",
            "🔎 Scanning.",
            "🔍 Scanning..",
            "🔎 Scanning..."
        ]
        self.current_frame = 0

    def _animate(self):
        """Animation loop"""
        while self.is_running:
            self.console.print(
                self.frames[self.current_frame],
                style=self.colors.scheme.primary,
                end="\r"
            )
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            time.sleep(0.2)

    def start(self):
        """Start scan animation"""
        self.is_running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop scan animation"""
        self.is_running = False
        if self._thread:
            self._thread.join()
        self.console.print(" " * 20, end="\r")  # Clear animation line


class PulseAnimation(Animation):
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.chars = "█▉▊▋▌▍▎▏"
        self.direction = 1
        self.position = 0

    def _animate(self):
        """Pulse animation loop"""
        while self.is_running:
            bar = ""
            for i in range(20):
                if i == self.position:
                    bar += self.chars[0]
                else:
                    bar += "░"
            self.console.print(bar, style=self.colors.scheme.primary, end="\r")

            self.position += self.direction
            if self.position in (0, 19):
                self.direction *= -1
            time.sleep(0.05)

    def start(self):
        """Start pulse animation"""
        self.is_running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop pulse animation"""
        self.is_running = False
        if self._thread:
            self._thread.join()
        self.console.print(" " * 20, end="\r")


class NetworkAnimation(Animation):
    def __init__(self, console: Optional[Console] = None):
        super().__init__(console)
        self.frames = [
            "⠋ Connecting",
            "⠙ Connecting",
            "⠹ Connected!",
            "⠸ Sending...",
            "⠼ Receiving...",
            "⠴ Processing",
            "⠦ Processing.",
            "⠧ Processing..",
            "⠇ Complete!",
            "⠏ Ready"
        ]
        self.current_frame = 0

    def _animate(self):
        """Network animation loop"""
        while self.is_running:
            self.console.print(
                self.frames[self.current_frame],
                style=self.colors.scheme.primary,
                end="\r"
            )
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            time.sleep(0.1)

    def start(self):
        """Start network animation"""
        self.is_running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop network animation"""
        self.is_running = False
        if self._thread:
            self._thread.join()
        self.console.print(" " * 30, end="\r")
