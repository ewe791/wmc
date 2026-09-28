from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """AI Service 运行配置。"""

    ai_database_url: str = (
        "postgresql+psycopg://customer_service:customer_service"
        "@127.0.0.1:5432/ai_customer_service"
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    internal_service_token: str = "customer-internal-token"
    jwt_secret: str = "ecommerce-secret"
    jwt_algorithm: str = "HS256"
    llm_provider: Literal["openai_compatible", "deepseek", "qwen"] = "openai_compatible"
    ecommerce_base_url: str = "http://127.0.0.1:8001/api/v1"
    ecommerce_timeout_seconds: float = 8.0
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str
    llm_thinking_mode: Literal["disabled", "enabled"] = "disabled"
    llm_timeout_seconds: float = Field(default=30, gt=0)
    history_message_limit: int = Field(default=30, ge=1, le=60)
    history_character_budget: int = Field(default=12000, ge=1)
    prompt_version: str = "customer-support-v1"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
