import httpx

from talentscreen.config import get_settings
from talentscreen.generation.llm.base import EmbeddingResult


class OllamaEmbeddingProvider:
    """Local embeddings via Ollama (e.g. nomic-embed-text) — maps to Titan in production."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.base_url = settings.ollama_base_url.rstrip("/")

    def embed(self, texts: list[str]) -> EmbeddingResult:
        vectors: list[list[float]] = []
        with httpx.Client(timeout=120.0) as client:
            for text in texts:
                response = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model_name, "prompt": text},
                )
                response.raise_for_status()
                vectors.append(response.json()["embedding"])
        return EmbeddingResult(vectors=vectors, model=self.model_name)
