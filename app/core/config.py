import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    PROJECT_NAME: str = "Bulk Certificate Generator API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'certificates.db'}")
    
    # Certificate File Storage
    STORAGE_DIR: Path = BASE_DIR / "generated_certificates"
    
    # Ensure storage directory exists
    def __init__(self):
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
