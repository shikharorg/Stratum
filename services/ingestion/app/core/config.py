from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION: str
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "ingestion"


settings = IngestionSettings()
