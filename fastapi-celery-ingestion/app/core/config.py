from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/app"
    REDIS_URL: str = "redis://localhost:6379/0"
    WORKER_MAX_THREADS: int = 20
    GLOBAL_RPS: int = 5
    PROVIDER_RPS_JSONPLACEHOLDER: int = 2
    PROVIDER_RPS_DUMMYJSON: int = 2
    PROVIDER_RPS_REQRES: int = 2
    HTTP_TIMEOUT_SECONDS: int = 10
    JOB_RETRY_MAX: int = 3
    JOB_RETRY_BACKOFF_SECONDS: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
