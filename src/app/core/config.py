from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    PROJECT_NAME: str = "Healthcare Cost Navigator"
    DATABASE_URL: str | None = None
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "healthcare_cost_navigator"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"


settings = Settings()
