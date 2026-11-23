from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings and configuration."""

    DATABASE_URL: str = "mysql+pymysql://jyohar:jyohar_pass@localhost:3306/jyohar_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "jyohar-files"
    MINIO_SECURE: bool = False
    ENVIRONMENT: str = "development"
    OTP_STUB_MODE: bool = True
    MSG91_API_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    MSG91_OTP_VARIABLE: str = "VAR1"
    MSG91_COUNTRY_CODE: str = "91"
    COMPANY_NAME: str = "Jyohar Tech × Innollege"
    COMPANY_TIMEZONE: str = "Asia/Kolkata"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 100

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
