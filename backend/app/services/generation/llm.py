"""Gemini generation service."""
import logging
from typing import AsyncGenerator, Optional

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger("lumina.llm")


class LLMService:
    _instance: Optional["LLMService"] = None

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.LLM_MODEL

    @classmethod
    def get(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _config(self, system: str) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=settings.LLM_MAX_TOKENS,
            temperature=0.2,
        )

    async def generate(self, system: str, user: str) -> tuple[str, int]:
        resp = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user,
            config=self._config(system),
        )
        text = resp.text or ""
        usage = resp.usage_metadata
        tokens = 0
        if usage:
            tokens = (usage.prompt_token_count or 0) + (usage.candidates_token_count or 0)
        return text, tokens

    async def generate_stream(self, system: str, user: str) -> AsyncGenerator[str, None]:
        # generate_content_stream is itself an async-generator function,
        # so calling it returns an async iterator — do NOT await it.
        async for chunk in self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=user,
            config=self._config(system),
        ):
            if chunk.text:
                yield chunk.text
