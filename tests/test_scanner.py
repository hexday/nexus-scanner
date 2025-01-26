import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.core.scanner import Scanner
from src.models.scan_result import ScanResult
from src.models.vulnerability import Vulnerability


class TestScanner:
    @pytest.fixture
    def scanner(self):
        return Scanner(
            config_path=Path("config/scanner.yml"),
            output_dir=Path("output")
        )

    @pytest.fixture
    def mock_target(self):
        return {
            "host": "example.com",
            "port": 443,
            "protocol": "https"
        }

    def test_scanner_initialization(self, scanner):
        assert scanner.config_path.exists()
        assert scanner.output_dir.exists()
        assert scanner.is_ready()

    def test_scan_target(self, scanner, mock_target):
        result = scanner.scan_target(mock_target)
        assert isinstance(result, ScanResult)
        assert result.target == mock_target
        assert result.start_time is not None
        assert result.end_time is not None

    @patch('src.scanner.Scanner._perform_vulnerability_scan')
    def test_vulnerability_detection(self, mock_scan, scanner, mock_target):
        mock_vuln = Vulnerability(
            id="CVE-2023-1234",
            severity="HIGH",
            description="Test vulnerability"
        )
        mock_scan.return_value = [mock_vuln]

        result = scanner.scan_target(mock_target)
        assert len(result.vulnerabilities) == 1
        assert result.vulnerabilities[0].id == "CVE-2023-1234"

    def test_scan_with_custom_rules(self, scanner, mock_target):
        custom_rules = [
            {"id": "CUSTOM-001", "check": "port_scan"},
            {"id": "CUSTOM-002", "check": "ssl_verify"}
        ]
        result = scanner.scan_target(mock_target, rules=custom_rules)
        assert len(result.applied_rules) == 2

    def test_concurrent_scans(self, scanner):
        targets = [
            {"host": "example1.com", "port": 443},
            {"host": "example2.com", "port": 443},
            {"host": "example3.com", "port": 443}
        ]
        results = scanner.scan_multiple(targets, max_workers=3)
        assert len(results) == 3
        assert all(isinstance(r, ScanResult) for r in results)

    def test_scan_interruption(self, scanner, mock_target):
        with pytest.raises(KeyboardInterrupt):
            with patch('src.scanner.Scanner._perform_scan', side_effect=KeyboardInterrupt):
                scanner.scan_target(mock_target)

    def test_scan_progress_tracking(self, scanner, mock_target):
        progress_callback = Mock()
        scanner.scan_target(mock_target, progress_callback=progress_callback)
        assert progress_callback.call_count > 0

    def test_scan_result_export(self, scanner, mock_target, tmp_path):
        result = scanner.scan_target(mock_target)
        export_path = tmp_path / "scan_result.json"
        result.export(export_path)
        assert export_path.exists()
        assert export_path.stat().st_size > 0

    def test_scanner_cleanup(self, scanner):
        scanner.cleanup()
        assert not any(scanner.output_dir.glob("*.tmp"))

    @pytest.mark.parametrize("target,expected_error", [
        ({}, ValueError),
        ({"host": ""}, ValueError),
        ({"host": "example.com", "port": -1}, ValueError)
    ])
    def test_invalid_targets(self, scanner, target, expected_error):
        with pytest.raises(expected_error):
            scanner.scan_target(target)

    def test_scan_performance(self, scanner, mock_target):
        with patch('time.time', side_effect=[0, 10]):  # Simulate 10-second scan
            result = scanner.scan_target(mock_target)
            assert result.duration == 10
            assert result.performance_metrics["avg_response_time"] > 0

    def test_scan_retry_mechanism(self, scanner, mock_target):
        with patch('src.scanner.Scanner._perform_scan') as mock_scan:
            mock_scan.side_effect = [ConnectionError, ConnectionError, ScanResult()]
            result = scanner.scan_target(mock_target, retries=3)
            assert isinstance(result, ScanResult)
            assert mock_scan.call_count == 3
