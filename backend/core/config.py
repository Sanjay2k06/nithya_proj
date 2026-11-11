"""
Backend Configuration and Environment Settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Explainable Forest Fire Detection API"
    APP_ENV: str = "development"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8010
    PORT: Optional[int] = None
    FRONTEND_ORIGIN: str = "http://localhost:5180"
    CORS_ORIGINS: str = ""

    # Database Settings (PostgreSQL or SQLite fallback)
    DATABASE_URL: str = "sqlite:///./runtime/forest_fire.db"

    # Model Settings
    MODEL_PATH: str = "artifacts/checkpoints/firenet_best.pt"
    MODEL_DEVICE: str = "auto"
    MODEL_DEMO_MODE: bool = False

    # Gemini multimodal analysis for image and video uploads (never CCTV alerts)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # Thresholds & Temporal Verification
    IMAGE_SIZE: int = 224
    FIRE_THRESHOLD: float = 0.75
    SMOKE_THRESHOLD: float = 0.70
    TEMPORAL_WINDOW: int = 5
    TEMPORAL_REQUIRED_POSITIVES: int = 3
    ALERT_COOLDOWN_SECONDS: int = 60

    # Uploads & Storage
    MAX_UPLOAD_MB: int = 25
    MAX_VIDEO_SECONDS: int = 120
    MEDIA_ROOT: str = "./runtime/media"

    # Notifications
    NOTIFICATION_PROVIDER: str = "console"
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_cors_origins(self) -> List[str]:
        origins = [
            self.FRONTEND_ORIGIN.rstrip("/"),
            "http://localhost:5180",
            "http://127.0.0.1:5180",
            "http://localhost:5181",
            "http://127.0.0.1:5181",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000"
        ]
        if self.CORS_ORIGINS:
            for o in self.CORS_ORIGINS.split(","):
                item = o.strip().rstrip("/")
                if item and item not in origins:
                    origins.append(item)
        return origins


settings = Settings()
