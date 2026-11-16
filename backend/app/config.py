import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_FILE = os.path.join(BASE_BACKEND_DIR, "phoenix.db")

class Settings(BaseSettings):
    APP_NAME: str = "Phoenix Small Business Portal"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database configuration (SQLite by default, resolves to backend/phoenix.db)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_FILE}")
    
    # Security & JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "phoenix-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Backup Configuration (default to external directory outside application folder)
    DEFAULT_BACKUP_DIR: str = os.getenv(
        "BACKUP_DIR", 
        os.path.abspath(os.path.join(BASE_BACKEND_DIR, "..", "..", "phoenix_backups"))
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
