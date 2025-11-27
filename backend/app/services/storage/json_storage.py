"""JSON file storage implementation."""

import os
import json
from typing import List, Dict
from datetime import datetime
from .base import Storage, Message


class JSONStorage(Storage):
    """JSON file-based storage."""

    def __init__(self, data_path: str):
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)

    def _get_session_file(self, session_id: str) -> str:
        """Get file path for session."""
        return os.path.join(self.data_path, f"{session_id}.json")

    async def save_message(self, message: Message) -> None:
        """Save a message."""
        file_path = self._get_session_file(message.session_id)

        # Load existing messages
        messages = []
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                messages = json.load(f)

        # Append new message
        messages.append(message.to_dict())

        # Save back
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    async def get_messages(self, session_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a session."""
        file_path = self._get_session_file(session_id)

        if not os.path.exists(file_path):
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert to Message objects
        messages = []
        for item in data[-limit:]:  # Last N messages
            messages.append(
                Message(
                    session_id=item["session_id"],
                    role=item["role"],
                    content=item["content"],
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    page_context=item.get("page_context", {}),
                )
            )

        return messages

    async def delete_session(self, session_id: str) -> None:
        """Delete all messages for a session."""
        file_path = self._get_session_file(session_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        sessions = []
        for filename in os.listdir(self.data_path):
            if filename.endswith(".json"):
                sessions.append(filename[:-5])  # Remove .json
        return sessions
