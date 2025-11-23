from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://qca_user:qca_password@db:5432/qca_db"
    API_TITLE: str = "Quantique Compliance Assistant API"
    API_VERSION: str = "1.0.0"
    
    # Security settings
    # ALLOWED_ORIGINS should only include the deployed frontend URL in production
    ALLOWED_ORIGINS: List[str] = [
        "https://ca-frontend-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io",  # Azure DEV
    ]
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # LLM API settings - Multiple providers for flexibility
    LLM_PROVIDER: str = "groq"  # Options: openai, groq, anthropic, ollama
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Groq Settings (Free tier: 30 req/min, 6000 req/day)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Current supported model
    
    # Anthropic settings
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    # Ollama settings (Local, completely free)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Azure AI Search settings
    AZURE_SEARCH_ENABLED: bool = False  # Feature flag - set to True to use Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = "https://qca-search-dev.search.windows.net"
    AZURE_SEARCH_API_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "compliance-knowledge"
    
    # Evidence storage configuration
    EVIDENCE_STORAGE_BACKEND: str = "local"  # Options: local, azure
    EVIDENCE_STORAGE_PATH: str = "/app/storage/evidence"
    EVIDENCE_MAX_FILE_SIZE_MB: int = 25
    EVIDENCE_ALLOWED_EXTENSIONS: List[str] = [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".csv",
        ".ppt",
        ".pptx",
        ".txt",
        ".jpg",
        ".jpeg",
        ".png",
        ".zip"
    ]
    
    # Azure Blob Storage configuration
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_CONTAINER_EVIDENCE: str = "evidence"
    AZURE_STORAGE_CONTAINER_REPORTS: str = "reports"
    
    class Config:
        env_file = ".env"


settings = Settings()
