from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Studium"
    
    # AI Model Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 1000
    CLAUDE_TEMPERATURE: float = 0.7
    
    # Language Configuration
    DEFAULT_LANGUAGE: str = "es"  # Spanish
    SUPPORTED_LANGUAGES: set = {"es", "en"}
    
    # Primary AI Service
    PRIMARY_AI_SERVICE: str = "claude"  # claude, openai
    FALLBACK_SERVICES: list = ["claude", "openai"]
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg"}
    UPLOAD_DIRECTORY: str = "uploads"
    
    # OCR Configuration
    TESSERACT_CMD: Optional[str] = None  # Will use system default
    
    # Vector Store Configuration
    VECTOR_STORE_PATH: str = "vector_store"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Processing Configuration
    MAX_PROCESSING_TIME: int = 30  # seconds
    MAX_FLASHCARDS: int = 10
    MAX_TRIVIA_QUESTIONS: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()