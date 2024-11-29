"""Langfuse service for LLM observability."""

import logging

import httpx
from langfuse import Langfuse

from src.constants.api import MODEL_COSTS
from src.utils.settings import settings

logger = logging.getLogger(__name__)


def register_models():
    """Register OpenRouter models with Langfuse."""
    try:
        client = httpx.Client(
            base_url=settings.LANGFUSE_HOST,
            headers={
                "Authorization": f"Bearer {settings.LANGFUSE_SECRET_KEY}",
                "Content-Type": "application/json",
            },
        )

        # Register Gemini Flash
        client.post(
            "/api/public/models",
            json={
                "name": "gemini-flash",
                "match_pattern": "(?i)^(google/gemini-flash-1.5-8b)(@[a-zA-Z0-9]+)?$",
                "input_price": MODEL_COSTS["google/gemini-flash-1.5-8b"]["input_cost"],
                "output_price": MODEL_COSTS["google/gemini-flash-1.5-8b"][
                    "output_cost"
                ],
                "unit": "TOKENS",
                "tokenizer": {
                    "type": "openai",
                    "model": "gpt-3.5-turbo",
                    "tokensPerMessage": 3,
                    "tokensPerName": 1,
                },
            },
        )

        # Register Nemo
        client.post(
            "/api/public/models",
            json={
                "name": "nemo",
                "match_pattern": "(?i)^(nvidia/llama-3.1-nemotron-70b-instruct)(@[a-zA-Z0-9]+)?$",
                "input_price": MODEL_COSTS["nvidia/llama-3.1-nemotron-70b-instruct"][
                    "input_cost"
                ],
                "output_price": MODEL_COSTS["nvidia/llama-3.1-nemotron-70b-instruct"][
                    "output_cost"
                ],
                "unit": "TOKENS",
                "tokenizer": {
                    "type": "openai",
                    "model": "gpt-3.5-turbo",
                    "tokensPerMessage": 3,
                    "tokensPerName": 1,
                },
            },
        )

        logger.info("✓ OpenRouter models registered with Langfuse")

    except Exception as e:
        logger.error(f"❌ Failed to register models: {str(e)}")


try:
    logger.debug("Initializing Langfuse...")
    langfuse = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
        debug=True,
    )
    register_models()  # Register models on startup
    logger.info("✓ Langfuse initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Langfuse: {str(e)}")
    logger.exception("Full traceback:")
    raise
