from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from rich.progress import (
    Progress, TextColumn, BarColumn, TaskID,
    SpinnerColumn, TimeRemainingColumn
)
from rich.live import Live
from rich.table import Table
from rich.text import Text
import time

from .colors import NexusColors
from ..utils.config import Config


@dataclass
class TaskStats:
    started_at: float
    completed: int
    total: int
    speed: float
    eta: float


class NexusProgress:
    def __init__(self, colors: NexusColors, config: Config):
        self.colors = colors
        self.config = config
        self.tasks: Dict[str, TaskID] = {}
        self.stats: Dict[str, TaskStats] = {}

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(
                complete_style=self.colors.get_color("primary"),
                finished_style=self.colors.get_color("success")
            ),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            TextColumn("{task.fields[speed]}/s")
        )

    def add_task(self, name: str, total: int, description: str = None) -> TaskID:
        """Add a new progress tracking task"""
        task_id = self.progress.add_task(
            description or name,
            total=total,
            speed="0.0"
        )

        self.tasks[name] = task_id
        self.stats[name] = TaskStats(
            started_at=time.time(),
            completed=0,
            total=total,
            speed=0.0,
            eta=0.0
        )

        return task_id

    def update(self, name: str, advance: int = 1, **fields):
        """Update task progress"""
        if name not in self.tasks:
            return

        task_id = self.tasks[name]
        stats = self.stats[name]

        # Update statistics
        stats.completed += advance
        elapsed = time.time() - stats.started_at
        stats.speed = stats.completed / elapsed if elapsed > 0 else 0
        stats.eta = (stats.total - stats.completed) / stats.speed if stats.speed > 0 else 0

        # Update progress
        self.progress.update(
            task_id,
            advance=advance,
            speed=f"{stats.speed:.1f}",
            **fields
        )

    def get_progress_table(self) -> Table:
        """Generate a table showing all task progress"""
        table = Table(
            title="Scan Progress",
            title_style=self.colors.get_color("primary")
        )

        table.add_column("Task")
        table.add_column("Progress")
        table.add_column("Speed")
        table.add_column("ETA")

        for name, stats in self.stats.items():
            progress_percentage = (stats.completed / stats.total) * 100 if stats.total > 0 else 0
            table.add_row(
                name,
                f"{progress_percentage:.1f}%",
                f"{stats.speed:.1f}/s",
                f"{stats.eta:.1f}s"
            )

        return table

    def create_subtask_progress(self, parent_task: str, subtasks: List[str]):
        """Create nested progress tracking for subtasks"""

        class SubtaskProgress:
            def __init__(self, parent: NexusProgress, parent_name: str, subtask_names: List[str]):
                self.parent = parent
                self.parent_name = parent_name
                self.subtask_progress = Progress(
                    TextColumn("[dim]{task.description}"),
                    BarColumn(),
                    TextColumn("{task.completed}/{task.total}")
                )
                self.subtasks = {
                    name: self.subtask_progress.add_task(name, total=100)
                    for name in subtask_names
                }

            def update_subtask(self, name: str, advance: int = 1):
                if name in self.subtasks:
                    self.subtask_progress.update(self.subtasks[name], advance=advance)
                    # Update parent task proportionally
                    total_progress = sum(
                        self.subtask_progress.tasks[task_id].completed
                        for task_id in self.subtasks.values()
                    )
                    parent_advance = total_progress / len(self.subtasks)
                    self.parent.update(self.parent_name, advance=parent_advance)

        return SubtaskProgress(self, parent_task, subtasks)

    def create_multi_progress(self):
        """Create multiple progress bars that can be updated independently"""
        return MultiProgress(self)

    def get_stats(self, name: str) -> Optional[TaskStats]:
        """Get statistics for a specific task"""
        return self.stats.get(name)

    def format_speed(self, speed: float) -> str:
        """Format speed with appropriate units"""
        if speed >= 1000:
            return f"{speed / 1000:.1f}k/s"
        return f"{speed:.1f}/s"

    def get_overall_progress(self) -> float:
        """Calculate overall progress across all tasks"""
        if not self.stats:
            return 0.0

        total_progress = sum(
            stats.completed / stats.total if stats.total > 0 else 0
            for stats in self.stats.values()
        )
        return (total_progress / len(self.stats)) * 100


class MultiProgress:
    def __init__(self, parent: NexusProgress):
        self.parent = parent
        self.progress_bars: Dict[str, Progress] = {}

    def add_progress(self, name: str, total: int) -> Progress:
        """Add a new independent progress bar"""
        progress = Progress(
            TextColumn(f"[blue]{name}"),
            BarColumn(
                complete_style=self.parent.colors.get_color("primary"),
                finished_style=self.parent.colors.get_color("success")
            ),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("{task.fields[speed]}/s")
        )

        self.progress_bars[name] = progress
        return progress

    def start(self):
        """Start displaying all progress bars"""
        return Live(self._generate_table(), refresh_per_second=10)

    def _generate_table(self) -> Table:
        """Generate a table containing all progress bars"""
        table = Table(box=None)
        table.add_column("Progress")

        for progress in self.progress_bars.values():
            table.add_row(progress)

        return table
