from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    Values are loaded from environment variables or .env file.
    """

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/featureflag"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 60  # How long to cache flag configs

    # Application
    app_env: str = "development"
    debug: bool = True

    class Config:
        # Tell pydantic to read from .env file
        env_file = ".env"


# Create a single instance to import elsewhere
settings = Settings()
