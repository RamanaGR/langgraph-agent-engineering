from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class EmbeddingResult:
    vectors: list[list[float]]
    model: str


class EmbeddingProvider(Protocol):
  def embed(self, texts: list[str]) -> EmbeddingResult: ...


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, Any] | None = None
    cached: bool = False


class LLMProvider(Protocol):
    def invoke(
        self,
        messages: list[dict[str, str]],
        *,
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse: ...
