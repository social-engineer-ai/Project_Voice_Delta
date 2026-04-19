"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str
    sarvam_api_key: str
    gemini_api_key: str
    database_url: str = "sqlite:///./shopsaarthi.db"
    log_level: str = "INFO"

    # Sarvam endpoint
    sarvam_stt_url: str = "https://api.sarvam.ai/speech-to-text"

    # Gemini model choice. Flash-Lite is cheapest; upgrade if accuracy insufficient.
    gemini_model: str = "gemini-2.5-flash-lite"


settings = Settings()
