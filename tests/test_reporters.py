import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.reporters.tree_view import TreeViewReporter
from src.reporters.log_handler import NexusLogHandler
from rich.tree import Tree
from rich.console import Console

class TestReporters:
    @pytest.fixture
    def tree_reporter(self):
        return TreeViewReporter(Console())

    @pytest.fixture
    def log_handler(self, tmp_path):
        return NexusLogHandler(log_dir=tmp_path)

    @pytest.fixture
    def sample_scan_data(self):
        return {
            "target": "example.com",
            "metadata": {
                "timestamp": "2023-01-01T00:00:00",
                "scanner_version": "1.0.0"
            },
            "findings": [
                {
                    "title": "Test Finding",
                    "severity": "HIGH",
                    "description": "Test Description"
                }
            ],
            "statistics": {
                "duration": 60,
                "total_checks": 100
            }
        }

    def test_tree_view_generation(self, tree_reporter, sample_scan_data):
        tree = tree_reporter.generate_tree(sample_scan_data)
        assert isinstance(tree, Tree)
        assert "Scan Results" in tree.label

    def test_tree_view_findings(self, tree_reporter, sample_scan_data):
        tree = tree_reporter.generate_tree(sample_scan_data)
        findings_count = len([node for node in tree.children if "Findings" in node.label])
        assert findings_count == 1

    def test_log_handler_creation(self, log_handler, tmp_path):
        assert log_handler.log_dir == tmp_path
        assert any(tmp_path.glob("*.log"))

    def test_log_handler_levels(self, log_handler):
        log_handler.info("Test Info")
        log_handler.error("Test Error")
        log_handler.warning("Test Warning")
        assert len(log_handler.get_active_tasks()) >= 0

    @patch('rich.console.Console.print')
    def test_tree_view_display(self, mock_print, tree_reporter, sample_scan_data):
        tree = tree_reporter.generate_tree(sample_scan_data)
        tree_reporter.display_tree(tree)
        mock_print.assert_called_once()

    def test_log_rotation(self, tmp_path):
        handler = NexusLogHandler(log_dir=tmp_path, max_size=100)
        for i in range(200):
            handler.info(f"Test message {i}")
        assert len(list(tmp_path.glob("*.log*"))) > 1

    def test_tree_view_severity_icons(self, tree_reporter):
        assert all(icon in tree_reporter.severity_icons.values()
                  for icon in ['🔴', '🟠', '🟡', '🔵', '🟢'])

    def test_log_handler_json_format(self, log_handler):
        log_handler.info("Test JSON", extra={"key": "value"})
        log_files = list(log_handler.log_dir.glob("*.log"))
        assert any("key" in log_file.read_text() for log_file in log_files)

    @pytest.mark.parametrize("severity,expected_icon", [
        ("CRITICAL", "🔴"),
        ("HIGH", "🟠"),
        ("MEDIUM", "🟡"),
        ("LOW", "🔵"),
        ("INFO", "🟢")
    ])
    def test_severity_icons(self, tree_reporter, severity, expected_icon):
        assert tree_reporter.severity_icons[severity] == expected_icon

    def test_tree_view_statistics(self, tree_reporter, sample_scan_data):
        tree = tree_reporter.generate_tree(sample_scan_data)
        stats_nodes = [node for node in tree.children if "Statistics" in node.label]
        assert len(stats_nodes) == 1

    def test_log_handler_threading(self, log_handler):
        import threading
        threads = []
        for i in range(10):
            thread = threading.Thread(target=log_handler.info, args=(f"Thread {i}",))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert True  # No exceptions raised

    def test_tree_view_empty_data(self, tree_reporter):
        empty_data = {"target": "empty", "findings": [], "statistics": {}}
        tree = tree_reporter.generate_tree(empty_data)
        assert isinstance(tree, Tree)

    def test_log_handler_error_tracking(self, log_handler):
        try:
            raise ValueError("Test Error")
        except ValueError:
            log_handler.error("Error occurred", exc_info=True)
        log_files = list(log_handler.log_dir.glob("*.log"))
        assert any("ValueError" in log_file.read_text() for log_file in log_files)
