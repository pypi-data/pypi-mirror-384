"""
Type definitions for Henotace AI Python SDK
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


@dataclass
class SessionSubject:
    """Subject information for tutoring sessions"""
    id: str
    name: str
    topic: str


@dataclass
class SessionChat:
    """Individual chat message in a session"""
    message: str
    is_reply: bool
    timestamp: Optional[int] = None


@dataclass
class SessionTutor:
    """Tutor information and chat history"""
    id: str
    name: str
    subject: SessionSubject
    chats: List[SessionChat] = None
    context: Optional[List[str]] = None
    persona: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.chats is None:
            self.chats = []
        if self.context is None:
            self.context = []


@dataclass
class SessionStudent:
    """Student information with associated tutors"""
    id: str
    name: Optional[str] = None
    tutors: List[SessionTutor] = None

    def __post_init__(self):
        if self.tutors is None:
            self.tutors = []


@dataclass
class ApiResponse:
    """Standard API response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: str = None


# Exception classes
class HenotaceError(Exception):
    """Base exception for Henotace API errors"""
    pass


class HenotaceAPIError(HenotaceError):
    """API-specific errors"""
    pass


class HenotaceNetworkError(HenotaceError):
    """Network-related errors"""
    pass


# Log levels
class LogLevel:
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    NONE = 4


# Logger interface
class Logger:
    """Logger interface for custom logging implementations"""
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        pass
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        pass
    
    def warn(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        pass
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        pass


# Storage connector interface
class StorageConnector:
    """Abstract base class for storage connectors"""
    
    def get_all(self) -> Dict[str, List[SessionStudent]]:
        """Get all stored data"""
        raise NotImplementedError
    
    def set_all(self, schema: Dict[str, List[SessionStudent]]) -> None:
        """Set all data"""
        raise NotImplementedError
    
    def list_students(self) -> List[SessionStudent]:
        """List all students"""
        raise NotImplementedError
    
    def upsert_student(self, student: SessionStudent) -> None:
        """Create or update a student"""
        raise NotImplementedError
    
    def delete_student(self, student_id: str) -> None:
        """Delete a student"""
        raise NotImplementedError
    
    def list_tutors(self, student_id: str) -> List[SessionTutor]:
        """List tutors for a student"""
        raise NotImplementedError
    
    def upsert_tutor(self, student_id: str, tutor: SessionTutor) -> None:
        """Create or update a tutor"""
        raise NotImplementedError
    
    def delete_tutor(self, student_id: str, tutor_id: str) -> None:
        """Delete a tutor"""
        raise NotImplementedError
    
    def list_chats(self, student_id: str, tutor_id: str) -> List[SessionChat]:
        """List chats for a tutor"""
        raise NotImplementedError
    
    def append_chat(self, student_id: str, tutor_id: str, chat: SessionChat) -> None:
        """Add a chat message"""
        raise NotImplementedError
    
    def replace_chats(self, student_id: str, tutor_id: str, chats: List[SessionChat]) -> None:
        """Replace all chats for a tutor"""
        raise NotImplementedError


# SDK Configuration
@dataclass
class SDKConfig:
    """SDK configuration options"""
    api_key: str
    base_url: str = "https://api.djtconcept.ng"
    timeout: int = 30
    retries: int = 3
    storage: Optional[StorageConnector] = None
    default_persona: Optional[str] = None
    default_preset: str = "tutor_default"
    default_user_profile: Optional[Dict[str, Any]] = None
    default_metadata: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None


# Tutor initialization options
@dataclass
class TutorInit:
    """Tutor initialization options"""
    student_id: str
    tutor_id: Optional[str] = None
    tutor_name: Optional[str] = None
    subject: Optional[SessionSubject] = None
    grade_level: Optional[str] = None
    language: Optional[str] = None
