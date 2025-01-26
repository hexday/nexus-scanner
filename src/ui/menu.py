from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import curses
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class MenuType(Enum):
    MAIN = "main"
    SCAN = "scan"
    REPORT = "report"
    CONFIG = "config"
    HELP = "help"


@dataclass
class MenuItem:
    key: str
    title: str
    callback: Callable
    description: str
    type: MenuType
    enabled: bool = True
    submenu: Optional['Menu'] = None


class Menu:
    def __init__(self, title: str, type: MenuType):
        self.logger = logging.getLogger("nexus.menu")
        self.title = title
        self.type = type
        self.items: Dict[str, MenuItem] = {}
        self.console = Console()
        self.current_menu: Optional[Menu] = None
        self.parent: Optional[Menu] = None

    def add_item(self,
                 key: str,
                 title: str,
                 callback: Callable,
                 description: str,
                 submenu: Optional['Menu'] = None):
        """Add menu item"""
        item = MenuItem(
            key=key,
            title=title,
            callback=callback,
            description=description,
            type=self.type,
            submenu=submenu
        )

        if submenu:
            submenu.parent = self

        self.items[key] = item

    def remove_item(self, key: str):
        """Remove menu item"""
        if key in self.items:
            del self.items[key]

    def display(self):
        """Display menu"""
        self.current_menu = self
        self._render_menu()

    def _render_menu(self):
        """Render current menu"""
        table = Table(title=self.title)
        table.add_column("Key", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Description", style="yellow")

        for item in self.items.values():
            if item.enabled:
                table.add_row(
                    item.key,
                    item.title,
                    item.description
                )

        self.console.clear()
        self.console.print(table)
        self._show_navigation_help()

    def _show_navigation_help(self):
        """Show navigation help"""
        help_text = "\nNavigation: [b]Enter key to select[/b] | [b]'b' for back[/b] | [b]'q' to quit[/b]"
        self.console.print(Panel(help_text))

    def handle_input(self, key: str) -> bool:
        """Handle menu input"""
        if key == 'q':
            return False

        if key == 'b' and self.parent:
            self.parent.display()
            return True

        if key in self.items:
            item = self.items[key]
            if item.enabled:
                if item.submenu:
                    item.submenu.display()
                else:
                    self._execute_callback(item)

        return True

    def _execute_callback(self, item: MenuItem):
        """Execute menu item callback"""
        try:
            result = item.callback()
            if result:
                self.console.print(f"\nResult: {result}")
            self.console.input("\nPress Enter to continue...")
            self.display()
        except Exception as e:
            self.logger.error(f"Menu callback error: {str(e)}")
            self.console.print(f"[red]Error executing menu item: {str(e)}[/red]")


class MenuBuilder:
    def __init__(self):
        self.main_menu = Menu("Nexus Security Scanner", MenuType.MAIN)
        self._build_menus()

    def _build_menus(self):
        """Build menu structure"""
        # Scan Menu
        scan_menu = Menu("Scan Options", MenuType.SCAN)
        scan_menu.add_item("1", "Quick Scan", self._quick_scan, "Perform quick security scan")
        scan_menu.add_item("2", "Full Scan", self._full_scan, "Perform comprehensive scan")
        scan_menu.add_item("3", "Custom Scan", self._custom_scan, "Configure custom scan")

        # Report Menu
        report_menu = Menu("Report Options", MenuType.REPORT)
        report_menu.add_item("1", "Generate Report", self._generate_report, "Generate scan report")
        report_menu.add_item("2", "Export Data", self._export_data, "Export raw scan data")
        report_menu.add_item("3", "View History", self._view_history, "View scan history")

        # Config Menu
        config_menu = Menu("Configuration", MenuType.CONFIG)
        config_menu.add_item("1", "Settings", self._edit_settings, "Edit scanner settings")
        config_menu.add_item("2", "Profiles", self._manage_profiles, "Manage scan profiles")
        config_menu.add_item("3", "Updates", self._check_updates, "Check for updates")

        # Main Menu
        self.main_menu.add_item("1", "Scan", lambda: None, "Security scanning options", scan_menu)
        self.main_menu.add_item("2", "Report", lambda: None, "Reporting options", report_menu)
        self.main_menu.add_item("3", "Config", lambda: None, "Scanner configuration", config_menu)
        self.main_menu.add_item("4", "Help", self._show_help, "Show help")

    def _quick_scan(self): pass

    def _full_scan(self): pass

    def _custom_scan(self): pass

    def _generate_report(self): pass

    def _export_data(self): pass

    def _view_history(self): pass

    def _edit_settings(self): pass

    def _manage_profiles(self): pass

    def _check_updates(self): pass

    def _show_help(self): pass

    def get_main_menu(self) -> Menu:
        """Get main menu instance"""
        return self.main_menu
