"""Provider-agnostic LLM access for FinSecAI.

Cohere is the current implementation. Additional providers can be added
without changing investigation or Copilot business logic.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
import logging
from typing import Any, Protocol

from app.core.config import settings

SYSTEM_PROMPT = (
    "You are FinSecAI's SOC analyst assistant. Be concise and factual. "
    "Never invent transaction details not supplied in the prompt."
)
logger = logging.getLogger(__name__)


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider cannot be used."""


class LLMProvider(Protocol):
    """Provider contract used by FinSecAI application services."""

    provider_name: str
    model: str

    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        ...

    def generate_structured_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        ...


class CohereInvestigationProvider:
    """Cohere implementation of the FinSecAI LLM provider contract."""

    provider_name = "cohere"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.cohere_api_key
        self.model = model or settings.cohere_chat_model
        if not self.api_key:
            raise LLMProviderError("COHERE_API_KEY is not configured")
        try:
            import cohere
        except Exception as exc:  # pragma: no cover
            raise LLMProviderError("Cohere SDK is not available") from exc
        self.client = cohere.ClientV2(api_key=self.api_key)

    def _extract_text(self, response: Any) -> str:
        message = getattr(response, "message", None)

        if not message:
            raise LLMProviderError("Cohere returned no message")

        content = getattr(message, "content", None) or []
        text_blocks = [
            block.text
            for block in content
            if (
                getattr(block, "type", None) == "text"
                and getattr(block, "text", None)
            )
        ]

        if not text_blocks:
            raise LLMProviderError("Cohere returned no text content")

        return "".join(text_blocks)

    def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        try:
            response = self.client.chat(
                model=self.model,
                temperature=settings.cohere_temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt or SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
        except Exception as exc:
            raise LLMProviderError("Cohere chat request failed") from exc

        return self._extract_text(response)

    def generate_structured_json(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        response_format: dict[str, Any] = {"type": "json_object"}
        if response_schema:
            response_format["schema"] = response_schema
        try:
            response = self.client.chat(
                model=self.model,
                temperature=settings.cohere_temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt or SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                response_format=response_format,
            )
        except Exception as exc:
            raise LLMProviderError("Cohere structured chat request failed") from exc

        return self._extract_text(response)


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider."""

    provider_name = (
        getattr(settings, "llm_provider", None) or "cohere"
    ).strip().lower()

    if provider_name == "cohere":
        return CohereInvestigationProvider()

    raise LLMProviderError(f"Unsupported LLM provider: {provider_name}")


async def generate(prompt: str) -> str | None:
    """Generate through Cohere only; no competing-provider or template fallback."""
    try:
        provider = CohereInvestigationProvider()
    except LLMProviderError:
        return None
    try:
        return await asyncio.to_thread(provider.generate_text, prompt)
    except Exception:
        return None


async def stream(prompt: str) -> AsyncIterator[str]:
    """Return a Copilot response from Cohere without blocking the event loop.

    ``ClientV2`` is the synchronous Cohere client.  Its ``chat_stream`` method
    returns a regular iterator, so using ``async for`` on it raises before a
    response can be sent.  A normal chat request in a worker thread is more
    reliable here; the websocket still delivers the completed answer as a
    single chunk and retains its existing protocol.
    """
    try:
        provider = get_llm_provider()
    except LLMProviderError as exc:
        yield str(exc)
        return
    try:
        answer = await asyncio.to_thread(provider.generate_text, prompt)
        if answer:
            yield answer
        else:
            yield "Cohere returned an empty response. Please try again."
    except Exception as exc:
        logger.warning("Cohere Copilot request failed: %s", type(exc).__name__)
        yield "The configured LLM is unavailable. No AI response was generated."


async def readiness() -> tuple[bool, str | None]:
    """Verify that the configured Cohere credentials and model can respond."""
    try:
        provider = get_llm_provider()
        response = await asyncio.to_thread(
            provider.generate_text,
            "Reply with exactly: ready",
            system_prompt="Reply with exactly the requested text.",
        )
        return bool(response.strip()), None if response.strip() else "Cohere returned an empty response"
    except LLMProviderError as exc:
        return False, str(exc)
    except Exception as exc:
        logger.warning("Cohere readiness check failed: %s", type(exc).__name__)
        return False, "Configured LLM provider rejected the request"
