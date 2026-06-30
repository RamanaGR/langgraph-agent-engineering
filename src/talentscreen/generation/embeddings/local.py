from talentscreen.config import get_settings
from talentscreen.generation.embeddings.ollama import OllamaEmbeddingProvider
from talentscreen.generation.llm.base import EmbeddingProvider, EmbeddingResult


class LocalEmbeddingProvider:
    """Local sentence-transformers; production swap → Amazon Titan via same interface."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> EmbeddingResult:
        model = self._load()
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        return EmbeddingResult(vectors=vectors, model=self.model_name)


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider()
    if settings.embedding_provider == "local":
        return LocalEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
