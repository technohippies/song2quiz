"""Application settings loaded from environment variables."""
import os
from dataclasses import dataclass

@dataclass
class Settings:
    """Application settings."""
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

settings = Settings()
