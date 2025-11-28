"""Pydantic schemas for Chat API."""

from pydantic import BaseModel
from typing import Dict, Optional, List


class PageContext(BaseModel):
    """Page context from frontend."""

    url: str = ""
    title: str = ""
    meta_description: Optional[str] = ""
    headings: Optional[Dict[str, List[str]]] = {}
    selected_text: Optional[str] = ""
    main_content: Optional[str] = ""


class ChatRequest(BaseModel):
    """Chat message request."""

    session_id: str
    message: str
    page_context: Optional[PageContext] = None


class ChatResponse(BaseModel):
    """Chat message response."""

    reply: str
    session_id: str
    blocked: bool = False
    attack_detected: Optional[str] = None
