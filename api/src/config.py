from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://qca_user:qca_password@db:5432/qca_db"
    API_TITLE: str = "Quantique Compliance Assistant API"
    API_VERSION: str = "1.0.0"
    
    # Security settings
    ALLOWED_ORIGINS: List[str] = ["*"]  # ⚠️ DEVELOPMENT ONLY - restrict for production
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # OpenAI API settings
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"


settings = Settings()
