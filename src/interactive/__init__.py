from .keyboard import KeyboardHandler
from .commands import CommandHandler, Command, CommandType
from .filters import Filter, FilterType, FilterOperator

__all__ = [
    'KeyboardHandler',
    'CommandHandler',
    'Command',
    'CommandType',
    'Filter',
    'FilterType',
    'FilterOperator'
]

# Interactive Configuration
COMMAND_PREFIX = '/'
HISTORY_SIZE = 1000
AUTO_COMPLETE = True
PROMPT_CHAR = '>'

# Command Registry
COMMANDS = {
    'scan': CommandType.SCAN,
    'report': CommandType.REPORT,
    'config': CommandType.CONFIG,
    'system': CommandType.SYSTEM
}

# Filter Registry
FILTERS = {
    'severity': FilterType.ENUM,
    'confidence': FilterType.ENUM,
    'type': FilterType.STRING,
    'date': FilterType.DATE,
    'score': FilterType.NUMERIC
}
