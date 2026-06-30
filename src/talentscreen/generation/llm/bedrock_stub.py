"""Typed Bedrock shapes — interview stub (not called without AWS credentials)."""

from dataclasses import dataclass
from typing import Any

from talentscreen.config import get_settings
from talentscreen.generation.llm.base import LLMResponse


@dataclass
class BedrockInvokeRequest:
    model_id: str
    messages: list[dict[str, str]]
    max_tokens: int = 1024
    temperature: float = 0.0
    system: str | None = None
    tools: list[dict[str, Any]] | None = None
    prompt_cache: bool = False


@dataclass
class BedrockInvokeResponse:
    content: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    def to_llm_response(self) -> LLMResponse:
        return LLMResponse(
            content=self.content,
            model=self.model_id,
            usage={
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cache_read_input_tokens": self.cache_read_input_tokens,
            },
            cached=self.cache_read_input_tokens > 0,
        )


class BedrockLLMProvider:
    """Production mapping for Amazon Bedrock Claude Sonnet + prompt caching."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def invoke(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        request = BedrockInvokeRequest(
            model_id=self.settings.bedrock_model_id,
            messages=messages,
            tools=tools,
            prompt_cache=True,
        )
        raise NotImplementedError(
            "Bedrock provider requires AWS credentials. "
            f"Stub request shape: model={request.model_id}, messages={len(messages)}. "
            "Set LLM_PROVIDER=ollama|anthropic|groq for local development."
        )

    @staticmethod
    def example_response() -> BedrockInvokeResponse:
        """Reference shape for interviews / IaC docs."""
        return BedrockInvokeResponse(
            content='{"answer": "example", "citations": []}',
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            input_tokens=120,
            output_tokens=45,
            cache_read_input_tokens=80,
        )
