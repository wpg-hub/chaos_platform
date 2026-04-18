import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Chaos Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    DATABASE_URL: str = "postgresql+asyncpg://chaos:chaos123@localhost:5432/chaos_platform"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    CHAOS_CONFIG_PATH: str = "/app/config.yaml"
    CASES_DIR: str = "/app/cases"
    LOGS_DIR: str = "/app/logs"
    REPORTS_DIR: str = "/app/reports"
    
    CORS_ORIGINS: list = ["http://localhost", "http://localhost:80", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
