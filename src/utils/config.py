from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Any
import yaml
import os
from pathlib import Path
import json


@dataclass
class ScanConfig:
    threads: int
    timeout: int
    max_depth: int
    max_urls: int
    user_agent: str
    verify_ssl: bool
    follow_robots: bool


@dataclass
class UIConfig:
    theme: str
    animation_speed: float
    colors: Dict[str, str]
    show_progress: bool


@dataclass
class OutputConfig:
    format: str
    path: Optional[Path]
    verbose: bool


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.scan: ScanConfig = self._create_default_scan_config()
        self.ui: UIConfig = self._create_default_ui_config()
        self.output: OutputConfig = self._create_default_output_config()

        self._load_config()

    def _get_default_config_path(self) -> str:
        """Get default configuration path"""
        return os.path.join(
            os.path.expanduser("~"),
            ".config",
            "nexus",
            "config.yaml"
        )

    def _create_default_scan_config(self) -> ScanConfig:
        """Create default scanning configuration"""
        return ScanConfig(
            threads=10,
            timeout=30,
            max_depth=3,
            max_urls=1000,
            user_agent="Nexus-Scanner/1.0",
            verify_ssl=True,
            follow_robots=True
        )

    def _create_default_ui_config(self) -> UIConfig:
        """Create default UI configuration"""
        return UIConfig(
            theme="dark",
            animation_speed=1.0,
            colors={
                "primary": "cyan",
                "secondary": "green",
                "error": "red",
                "warning": "yellow",
                "info": "blue"
            },
            show_progress=True
        )

    def _create_default_output_config(self) -> OutputConfig:
        """Create default output configuration"""
        return OutputConfig(
            format="cli",
            path=None,
            verbose=False
        )

    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                self._update_config(config_data)

    def _update_config(self, config_data: Dict[str, Any]):
        """Update configuration with loaded data"""
        if 'scan' in config_data:
            for key, value in config_data['scan'].items():
                if hasattr(self.scan, key):
                    setattr(self.scan, key, value)

        if 'ui' in config_data:
            for key, value in config_data['ui'].items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)

        if 'output' in config_data:
            for key, value in config_data['output'].items():
                if hasattr(self.output, key):
                    if key == 'path' and value:
                        value = Path(value)
                    setattr(self.output, key, value)

    def save(self):
        """Save current configuration to file"""
        config_dir = os.path.dirname(self.config_path)
        os.makedirs(config_dir, exist_ok=True)

        config_data = {
            'scan': {
                'threads': self.scan.threads,
                'timeout': self.scan.timeout,
                'max_depth': self.scan.max_depth,
                'max_urls': self.scan.max_urls,
                'user_agent': self.scan.user_agent,
                'verify_ssl': self.scan.verify_ssl,
                'follow_robots': self.scan.follow_robots
            },
            'ui': {
                'theme': self.ui.theme,
                'animation_speed': self.ui.animation_speed,
                'colors': self.ui.colors,
                'show_progress': self.ui.show_progress
            },
            'output': {
                'format': self.output.format,
                'path': str(self.output.path) if self.output.path else None,
                'verbose': self.output.verbose
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'scan': {
                'threads': self.scan.threads,
                'timeout': self.scan.timeout,
                'max_depth': self.scan.max_depth,
                'max_urls': self.scan.max_urls,
                'user_agent': self.scan.user_agent,
                'verify_ssl': self.scan.verify_ssl,
                'follow_robots': self.scan.follow_robots
            },
            'ui': {
                'theme': self.ui.theme,
                'animation_speed': self.ui.animation_speed,
                'colors': self.ui.colors,
                'show_progress': self.ui.show_progress
            },
            'output': {
                'format': self.output.format,
                'path': str(self.output.path) if self.output.path else None,
                'verbose': self.output.verbose
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Config:
        """Create configuration from dictionary"""
        config = cls()
        config._update_config(data)
        return config

    def validate(self) -> bool:
        """Validate configuration values"""
        try:
            assert 1 <= self.scan.threads <= 100
            assert 1 <= self.scan.timeout <= 300
            assert 1 <= self.scan.max_depth <= 10
            assert 1 <= self.scan.max_urls <= 10000
            assert self.ui.animation_speed > 0
            assert self.ui.theme in ['dark', 'light']
            assert self.output.format in ['cli', 'json', 'html']
            return True
        except AssertionError:
            return False

    def get_theme_colors(self) -> Dict[str, str]:
        """Get theme-specific colors"""
        themes = {
            'dark': {
                'background': '#1a1a1a',
                'text': '#ffffff',
                **self.ui.colors
            },
            'light': {
                'background': '#ffffff',
                'text': '#000000',
                **self.ui.colors
            }
        }
        return themes.get(self.ui.theme, themes['dark'])
