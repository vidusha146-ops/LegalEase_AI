import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings for LegalEase AI.
    Loads configurations from environment variables or .env file.
    Supports PostgreSQL production with seamless SQLite async fallback.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "LegalEase AI – Intelligent Legal Decision Support System"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    # Default to async SQLite for development; easily switched to PostgreSQL via DATABASE_URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./legalease.db"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Artificial Intelligence
    GEMINI_API_KEY: str = ""

    # Document & Vector Storage
    CHROMA_PERSIST_DIRECTORY: str = "./backend/chroma_data"
    UPLOAD_DIR: str = "./backend/storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 15


settings = Settings()
