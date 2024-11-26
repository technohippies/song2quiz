"""Application settings loaded from environment variables."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Settings:
    """Application settings."""
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable is required but not set in .env file")

settings = Settings()
