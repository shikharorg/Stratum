from pydantic_settings import BaseSettings, SettingsConfigDict


class ObserverSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    REDIS_CONSUMER_GROUP: str = "observer-group"
    REDIS_CONSUMER_NAME: str = "observer-1"
    EVENT_RETENTION_DAYS: int = 90
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "observer"


settings = ObserverSettings()
