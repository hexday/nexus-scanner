from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.style import Style
from rich.color import Color

@dataclass
class ColorScheme:
    primary: str
    secondary: str
    success: str
    warning: str
    error: str
    info: str
    background: str
    text: str
    accent: str
    muted: str

class NexusColors:
    def __init__(self, theme: str = "dark"):
        self.theme = theme
        self.scheme = self._get_color_scheme()
        self.styles = self._create_styles()

    def _get_color_scheme(self) -> ColorScheme:
        schemes = {
            "dark": ColorScheme(
                primary="cyan",
                secondary="blue",
                success="green",
                warning="yellow",
                error="red",
                info="white",
                background="#1a1a1a",
                text="#ffffff",
                accent="#ff00ff",
                muted="#666666"
            ),
            "light": ColorScheme(
                primary="blue",
                secondary="cyan",
                success="green",
                warning="yellow",
                error="red",
                info="black",
                background="#ffffff",
                text="#000000",
                accent="#800080",
                muted="#999999"
            ),
            "hacker": ColorScheme(
                primary="green",
                secondary="cyan",
                success="bright_green",
                warning="yellow",
                error="red",
                info="white",
                background="#000000",
                text="#00ff00",
                accent="#ff00ff",
                muted="#303030"
            )
        }
        return schemes.get(self.theme, schemes["dark"])

    def _create_styles(self) -> Dict[str, Style]:
        return {
            "header": Style(color=self.scheme.primary, bold=True),
            "subheader": Style(color=self.scheme.secondary, bold=True),
            "success": Style(color=self.scheme.success),
            "warning": Style(color=self.scheme.warning),
            "error": Style(color=self.scheme.error),
            "info": Style(color=self.scheme.info),
            "muted": Style(color=self.scheme.muted),
            "accent": Style(color=self.scheme.accent),
            "url": Style(color=self.scheme.primary, underline=True),
            "code": Style(bgcolor="#202020", color=self.scheme.text),
        }

    def get_status_color(self, status_code: int) -> str:
        """Get color based on HTTP status code"""
        if status_code < 300:
            return self.scheme.success
        elif status_code < 400:
            return self.scheme.info
        elif status_code < 500:
            return self.scheme.warning
        return self.scheme.error

    def get_severity_color(self, severity: str) -> str:
        """Get color based on severity level"""
        colors = {
            "CRITICAL": "red1",
            "HIGH": "red3",
            "MEDIUM": "yellow",
            "LOW": "blue",
            "INFO": "green"
        }
        return colors.get(severity.upper(), self.scheme.info)

    def get_chart_colors(self) -> List[str]:
        """Get colors for charts and graphs"""
        return [
            self.scheme.primary,
            self.scheme.success,
            self.scheme.warning,
            self.scheme.secondary,
            self.scheme.accent,
            self.scheme.error
        ]

    def get_progress_colors(self) -> Dict[str, str]:
        """Get colors for progress bars"""
        return {
            "complete": self.scheme.success,
            "pending": self.scheme.primary,
            "error": self.scheme.error,
            "paused": self.scheme.warning
        }

    def get_diff_colors(self) -> Dict[str, str]:
        """Get colors for diff display"""
        return {
            "added": self.scheme.success,
            "removed": self.scheme.error,
            "modified": self.scheme.warning,
            "unchanged": self.scheme.muted
        }

    def get_table_colors(self) -> Dict[str, Style]:
        """Get colors for table elements"""
        return {
            "header": self.styles["header"],
            "row": Style(color=self.scheme.text),
            "alternate_row": Style(color=self.scheme.text, bgcolor="#202020"),
            "border": Style(color=self.scheme.muted)
        }

    def get_network_colors(self) -> Dict[str, str]:
        """Get colors for network visualization"""
        return {
            "node": self.scheme.primary,
            "edge": self.scheme.secondary,
            "highlight": self.scheme.accent,
            "background": self.scheme.background
        }

    def get_syntax_colors(self) -> Dict[str, str]:
        """Get colors for syntax highlighting"""
        return {
            "keyword": self.scheme.primary,
            "string": self.scheme.success,
            "number": self.scheme.warning,
            "comment": self.scheme.muted,
            "function": self.scheme.secondary,
            "class": self.scheme.accent
        }

    def get_alert_style(self, level: str) -> Style:
        """Get style for alert messages"""
        styles = {
            "critical": Style(color="red", bold=True, blink=True),
            "error": Style(color=self.scheme.error, bold=True),
            "warning": Style(color=self.scheme.warning),
            "info": Style(color=self.scheme.info),
            "success": Style(color=self.scheme.success)
        }
        return styles.get(level.lower(), styles["info"])
