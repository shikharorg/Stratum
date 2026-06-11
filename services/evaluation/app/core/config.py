from pydantic_settings import BaseSettings, SettingsConfigDict


class EvaluationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "evaluation"


settings = EvaluationSettings()
