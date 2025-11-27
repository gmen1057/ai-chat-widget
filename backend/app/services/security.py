"""Security service - protection against attacks and abuse."""

import re
import logging
import hashlib
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityService:
    """
    Protection against various attacks:
    - Prompt injection
    - Token exhaustion (very long messages)
    - Spam / flooding
    - RCE attempts
    - Information reconnaissance
    """

    def __init__(self):
        # Rate limiting: session_id -> list of timestamps
        self._request_history: Dict[str, list] = defaultdict(list)
        # Banned sessions: session_id -> ban_until
        self._banned_sessions: Dict[str, datetime] = {}
        # Strike counter: session_id -> strike_count
        self._strikes: Dict[str, int] = defaultdict(int)

        # Configuration
        self.max_message_length = 2000  # Max chars per message
        self.max_requests_per_minute = 10
        self.max_requests_per_hour = 60
        self.ban_duration_minutes = 30
        self.max_strikes = 3  # After 3 strikes -> auto-ban

        # Patterns for attack detection
        self._prompt_injection_patterns = [
            r"ignore\s+(previous|all|above)",
            r"disregard\s+(previous|all|above)",
            r"forget\s+(previous|all|above)",
            r"new\s+instructions?",
            r"system\s*:",
            r"<\s*system\s*>",
            r"\[\s*system\s*\]",
            r"you\s+are\s+now",
            r"act\s+as\s+if",
            r"pretend\s+(you|to\s+be)",
            r"roleplay\s+as",
            r"respond\s+in\s+(chinese|chinese|arabic|korean)",
            r"отвечай\s+на\s+(китайском|арабском|корейском)",
            r"translate\s+everything\s+to",
            r"переведи\s+всё\s+на",
            r"ты\s+теперь",
            r"новые\s+инструкции",
            r"игнорируй\s+(предыдущ|всё|выше)",
            r"забудь\s+(предыдущ|всё|выше)",
        ]

        self._rce_patterns = [
            r"exec\s*\(",
            r"eval\s*\(",
            r"os\s*\.\s*system",
            r"subprocess",
            r"import\s+os",
            r"__import__",
            r"cat\s+/etc/",
            r"cat\s+~/.ssh",
            r"rm\s+-rf",
            r"/bin/(ba)?sh",
            r"curl\s+.+\s*\|",
            r"wget\s+.+\s*\|",
            r"выполни\s+команду",
            r"запусти\s+скрипт",
            r"execute\s+command",
            r"run\s+command",
            r"shell\s+command",
        ]

        self._recon_patterns = [
            r"what\s+(model|ai|llm)\s+are\s+you",
            r"какая\s+ты\s+модель",
            r"какой\s+у\s+тебя\s+api",
            r"your\s+api\s+key",
            r"твой\s+api\s+ключ",
            r"show\s+(me\s+)?your\s+(config|settings|prompt)",
            r"покажи\s+(свой\s+)?(конфиг|настройки|промпт)",
            r"what\s+is\s+your\s+system\s+prompt",
            r"какой\s+твой\s+системный\s+промпт",
            r"dump\s+(your\s+)?(memory|context|instructions)",
            r"print\s+(your\s+)?(instructions|prompt)",
        ]

        self._spam_patterns = [
            r"(.)\1{10,}",  # Same character 10+ times
            r"(test\s*){5,}",  # "test" repeated 5+ times
            r"^[a-z]{50,}$",  # 50+ lowercase letters without spaces
            r"^[A-Z]{50,}$",  # 50+ uppercase letters without spaces
        ]

        self._token_exhaustion_patterns = [
            r"напиши\s+(рассказ|историю|текст|эссе)\s+на\s+\d{3,}\s+(слов|символов)",
            r"write\s+(a\s+)?(story|essay|text)\s+(of\s+)?\d{3,}\s+(words|characters)",
            r"сгенерируй\s+\d{3,}\s+(слов|символов|строк)",
            r"generate\s+\d{3,}\s+(words|characters|lines)",
            r"repeat\s+.+\s+\d{3,}\s+times",
            r"повтори\s+.+\s+\d{3,}\s+раз",
        ]

    def is_banned(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if session is banned.

        Returns:
            Tuple of (is_banned, ban_reason)
        """
        if session_id in self._banned_sessions:
            ban_until = self._banned_sessions[session_id]
            if datetime.now() < ban_until:
                remaining = (ban_until - datetime.now()).seconds // 60
                return True, f"Сессия заблокирована. Осталось {remaining} минут."
            else:
                # Ban expired
                del self._banned_sessions[session_id]
                self._strikes[session_id] = 0

        return False, None

    def ban_session(self, session_id: str, reason: str, duration_minutes: int = None):
        """Ban a session."""
        duration = duration_minutes or self.ban_duration_minutes
        self._banned_sessions[session_id] = datetime.now() + timedelta(minutes=duration)
        logger.warning(f"Session banned: {session_id[:20]}... Reason: {reason}")

    def add_strike(self, session_id: str, reason: str) -> int:
        """
        Add a strike to session.

        Returns:
            Current strike count
        """
        self._strikes[session_id] += 1
        strikes = self._strikes[session_id]

        logger.warning(f"Strike {strikes}/{self.max_strikes} for session {session_id[:20]}... Reason: {reason}")

        if strikes >= self.max_strikes:
            self.ban_session(session_id, f"Max strikes reached ({strikes})")

        return strikes

    def check_rate_limit(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if session has exceeded rate limits.

        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = datetime.now()
        history = self._request_history[session_id]

        # Clean old entries
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        history = [t for t in history if t > hour_ago]
        self._request_history[session_id] = history

        # Count requests
        requests_last_minute = sum(1 for t in history if t > minute_ago)
        requests_last_hour = len(history)

        if requests_last_minute >= self.max_requests_per_minute:
            return False, f"Слишком много запросов. Подождите минуту. ({requests_last_minute}/{self.max_requests_per_minute})"

        if requests_last_hour >= self.max_requests_per_hour:
            return False, f"Слишком много запросов за час. ({requests_last_hour}/{self.max_requests_per_hour})"

        # Record this request
        history.append(now)
        return True, None

    def detect_attack(self, message: str, session_id: str = None) -> Optional[Dict]:
        """
        Detect various attack types in message.

        Returns:
            Attack info dict if detected, None otherwise
            {"type": "...", "description": "...", "severity": "..."}
        """
        message_lower = message.lower()

        # Check message length (token exhaustion)
        if len(message) > self.max_message_length:
            return {
                "type": "token_exhaustion",
                "description": f"Сообщение слишком длинное ({len(message)} символов)",
                "severity": "medium",
            }

        # Check prompt injection
        for pattern in self._prompt_injection_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "type": "prompt_injection",
                    "description": f"Попытка prompt injection: {pattern}",
                    "severity": "high",
                }

        # Check RCE attempts
        for pattern in self._rce_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "type": "rce_attempt",
                    "description": f"Попытка RCE/выполнения команд",
                    "severity": "critical",
                }

        # Check reconnaissance
        for pattern in self._recon_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "type": "reconnaissance",
                    "description": f"Попытка получить информацию о системе",
                    "severity": "medium",
                }

        # Check spam patterns
        for pattern in self._spam_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return {
                    "type": "spam",
                    "description": "Обнаружен спам или бессмысленный текст",
                    "severity": "low",
                }

        # Check token exhaustion requests
        for pattern in self._token_exhaustion_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "type": "token_exhaustion",
                    "description": "Запрос на генерацию слишком большого текста",
                    "severity": "medium",
                }

        return None

    def validate_request(
        self, message: str, session_id: str
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Full validation of incoming request.

        Returns:
            Tuple of (is_valid, error_message, attack_info)
        """
        # Check if banned
        is_banned, ban_reason = self.is_banned(session_id)
        if is_banned:
            return False, ban_reason, None

        # Check rate limit
        is_allowed, rate_error = self.check_rate_limit(session_id)
        if not is_allowed:
            return False, rate_error, None

        # Detect attack
        attack = self.detect_attack(message, session_id)
        if attack:
            # Add strike
            strikes = self.add_strike(session_id, attack["type"])
            attack["strikes"] = strikes
            attack["max_strikes"] = self.max_strikes

            # Auto-ban for critical attacks
            if attack["severity"] == "critical":
                self.ban_session(session_id, attack["type"], duration_minutes=60)
                return False, "Доступ заблокирован из-за подозрительной активности.", attack

            # Return attack info but allow the request (AI will handle it)
            return True, None, attack

        return True, None, None

    def get_blocked_response(self, attack: Dict) -> str:
        """Get response message for blocked attack."""
        attack_type = attack.get("type", "unknown")

        responses = {
            "prompt_injection": "Я заметил попытку изменить мои инструкции. Это не сработает. Чем могу помочь по существу?",
            "rce_attempt": "Я не выполняю системные команды. Чем могу помочь?",
            "token_exhaustion": "Извините, я не могу генерировать такие большие тексты. Попробуйте уменьшить запрос.",
            "reconnaissance": "Я не раскрываю техническую информацию о себе. Чем ещё могу помочь?",
            "spam": "Пожалуйста, сформулируйте ваш вопрос понятнее.",
        }

        return responses.get(attack_type, "Запрос заблокирован из-за подозрительной активности.")


# Global instance
security_service = SecurityService()
