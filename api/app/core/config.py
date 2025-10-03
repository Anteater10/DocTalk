import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load values from .env into environment
load_dotenv()

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/doctalk")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()