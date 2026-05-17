from arq.connections import RedisSettings

from app.core.config import settings


class WorkerSettings:
    functions: list = []
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs: int = 10
    job_timeout: int = 600
