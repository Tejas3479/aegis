from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Pydantic BaseSettings loading system configuration variables.
    """
    APP_NAME: str = "Aegis Triage OS"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    SUPABASE_URL: str
    SUPABASE_KEY: str
    POSTGRES_PRISMA_URL: Optional[str] = None
    
    # AI
    GOOGLE_GENAI_API_KEY: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
