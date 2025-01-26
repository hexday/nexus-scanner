from typing import List, Dict, Union, Optional
from rich.console import Console
from rich.table import Table
import math
import statistics


class ASCIIGraph:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.graph_width = 60
        self.graph_height = 15
        self.symbols = {
            'bar': '█',
            'half': '▄',
            'dot': '•',
            'line': '─',
            'corner': '└',
            'vertical': '│'
        }

    def bar_graph(self, data: Dict[str, int], title: str = "Bar Graph"):
        """Generate ASCII bar graph"""
        if not data:
            return

        max_value = max(data.values())
        max_label_length = max(len(str(k)) for k in data.keys())
        scale_factor = self.graph_width / max_value if max_value > 0 else 0

        table = Table(title=title, show_header=False, box=None)
        table.add_column("Label", style="cyan", width=max_label_length + 2)
        table.add_column("Bar", style="green")
        table.add_column("Value", style="yellow", width=10)

        for key, value in data.items():
            bar_length = int(value * scale_factor)
            bar = self.symbols['bar'] * bar_length
            table.add_row(str(key), bar, str(value))

        self.console.print(table)

    def line_graph(self, data: List[float], title: str = "Line Graph"):
        """Generate ASCII line graph"""
        if not data:
            return

        min_value = min(data)
        max_value = max(data)
        value_range = max_value - min_value

        normalized = [
            int((x - min_value) * (self.graph_height - 1) / value_range)
            if value_range > 0 else 0
            for x in data
        ]

        graph = [[' ' for _ in range(len(data))] for _ in range(self.graph_height)]

        for x in range(len(data) - 1):
            y1, y2 = normalized[x], normalized[x + 1]
            self._draw_line(graph, x, y1, x + 1, y2)

        self._print_graph(graph, title, min_value, max_value)

    def histogram(self, data: List[float], bins: int = 10, title: str = "Histogram"):
        """Generate ASCII histogram"""
        if not data:
            return

        min_val, max_val = min(data), max(data)
        bin_width = (max_val - min_val) / bins
        histogram = [0] * bins

        for value in data:
            bin_index = min(
                int((value - min_val) / bin_width),
                bins - 1
            )
            histogram[bin_index] += 1

        max_count = max(histogram)
        scale_factor = self.graph_width / max_count if max_count > 0 else 0

        table = Table(title=title, show_header=False, box=None)
        table.add_column("Range", style="cyan", width=20)
        table.add_column("Count", style="green")
        table.add_column("Value", style="yellow", width=10)

        for i in range(bins):
            start = min_val + i * bin_width
            end = start + bin_width
            bar_length = int(histogram[i] * scale_factor)
            bar = self.symbols['bar'] * bar_length
            table.add_row(
                f"{start:.2f} - {end:.2f}",
                bar,
                str(histogram[i])
            )

        self.console.print(table)

    def scatter_plot(self, x_data: List[float], y_data: List[float], title: str = "Scatter Plot"):
        """Generate ASCII scatter plot"""
        if not x_data or not y_data or len(x_data) != len(y_data):
            return

        x_min, x_max = min(x_data), max(x_data)
        y_min, y_max = min(y_data), max(y_data)

        plot = [[' ' for _ in range(self.graph_width)] for _ in range(self.graph_height)]

        for x, y in zip(x_data, y_data):
            plot_x = int((x - x_min) * (self.graph_width - 1) / (x_max - x_min)) if x_max > x_min else 0
            plot_y = int((y - y_min) * (self.graph_height - 1) / (y_max - y_min)) if y_max > y_min else 0
            plot[self.graph_height - 1 - plot_y][plot_x] = self.symbols['dot']

        self._print_graph(plot, title, y_min, y_max)

    def _draw_line(self, graph: List[List[str]], x1: int, y1: int, x2: int, y2: int):
        """Draw line between two points"""
        if x2 - x1 == 0:
            return

        slope = (y2 - y1) / (x2 - x1)
        for x in range(x1, x2 + 1):
            y = int(y1 + slope * (x - x1))
            if 0 <= y < self.graph_height:
                graph[self.graph_height - 1 - y][x] = self.symbols['dot']

    def _print_graph(self, graph: List[List[str]], title: str, min_val: float, max_val: float):
        """Print formatted graph"""
        self.console.print(f"\n[bold]{title}[/bold]")

        # Print y-axis labels and graph
        for i, row in enumerate(graph):
            value = max_val - (i * (max_val - min_val) / (self.graph_height - 1))
            self.console.print(f"{value:6.2f} {self.symbols['vertical']} {''.join(row)}")

        # Print x-axis
        self.console.print(f"       {self.symbols['corner']}{self.symbols['line'] * self.graph_width}")

    def box_plot(self, data: List[float], title: str = "Box Plot"):
        """Generate ASCII box plot"""
        if not data:
            return

        # Calculate statistics
        sorted_data = sorted(data)
        q1 = statistics.quantiles(sorted_data, n=4)[0]
        q2 = statistics.median(sorted_data)
        q3 = statistics.quantiles(sorted_data, n=4)[2]
        iqr = q3 - q1
        whisker_low = max(min(sorted_data), q1 - 1.5 * iqr)
        whisker_high = min(max(sorted_data), q3 + 1.5 * iqr)

        # Generate box plot
        box = f"{whisker_low:.2f} {self.symbols['line']}{'─' * 10}│{q1:.2f}│{'█' * 10}│{q2:.2f}│{'█' * 10}│{q3:.2f}│{'─' * 10}{self.symbols['line']} {whisker_high:.2f}"

        self.console.print(f"\n[bold]{title}[/bold]")
        self.console.print(box)
