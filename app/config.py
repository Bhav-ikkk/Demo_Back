import os
from typing import Optional, List

class Settings:
    # API Configuration
    app_name: str = "AI Product Council API"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # AI Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ai_council.db")
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_recycle: int = 300
    database_pool_pre_ping: bool = True
    
    # Redis Configuration (for caching and rate limiting)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_max_connections: int = 10
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    access_token_expire_minutes: int = 30
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    
    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
    rate_limit_storage: str = "memory"  # memory or redis
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = "json"
    
    # Performance
    max_concurrent_requests: int = 100
    request_timeout: int = 300  # 5 minutes
    background_task_timeout: int = 600  # 10 minutes
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Health Check
    health_check_timeout: int = 30

settings = Settings()
