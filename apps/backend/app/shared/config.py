from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AnyHttpUrl, field_validator
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
    model_path: Path = REPOSITORY_ROOT / "artifacts" / "models" / "intent-classifier.joblib"
    conversation_log_dir: Path = REPOSITORY_ROOT / "data" / "logs"
    app_timezone: str = "Asia/Jakarta"

    @field_validator("conversation_log_dir")
    @classmethod
    def resolve_conversation_log_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else REPOSITORY_ROOT / value

    @field_validator("app_timezone")
    @classmethod
    def validate_app_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("APP_TIMEZONE must be a valid IANA timezone.") from error
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
