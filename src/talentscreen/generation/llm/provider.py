import hashlib
import json
from typing import Any

import httpx

from talentscreen.config import get_settings
from talentscreen.generation.llm.base import LLMProvider, LLMResponse


class _PromptPrefixCache:
    """Local hash-prefix cache; maps to Bedrock prompt caching in production."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = value


_prompt_cache = _PromptPrefixCache()


def _cache_key(messages: list[dict[str, str]]) -> str:
    prefix = json.dumps(messages[:1], sort_keys=True)
    return hashlib.sha256(prefix.encode()).hexdigest()


class OllamaLLMProvider:
    def __init__(self) -> None:
        self.settings = get_settings()

    def invoke(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        cache_key = _cache_key(messages)
        cached = _prompt_cache.get(cache_key)
        if cached is not None:
            return LLMResponse(content=cached, model=self.settings.ollama_model, cached=True)

        payload: dict[str, Any] = {
            "model": self.settings.ollama_model,
            "messages": messages,
            "stream": False,
        }
        if response_format:
            payload["format"] = "json" if response_format.get("type") == "json_object" else None

        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self.settings.ollama_base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            _prompt_cache.set(cache_key, content)
            return LLMResponse(content=content, model=self.settings.ollama_model)


class AnthropicLLMProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required when LLM_PROVIDER=anthropic")

    def invoke(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        system = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                user_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.settings.anthropic_model,
            "max_tokens": 1024,
            "messages": user_messages,
        }
        if system:
            payload["system"] = system

        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data["content"][0]["text"]
            return LLMResponse(content=content, model=self.settings.anthropic_model)


class GroqLLMProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.groq_api_key:
            raise ValueError("GROQ_API_KEY required when LLM_PROVIDER=groq")

    def invoke(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.settings.groq_model,
            "messages": messages,
        }
        if response_format and response_format.get("type") == "json_object":
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return LLMResponse(content=content, model=self.settings.groq_model)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    match settings.llm_provider:
        case "ollama":
            return OllamaLLMProvider()
        case "anthropic":
            return AnthropicLLMProvider()
        case "groq":
            return GroqLLMProvider()
        case "bedrock":
            from talentscreen.generation.llm.bedrock_stub import BedrockLLMProvider

            return BedrockLLMProvider()
        case _:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
