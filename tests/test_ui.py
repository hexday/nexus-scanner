import pytest
from unittest.mock import Mock, patch
from src.ui.menu import Menu, MenuItem, MenuType
from src.ui.display import Display
from src.ui.input_handler import InputHandler
from rich.console import Console
from rich.table import Table


class TestUI:
    @pytest.fixture
    def menu(self):
        return Menu("Test Menu", MenuType.MAIN)

    @pytest.fixture
    def display(self):
        return Display(Console())

    @pytest.fixture
    def input_handler(self):
        return InputHandler()

    def test_menu_creation(self, menu):
        menu.add_item("1", "Test Item", lambda: None, "Test Description")
        assert len(menu.items) == 1
        assert "1" in menu.items
        assert menu.items["1"].title == "Test Item"

    def test_submenu_navigation(self, menu):
        submenu = Menu("Sub Menu", MenuType.SCAN)
        menu.add_item("1", "Sub Menu", lambda: None, "Test Submenu", submenu)
        assert menu.items["1"].submenu is submenu
        assert submenu.parent is menu

    @patch('rich.console.Console.print')
    def test_menu_display(self, mock_print, menu, display):
        menu.add_item("1", "Test Item", lambda: None, "Test Description")
        menu.display()
        mock_print.assert_called()

    def test_input_handling(self, menu, input_handler):
        callback = Mock()
        menu.add_item("1", "Test Item", callback, "Test Description")

        with patch('builtins.input', return_value="1"):
            menu.handle_input("1")
            callback.assert_called_once()

    @pytest.mark.parametrize("key,expected", [
        ("q", False),  # Exit
        ("b", True),  # Back
        ("1", True),  # Valid item
        ("x", True)  # Invalid item
    ])
    def test_menu_navigation(self, menu, key, expected):
        menu.add_item("1", "Test Item", lambda: None, "Test Description")
        assert menu.handle_input(key) == expected

    def test_display_formatting(self, display):
        table = Table(title="Test Table")
        table.add_column("Test")
        table.add_row("Data")

        with patch('rich.console.Console.print') as mock_print:
            display.show_table(table)
            mock_print.assert_called_once()

    def test_menu_item_enable_disable(self, menu):
        menu.add_item("1", "Test Item", lambda: None, "Test Description")
        menu.items["1"].enabled = False
        assert not menu.items["1"].enabled
        menu.items["1"].enabled = True
        assert menu.items["1"].enabled

    def test_display_progress(self, display):
        with patch('rich.progress.Progress.add_task') as mock_task:
            display.show_progress("Test Progress")
            mock_task.assert_called_once()

    def test_input_validation(self, input_handler):
        with patch('builtins.input', return_value="test"):
            result = input_handler.get_input("Prompt", validator=lambda x: len(x) > 0)
            assert result == "test"

    def test_menu_type_grouping(self, menu):
        menu.add_item("1", "Scan Item", lambda: None, "Scan", type=MenuType.SCAN)
        menu.add_item("2", "Config Item", lambda: None, "Config", type=MenuType.CONFIG)
        scan_items = [item for item in menu.items.values() if item.type == MenuType.SCAN]
        assert len(scan_items) == 1

    def test_display_error_handling(self, display):
        with patch('rich.console.Console.print') as mock_print:
            display.show_error("Test Error")
            mock_print.assert_called_once()

    def test_input_timeout(self, input_handler):
        with patch('builtins.input', side_effect=TimeoutError):
            with pytest.raises(TimeoutError):
                input_handler.get_input("Prompt", timeout=1)

    def test_menu_callback_error(self, menu):
        def error_callback():
            raise Exception("Test Error")

        menu.add_item("1", "Error Item", error_callback, "Error Test")
        with pytest.raises(Exception):
            menu.handle_input("1")

    def test_display_theme(self, display):
        with patch('rich.console.Console.print') as mock_print:
            display.set_theme("dark")
            display.show_message("Test Message")
            mock_print.assert_called_once()
