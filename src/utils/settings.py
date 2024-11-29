"""Application settings loaded from environment variables."""

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings."""

    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    def __post_init__(self) -> None:
        if not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set")
        if not self.LANGFUSE_PUBLIC_KEY:
            logger.warning("LANGFUSE_PUBLIC_KEY not set")
        if not self.LANGFUSE_SECRET_KEY:
            logger.warning("LANGFUSE_SECRET_KEY not set")


settings = Settings()
