from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    INGESTION_SERVICE_URL: str
    ENCRYPTION_KEY: str | None = None
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "connectors"


settings = ConnectorSettings()
