"""PostgreSQL storage implementation."""

import json
from typing import List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .base import Storage, Message

Base = declarative_base()


class MessageModel(Base):
    """Message database model."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    page_context = Column(Text)  # JSON string

    __table_args__ = (Index("idx_session_timestamp", "session_id", "timestamp"),)


class PostgresStorage(Storage):
    """PostgreSQL-based storage."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    async def save_message(self, message: Message) -> None:
        """Save a message."""
        session = self.SessionLocal()

        try:
            db_message = MessageModel(
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
                page_context=json.dumps(message.page_context),
            )
            session.add(db_message)
            session.commit()
        finally:
            session.close()

    async def get_messages(self, session_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a session."""
        session = self.SessionLocal()

        try:
            rows = (
                session.query(MessageModel)
                .filter(MessageModel.session_id == session_id)
                .order_by(MessageModel.timestamp.desc())
                .limit(limit)
                .all()
            )

            # Convert to Message objects
            messages = []
            for row in reversed(rows):  # Reverse to get chronological order
                messages.append(
                    Message(
                        session_id=row.session_id,
                        role=row.role,
                        content=row.content,
                        timestamp=row.timestamp,
                        page_context=json.loads(row.page_context) if row.page_context else {},
                    )
                )

            return messages
        finally:
            session.close()

    async def delete_session(self, session_id: str) -> None:
        """Delete all messages for a session."""
        session = self.SessionLocal()

        try:
            session.query(MessageModel).filter(MessageModel.session_id == session_id).delete()
            session.commit()
        finally:
            session.close()

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        session = self.SessionLocal()

        try:
            rows = session.query(MessageModel.session_id).distinct().all()
            return [row[0] for row in rows]
        finally:
            session.close()
