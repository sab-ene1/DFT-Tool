from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings.
    """
    # API Settings
    api_title: str = "DFT Analysis Tool API"
    api_description: str = "API for analyzing frequency patterns in DFT output"
    api_version: str = "1.0.0"
    
    # CORS Settings
    allow_origins: list[str] = ["http://localhost:3000"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    
    # Clustering Settings
    max_clusters: int = 10
    min_clusters: int = 2
    default_clusters: int = 3
    max_points: int = 1_000_000
    
    # Cache Settings
    cache_size: int = 100
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()
