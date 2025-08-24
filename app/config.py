import os
from pydantic_settings import BaseSettings
from typing import Optional
from datetime import datetime, timezone

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "AI Product Council API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # AI Configuration
    google_api_key: str
    openai_api_key: Optional[str] = None
    
    # Database Configuration
    database_url: str = "sqlite:///./ai_council.db"
    
    # Redis Configuration (for caching and rate limiting)
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
