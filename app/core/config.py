from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    google_client_id: str
    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str
    google_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    jwt_algorithm: str = "HS256"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
