from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bulk Certificate Generator"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Storage settings
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CERTIFICATES_DIR: Path = BASE_DIR / "storage" / "certificates"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'certificates.db'}"
    
    # Certificate Defaults
    DEFAULT_ISSUER: str = "AEREO Engineering Team"
    DEFAULT_TITLE: str = "Certificate of Achievement"
    DEFAULT_EVENT: str = "Software Engineering Bootcamp"
    
    # Server / Base URL for verification links (e.g. http://localhost:8000)
    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

# Ensure storage directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
