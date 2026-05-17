from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkflowSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    RETRIEVAL_SERVICE_URL: str
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "workflow"


settings = WorkflowSettings()
