"""
Core configuration module using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database configuration
    database_url: str = "sqlite:///./crm.db"
    
    # API configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Mini-CRM Operator Request Distribution"
    app_name: Optional[str] = None
    
    # Application configuration
    debug: bool = False
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
