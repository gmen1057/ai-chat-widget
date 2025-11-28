"""Chat API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from ..services.storage.base import Message
from ..services.ai_service import ai_service
from ..services.telegram import telegram_service
from ..services.security import security_service
from .schemas import PageContext, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get AI response.

    This endpoint:
    1. Validates request (security checks)
    2. Saves user message with page context
    3. Loads conversation history
    4. Builds system prompt with page context and knowledge base
    5. Sends to AI
    6. Saves AI response
    7. Returns reply
    """
    from ..main import storage, knowledge_base

    # ==========================================
    # SECURITY CHECKS
    # ==========================================
    is_valid, error_message, attack_info = security_service.validate_request(
        message=request.message,
        session_id=request.session_id
    )

    # If completely blocked (banned or rate limited)
    if not is_valid and not attack_info:
        return ChatResponse(
            reply=error_message,
            session_id=request.session_id,
            blocked=True
        )

    # If attack detected
    if attack_info:
        page_url = request.page_context.url if request.page_context else "unknown"

        # Log attack
        logger.warning(
            f"Attack detected: {attack_info['type']} | "
            f"Session: {request.session_id[:20]}... | "
            f"Page: {page_url} | "
            f"Severity: {attack_info['severity']}"
        )

        # Send Telegram alert for high/critical attacks
        if attack_info["severity"] in ["high", "critical"]:
            await telegram_service.send_alert(
                message=f"Тип: {attack_info['type']}\n"
                        f"Severity: {attack_info['severity']}\n"
                        f"Описание: {attack_info['description']}\n"
                        f"Strikes: {attack_info.get('strikes', 0)}/{attack_info.get('max_strikes', 3)}",
                alert_type="escalation",
                session_id=request.session_id,
                page_url=page_url,
            )

        # If banned after this attack
        if not is_valid:
            return ChatResponse(
                reply=error_message,
                session_id=request.session_id,
                blocked=True,
                attack_detected=attack_info["type"]
            )

        # Return blocked response (but don't ban yet)
        blocked_response = security_service.get_blocked_response(attack_info)
        return ChatResponse(
            reply=blocked_response,
            session_id=request.session_id,
            blocked=False,
            attack_detected=attack_info["type"]
        )

    # ==========================================
    # DETECT ESCALATION / FEEDBACK
    # ==========================================
    message_lower = request.message.lower()
    page_url = request.page_context.url if request.page_context else "unknown"

    # Escalation keywords (user wants human help) - use word stems for flexibility
    escalation_keywords = [
        "человек", "оператор", "менеджер", "поддержк",  # want human
        "не работа", "сломал", "баг", "ошибк",  # something broken
        "не могу", "не получ", "помоги", "срочно",  # need help
        "talk to human", "real person", "support", "help me"
    ]

    # Positive feedback keywords
    positive_keywords = [
        "спасибо", "благодар",  # thanks
        "отлично", "супер", "класс", "молодец", "круто", "здорово", "классн",  # great
        "помогл", "получил", "понял", "разобрал",  # it worked
        "thank", "great", "awesome", "helpful", "works", "nice", "cool"
    ]

    # Negative feedback keywords
    negative_keywords = [
        "плохо", "ужасн", "отстой", "фигн", "хрен",  # bad
        "не помог", "бесполезн", "не понима", "тупой", "глуп", "идиот",  # useless
        "не работа", "сломал",  # broken (also triggers escalation)
        "useless", "stupid", "bad", "terrible", "suck", "hate"
    ]

    # Check for escalation (broken things, need human)
    is_escalation = any(kw in message_lower for kw in escalation_keywords)
    is_negative = any(kw in message_lower for kw in negative_keywords)
    is_positive = any(kw in message_lower for kw in positive_keywords)

    # Don't send positive if also negative (sarcasm protection)
    if is_positive and is_negative:
        is_positive = False

    if is_escalation:
        print(f"🚨 Escalation detected: {request.message[:50]}...")
        try:
            result = await telegram_service.send_escalation(
                reason="Пользователь запрашивает помощь или сообщает о проблеме",
                conversation_summary=request.message[:300],
                session_id=request.session_id,
                page_url=page_url,
            )
            print(f"Telegram escalation result: {result}")
        except Exception as e:
            print(f"Telegram escalation ERROR: {e}")

    elif is_negative:
        print(f"😞 Negative feedback detected: {request.message[:50]}...")
        try:
            result = await telegram_service.send_feedback(
                text=request.message[:300],
                sentiment="negative",
                session_id=request.session_id,
                page_url=page_url,
            )
            print(f"Telegram negative feedback result: {result}")
        except Exception as e:
            print(f"Telegram negative feedback ERROR: {e}")

    elif is_positive:
        print(f"😊 Positive feedback detected: {request.message[:50]}...")
        try:
            result = await telegram_service.send_feedback(
                text=request.message[:300],
                sentiment="positive",
                session_id=request.session_id,
                page_url=page_url,
            )
            print(f"Telegram positive feedback result: {result}")
        except Exception as e:
            print(f"Telegram positive feedback ERROR: {e}")

    # ==========================================
    # NORMAL MESSAGE PROCESSING
    # ==========================================
    try:
        # Save user message with page context
        page_context_dict = request.page_context.dict() if request.page_context else {}

        user_message = Message(
            session_id=request.session_id,
            role="user",
            content=request.message,
            page_context=page_context_dict,
        )
        await storage.save_message(user_message)

        # Load conversation history
        history = await storage.get_messages(request.session_id, limit=20)

        # Build system prompt with page context
        system_prompt = ai_service.build_system_prompt(
            page_context=page_context_dict, knowledge_base=knowledge_base.get_content()
        )

        # Prepare messages for AI
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})

        # Get AI response
        ai_reply = await ai_service.chat_completion(messages)

        # Save AI response
        assistant_message = Message(
            session_id=request.session_id, role="assistant", content=ai_reply, page_context=page_context_dict
        )
        await storage.save_message(assistant_message)

        return ChatResponse(reply=ai_reply, session_id=request.session_id)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    from ..main import storage

    try:
        await storage.delete_session(session_id)
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions():
    """Get all session IDs."""
    from ..main import storage

    try:
        sessions = await storage.get_all_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alert")
async def send_alert(alert_type: str, message: str):
    """
    Send alert to Telegram.

    Alert types: bug, escalation, suggestion, feedback
    """
    try:
        await telegram_service.send_alert(message, alert_type)
        return {"message": "Alert sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    """Get chat history for a session."""
    from ..main import storage

    try:
        messages = await storage.get_messages(session_id, limit)
        return {
            "session_id": session_id,
            "messages": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp.isoformat()} for msg in messages
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telegram/test")
async def test_telegram():
    """
    Test Telegram connection.

    Returns bot info if configured correctly.
    """
    result = await telegram_service.test_connection()

    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Telegram not configured"))

    return result


@router.post("/telegram/send-test")
async def send_test_message():
    """
    Send a test message to Telegram.

    Use this to verify alerts are working.
    """
    if not telegram_service.enabled:
        raise HTTPException(status_code=400, detail="Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    success = await telegram_service.send_alert(
        message="🧪 Test message from AI Chat Widget!\n\nIf you see this, Telegram alerts are working correctly.",
        alert_type="success",
    )

    if success:
        return {"message": "Test message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test message")


@router.get("/security/status")
async def security_status():
    """Get security service status (for debugging)."""
    return {
        "max_message_length": security_service.max_message_length,
        "max_requests_per_minute": security_service.max_requests_per_minute,
        "max_requests_per_hour": security_service.max_requests_per_hour,
        "ban_duration_minutes": security_service.ban_duration_minutes,
        "max_strikes": security_service.max_strikes,
        "active_bans": len(security_service._banned_sessions),
    }
