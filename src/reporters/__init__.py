from .cli_reporter import CLIReporter
from .json_reporter import JSONReporter
from .tree_view import TreeViewReporter
from .log_handler import NexusLogHandler

__all__ = [
    'CLIReporter',
    'JSONReporter',
    'TreeViewReporter',
    'NexusLogHandler'
]

# Reporter Configuration
OUTPUT_DIR = 'reports'
LOG_LEVEL = 'INFO'
REPORT_FORMATS = ['cli', 'json', 'tree', 'log']

# Reporter Registry
REPORTERS = {
    'cli': CLIReporter,
    'json': JSONReporter,
    'tree': TreeViewReporter,
    'log': NexusLogHandler
}

# Report Templates
TEMPLATES = {
    'scan': 'templates/scan_report.txt',
    'vuln': 'templates/vulnerability_report.txt',
    'summary': 'templates/summary_report.txt'
}
