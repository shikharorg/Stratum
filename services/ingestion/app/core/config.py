from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    QDRANT_COLLECTION: str
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "ingestion"

    MINIO_URL: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET: str


settings = IngestionSettings()
