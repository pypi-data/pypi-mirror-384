"""
Henotace AI Python SDK
Official Python SDK for the Henotace AI API
"""

from .index import HenotaceAI
from .tutor import Tutor, create_tutor
from .types import (
    SessionStudent, SessionTutor, SessionChat, SessionSubject,
    HenotaceError, HenotaceAPIError, HenotaceNetworkError,
    StorageConnector, Logger, LogLevel
)
from .connectors import InMemoryConnector
from .logger import ConsoleLogger, NoOpLogger, create_logger

# Export main classes and functions
__all__ = [
    'HenotaceAI', 'Tutor', 'create_tutor',
    'StorageConnector', 'InMemoryConnector',
    'SessionStudent', 'SessionTutor', 'SessionChat', 'SessionSubject',
    'HenotaceError', 'HenotaceAPIError', 'HenotaceNetworkError',
    'Logger', 'LogLevel', 'ConsoleLogger', 'NoOpLogger', 'create_logger'
]

# Version info
__version__ = '1.1.1'
__author__ = 'Henotace AI Team'
__email__ = 'support@henotace.ai'
