"""Abstract storage interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class Message:
    """Chat message."""

    def __init__(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        page_context: Optional[Dict] = None,
    ):
        self.session_id = session_id
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.page_context = page_context or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "page_context": self.page_context,
        }


class Storage(ABC):
    """Abstract storage interface."""

    @abstractmethod
    async def save_message(self, message: Message) -> None:
        """Save a message."""
        pass

    @abstractmethod
    async def get_messages(self, session_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a session."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete all messages for a session."""
        pass

    @abstractmethod
    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        pass
