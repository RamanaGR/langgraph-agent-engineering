from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://talentscreen:talentscreen@localhost:5432/talentscreen"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "talentscreen-docs"
    minio_secure: bool = False

    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "talentscreen_chunks"

    embedding_provider: str = "ollama"
    embedding_model: str = "nomic-embed-text:latest"
    embedding_dimension: int = 768

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    chunk_size: int = 512
    chunk_overlap: int = 64
    default_tenant_id: str = "demo-tenant"

    # Retrieval / RAG (Phase 1a Week 2)
    retrieval_top_k: int = 20
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    query_cache_ttl_seconds: int = 3600

    # Phase 1b — hybrid + semantic cache
    retrieval_mode: str = "hybrid"
    rrf_k: int = 60
    semantic_cache_threshold: float = 0.92
    semantic_cache_ttl_seconds: int = 86400

    # Phase 2a — LangGraph agents
    agent_checkpointer: str = "memory"
    summarization_message_threshold: int = 10

    # Phase 3 — auth + CORS
    auth_enabled: bool = False
    api_key_recruiter: str = "recruiter-dev-key"
    api_key_candidate: str = "candidate-dev-key"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
