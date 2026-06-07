from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # GitHub
    github_webhook_secret: str
    github_token: str

    # LLM
    hf_token: str = ""
    llm_model_name: str = Field("llama3-8b-8192", alias="MODEL_NAME")

    # Groq
    groq_api_key: str = ""

    # Queue
    redis_url: str = "redis://localhost:6379/0"

    # App
    app_env: str = "development"
    app_port: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "populate_by_name": True,
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()