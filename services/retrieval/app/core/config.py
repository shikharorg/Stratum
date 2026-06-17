from pydantic_settings import BaseSettings, SettingsConfigDict


class RetrievalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION: str
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    OPENAI_API_KEY: str | None = None
    OPENAI_GENERATION_MODEL: str = "gpt-4o"
    OPENAI_GENERATION_MAX_TOKENS: int = 700
    OPENAI_VALIDATION_MODEL: str = "gpt-4o-mini"
    EVALUATION_SERVICE_URL: str = "http://localhost:8007"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "retrieval"


settings = RetrievalSettings()
