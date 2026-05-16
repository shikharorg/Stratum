from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REDIS_URL: str
    IDENTITY_SERVICE_URL: str
    INGESTION_SERVICE_URL: str
    RETRIEVAL_SERVICE_URL: str
    WORKFLOW_SERVICE_URL: str
    CONNECTORS_SERVICE_URL: str
    EVALUATION_SERVICE_URL: str
    OBSERVER_SERVICE_URL: str
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "gateway"


settings = GatewaySettings()
