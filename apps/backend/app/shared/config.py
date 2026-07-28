from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPOSITORY_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Reservation Chatbot API"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: AnyHttpUrl = AnyHttpUrl("http://localhost:3000")
    database_url: str = (
        "mysql+pymysql://reservation_app:reservation_app@127.0.0.1:3306/reservation_chatbot"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
