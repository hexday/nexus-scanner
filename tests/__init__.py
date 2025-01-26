import pytest
from pathlib import Path
import sys

# Add src directory to Python path for test imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Test Configuration
TEST_CONFIG = {
    'test_data_dir': 'tests/data',
    'mock_responses_dir': 'tests/mocks',
    'temp_dir': 'tests/temp',
    'coverage_threshold': 80
}

# Test Fixtures Registry
FIXTURES = {
    'scanner': 'tests.fixtures.scanner',
    'reporter': 'tests.fixtures.reporter',
    'ui': 'tests.fixtures.ui',
    'monitoring': 'tests.fixtures.monitoring'
}

# Test Categories
TEST_CATEGORIES = [
    'unit',
    'integration',
    'performance',
    'security'
]
