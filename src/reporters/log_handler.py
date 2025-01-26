import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Dict
import json
from datetime import datetime
import sys
import threading
from queue import Queue
import traceback

class NexusLogHandler:
    def __init__(self,
                 log_dir: Path,
                 log_level: int = logging.INFO,
                 max_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 format_json: bool = True):
        self.log_dir = log_dir
        self.log_level = log_level
        self.max_size = max_size
        self.backup_count = backup_count
        self.format_json = format_json
        self.queue = Queue()
        self.logger = self._setup_logger()
        self._start_queue_handler()

    def _setup_logger(self) -> logging.Logger:
        """Configure and setup the logger"""
        logger = logging.getLogger('nexus')
        logger.setLevel(self.log_level)

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Add handlers
        handlers = [
            self._create_file_handler(),
            self._create_rotating_handler(),
            self._create_console_handler()
        ]

        for handler in handlers:
            logger.addHandler(handler)

        return logger

    def _create_file_handler(self) -> logging.FileHandler:
        """Create main log file handler"""
        log_file = self.log_dir / 'nexus.log'
        handler = logging.FileHandler(log_file)
        handler.setLevel(self.log_level)
        handler.setFormatter(self._get_formatter())
        return handler

    def _create_rotating_handler(self) -> RotatingFileHandler:
        """Create rotating file handler for size-based rotation"""
        log_file = self.log_dir / 'nexus_rotating.log'
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count
        )
        handler.setLevel(self.log_level)
        handler.setFormatter(self._get_formatter())
        return handler

    def _create_console_handler(self) -> logging.StreamHandler:
        """Create console output handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)
        handler.setFormatter(self._get_formatter())
        return handler

    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate log formatter"""
        if self.format_json:
            return JsonFormatter()
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _start_queue_handler(self):
        """Start asynchronous queue handler thread"""
        def queue_handler():
            while True:
                record = self.queue.get()
                if record is None:
                    break
                self._handle_log_record(record)

        thread = threading.Thread(target=queue_handler)
        thread.daemon = True
        thread.start()

    def _handle_log_record(self, record: Dict):
        """Process a log record from the queue"""
        if self.format_json:
            self.logger.log(
                record['level'],
                json.dumps(record, default=str)
            )
        else:
            self.logger.log(
                record['level'],
                record['message']
            )

    def log(self, level: int, message: str, extra: Optional[Dict] = None):
        """Add a log record to the queue"""
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'extra': extra or {},
            'thread': threading.current_thread().name
        }
        self.queue.put(record)

    def error(self, message: str, exc_info: bool = True):
        """Log an error message"""
        extra = {}
        if exc_info:
            extra['traceback'] = traceback.format_exc()
        self.log(logging.ERROR, message, extra)

    def warning(self, message: str):
        """Log a warning message"""
        self.log(logging.WARNING, message)

    def info(self, message: str):
        """Log an info message"""
        self.log(logging.INFO, message)

    def debug(self, message: str):
        """Log a debug message"""
        self.log(logging.DEBUG, message)

    def critical(self, message: str):
        """Log a critical message"""
        self.log(logging.CRITICAL, message)

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for log records"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno,
            'thread': record.threadName
        }

        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra

        if record.exc_info:
            log_data['exception'] = {
                'type': str(record.exc_info[0]),
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)

    def formatException(self, ei) -> str:
        """Format exception information as JSON"""
        return json.dumps(traceback.format_exception(*ei))
