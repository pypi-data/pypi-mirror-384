"""
Logger utilities for Henotace AI Python SDK
"""

import logging
from typing import Any
from .types import Logger, LogLevel


class ConsoleLogger(Logger):
    """Default console logger implementation"""
    
    def __init__(self, level: int = LogLevel.INFO):
        self.level = level
        self.logger = logging.getLogger('henotace_ai')
        self.logger.setLevel(self._convert_level(level))
        
        # Create console handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[Henotace SDK] %(asctime)s [%(levelname)s] %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _convert_level(self, level: int) -> int:
        """Convert internal log level to Python logging level"""
        if level == LogLevel.DEBUG:
            return logging.DEBUG
        elif level == LogLevel.INFO:
            return logging.INFO
        elif level == LogLevel.WARN:
            return logging.WARNING
        elif level == LogLevel.ERROR:
            return logging.ERROR
        else:
            return logging.CRITICAL
    
    def _should_log(self, level: int) -> bool:
        """Check if message should be logged at given level"""
        return level >= self.level
    
    def _format_message(self, level: str, message: str, *args, **kwargs) -> str:
        """Format log message with arguments"""
        if args or kwargs:
            # Convert args and kwargs to string representation
            formatted_args = []
            for arg in args:
                if isinstance(arg, dict):
                    formatted_args.append(str(arg))
                else:
                    formatted_args.append(str(arg))
            
            for key, value in kwargs.items():
                formatted_args.append(f"{key}={value}")
            
            return f"{message} {' '.join(formatted_args)}"
        return message
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        if self._should_log(LogLevel.DEBUG):
            formatted = self._format_message('DEBUG', message, *args, **kwargs)
            self.logger.debug(formatted)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        if self._should_log(LogLevel.INFO):
            formatted = self._format_message('INFO', message, *args, **kwargs)
            self.logger.info(formatted)
    
    def warn(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        if self._should_log(LogLevel.WARN):
            formatted = self._format_message('WARN', message, *args, **kwargs)
            self.logger.warning(formatted)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        if self._should_log(LogLevel.ERROR):
            formatted = self._format_message('ERROR', message, *args, **kwargs)
            self.logger.error(formatted)


class NoOpLogger(Logger):
    """No-op logger for when logging is disabled"""
    
    def debug(self, message: str, *args, **kwargs) -> None:
        pass
    
    def info(self, message: str, *args, **kwargs) -> None:
        pass
    
    def warn(self, message: str, *args, **kwargs) -> None:
        pass
    
    def error(self, message: str, *args, **kwargs) -> None:
        pass


def create_logger(level: int = LogLevel.INFO, enabled: bool = True) -> Logger:
    """Logger factory function"""
    if not enabled or level == LogLevel.NONE:
        return NoOpLogger()
    return ConsoleLogger(level)
