import os
from typing import Optional
from pathlib import Path

# Load environment variables manually as a reliable fallback
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

try:
    from pydantic_settings import BaseSettings
    class Settings(BaseSettings):
        PROJECT_NAME: str = "Hệ thống Quản lý Bảo hiểm Tích hợp AI (InsurTech AI)"
        VERSION: str = "1.0.0"
        API_V1_STR: str = "/api/v1"
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        AI_MOCK_MODE: bool = os.getenv("AI_MOCK_MODE", "True").lower() in ("true", "1", "yes")
        AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gpt-4o-mini")
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./insurtech_database.db")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "insurtech_secret_jwt_key_2026_very_secure")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

        class Config:
            env_file = ".env"
            extra = "ignore"

    settings = Settings()
except Exception:
    class SimpleSettings:
        PROJECT_NAME: str = "Hệ thống Quản lý Bảo hiểm Tích hợp AI (InsurTech AI)"
        VERSION: str = "1.0.0"
        API_V1_STR: str = "/api/v1"
        OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        AI_MOCK_MODE: bool = os.getenv("AI_MOCK_MODE", "True").lower() in ("true", "1", "yes")
        AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gpt-4o-mini")
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./insurtech_database.db")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "insurtech_secret_jwt_key_2026_very_secure")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    settings = SimpleSettings()
