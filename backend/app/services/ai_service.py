"""Universal AI service using OpenAI-compatible API."""

import os
import time
import uuid
import httpx
from typing import List, Dict, Optional
from ..config import settings

# Default system prompt (used if system_prompt.md not found)
DEFAULT_SYSTEM_PROMPT = """Ты AI-ассистент на сайте.

КОНТЕКСТ СТРАНИЦЫ:
- URL: {page_url}
- Заголовок: {page_title}
- Описание: {page_description}
{page_headings}
{selected_text}

БАЗА ЗНАНИЙ:
{knowledge_base}

ПРАВИЛА:
1. Отвечай кратко и по делу (2-4 предложения)
2. Используй контекст страницы для релевантных ответов
3. Если пользователь выделил текст - учитывай его в ответе
4. Отвечай на языке пользователя
5. Если не знаешь ответа - честно скажи об этом
6. Будь вежливым и полезным
"""


class AIService:
    """Universal AI client for any OpenAI-compatible API."""

    def __init__(self):
        self.base_url = settings.AI_BASE_URL.rstrip("/") if settings.AI_BASE_URL else ""
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS
        self._system_prompt_template = None

        # GigaChat token management
        self._gigachat_credentials = settings.GIGACHAT_CREDENTIALS
        self._gigachat_token_expires_at = 0

    def _is_gigachat(self) -> bool:
        """Check if using GigaChat API."""
        return "gigachat" in self.base_url.lower()

    async def _refresh_gigachat_token(self):
        """Refresh GigaChat access token if expired or about to expire."""
        if not self._is_gigachat() or not self._gigachat_credentials:
            return

        # Refresh if expires in less than 60 seconds
        if time.time() * 1000 < self._gigachat_token_expires_at - 60000:
            return

        print("Refreshing GigaChat token...")
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                response = await client.post(
                    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "RqUID": str(uuid.uuid4()),
                        "Authorization": f"Basic {self._gigachat_credentials}",
                    },
                    data="scope=GIGACHAT_API_PERS",
                )
                response.raise_for_status()
                data = response.json()

                self.api_key = data["access_token"]
                self._gigachat_token_expires_at = data["expires_at"]
                print(f"GigaChat token refreshed, expires at {self._gigachat_token_expires_at}")

        except Exception as e:
            print(f"Failed to refresh GigaChat token: {e}")

    def _load_system_prompt_template(self) -> str:
        """Load system prompt from file or use default."""
        if self._system_prompt_template is not None:
            return self._system_prompt_template

        # Try to load from knowledge/system_prompt.md
        prompt_path = os.path.join(settings.KNOWLEDGE_PATH, "system_prompt.md")

        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Remove comments (lines starting with #)
                    lines = [line for line in content.split("\n")
                             if not line.strip().startswith("#")]
                    self._system_prompt_template = "\n".join(lines).strip()
                    print(f"Loaded custom system prompt from {prompt_path}")
            except Exception as e:
                print(f"Warning: Failed to load system prompt: {e}")
                self._system_prompt_template = DEFAULT_SYSTEM_PROMPT
        else:
            print(f"Using default system prompt (no {prompt_path} found)")
            self._system_prompt_template = DEFAULT_SYSTEM_PROMPT

        return self._system_prompt_template

    def reload_prompt(self):
        """Force reload of system prompt from file."""
        self._system_prompt_template = None
        return self._load_system_prompt_template()

    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """Format messages for API."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]

    def _is_gemini(self) -> bool:
        """Check if using Google Gemini API."""
        return "googleapis.com" in self.base_url or "generativelanguage" in self.base_url

    async def _gemini_completion(
        self, messages: List[Dict], temperature: Optional[float] = None, max_tokens: Optional[int] = None
    ) -> str:
        """Handle Google Gemini API (different format from OpenAI)."""
        # Build Gemini endpoint
        # Format: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        # Convert OpenAI messages to Gemini format
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_instruction = content
            elif role == "user":
                gemini_contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                gemini_contents.append({"role": "model", "parts": [{"text": content}]})

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature or self.temperature,
                "maxOutputTokens": max_tokens or self.max_tokens,
            }
        }

        # Add system instruction if present
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                # Extract text from Gemini response
                return data["candidates"][0]["content"]["parts"][0]["text"]

        except httpx.HTTPStatusError as e:
            error_msg = f"Gemini API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)

    async def chat_completion(
        self, messages: List[Dict], temperature: Optional[float] = None, max_tokens: Optional[int] = None
    ) -> str:
        """
        Send chat completion request to AI API.

        Works with:
        - OpenAI (https://api.openai.com/v1)
        - Anthropic Claude (https://api.anthropic.com/v1)
        - Google Gemini (https://generativelanguage.googleapis.com)
        - GigaChat (https://gigachat.devices.sberbank.ru/api/v1)
        - DeepSeek (https://api.deepseek.com/v1)
        - Qwen (https://dashscope.aliyuncs.com/compatible-mode/v1)
        - Groq (https://api.groq.com/openai/v1)
        - YandexGPT (https://llm.api.cloud.yandex.net/foundationModels/v1)
        - Ollama (http://localhost:11434/v1)
        - OpenRouter (https://openrouter.ai/api/v1)
        - Any OpenAI-compatible API
        """
        # Handle Gemini separately (different API format)
        if self._is_gemini():
            return await self._gemini_completion(messages, temperature, max_tokens)

        # Auto-refresh GigaChat token if needed
        await self._refresh_gigachat_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Special handling for Anthropic Claude
        if "anthropic.com" in self.base_url:
            headers["anthropic-version"] = "2023-06-01"

        payload = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        # API endpoint
        endpoint = f"{self.base_url}/chat/completions"

        # Special handling for different providers
        if "anthropic.com" in self.base_url:
            endpoint = f"{self.base_url}/messages"
        elif "foundationModels" in self.base_url:
            # Old YandexGPT format (foundationModels/v1)
            endpoint = f"{self.base_url}/completion"
        # Note: New YandexGPT format (llm.api.cloud.yandex.net/v1) is OpenAI-compatible

        try:
            # GigaChat uses self-signed certificate
            verify_ssl = not self._is_gigachat()
            async with httpx.AsyncClient(timeout=60.0, verify=verify_ssl) as client:
                response = await client.post(endpoint, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                # Extract content based on provider
                if "anthropic.com" in self.base_url:
                    # Anthropic format
                    return data["content"][0]["text"]
                elif "foundationModels" in self.base_url:
                    # Old YandexGPT format (foundationModels/v1)
                    return data["result"]["alternatives"][0]["message"]["text"]
                else:
                    # Standard OpenAI format (OpenAI, GigaChat, DeepSeek, Qwen, Groq, Ollama, YandexGPT v1, etc.)
                    return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            error_msg = f"AI API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data}"
            except:
                error_msg += f" - {e.response.text}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"AI request failed: {str(e)}")

    def build_system_prompt(self, page_context: Dict, knowledge_base: str) -> str:
        """Build system prompt with page context and knowledge base."""
        template = self._load_system_prompt_template()

        # Extract page context
        url = page_context.get("url", "неизвестен")
        title = page_context.get("title", "неизвестен")
        meta_description = page_context.get("meta_description", "")
        headings = page_context.get("headings", {})
        selected_text = page_context.get("selected_text", "")

        # Format headings
        headings_text = ""
        if headings:
            h1_list = headings.get("h1", [])
            h2_list = headings.get("h2", [])
            if h1_list:
                headings_text += f"- H1: {', '.join(h1_list)}"
            if h2_list:
                if headings_text:
                    headings_text += "\n"
                headings_text += f"- H2: {', '.join(h2_list[:5])}"

        # Format selected text
        selected_text_formatted = ""
        if selected_text:
            selected_text_formatted = f"- Выделенный текст: {selected_text}"

        # Replace placeholders
        prompt = template.format(
            page_url=url,
            page_title=title,
            page_description=meta_description,
            page_headings=headings_text,
            selected_text=selected_text_formatted,
            knowledge_base=knowledge_base or "База знаний не загружена.",
        )

        return prompt


# Global instance
ai_service = AIService()
