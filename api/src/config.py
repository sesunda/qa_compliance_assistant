from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://qca_user:qca_password@db:5432/qca_db"
    API_TITLE: str = "Quantique Compliance Assistant API"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"


settings = Settings()
