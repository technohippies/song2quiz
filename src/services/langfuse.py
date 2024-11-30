"""Langfuse service for LLM observability."""

import logging
import uuid
from datetime import datetime
from typing import Optional

import httpx
from langfuse import Langfuse

from src.constants.api import MODEL_COSTS
from src.utils.settings import settings

logger = logging.getLogger(__name__)


def create_song_session_id(
    song_id: Optional[str] = None,
    artist: Optional[str] = None,
    song: Optional[str] = None,
    pipeline_step: Optional[str] = None,
) -> str:
    """Create a unique session ID for each pipeline run.

    Args:
        song_id: The Genius song ID if available
        artist: Artist name as fallback
        song: Song title as fallback
        pipeline_step: Current pipeline step (ingest, preprocess, etc.)

    Returns:
        A unique session ID string including timestamp and run ID
    """
    # Create base song identifier
    if song_id:
        song_identifier = str(song_id)
    elif artist and song:
        song_identifier = (
            f"{artist.lower().replace(' ', '_')}_{song.lower().replace(' ', '_')}"
        )
    else:
        raise ValueError("Either song_id or both artist and song must be provided")

    # Create unique run components
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    step = pipeline_step or "all"

    return f"song_pipeline_{song_identifier}_{step}_{timestamp}_{run_id}"


def register_models() -> None:
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


def create_llm_trace(
    session_id: str,
    model_name: str,
    prompt: str,
    completion: str,
    input_tokens: int,
    output_tokens: int,
    metadata: Optional[dict] = None,
) -> None:
    """Create a Langfuse trace for an LLM call with token tracking.

    Args:
        session_id: Unique session identifier
        model_name: Name of the LLM model used
        prompt: Input prompt text
        completion: Model completion/response
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        metadata: Optional additional metadata
    """
    try:
        trace = langfuse.trace(
            id=session_id,
            name=f"llm_trace_{model_name}",
            metadata=metadata or {},
        )

        generation = trace.generation(
            name=f"{model_name}_call",
            model=model_name,
            prompt=prompt,
            completion=completion,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata=metadata or {},
        )

        generation.end()  # End the generation span
        trace.end()  # End the trace

        logger.info(
            f"✓ Logged LLM usage to Langfuse - Model: {model_name}, "
            f"Input tokens: {input_tokens}, Output tokens: {output_tokens}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to log to Langfuse: {str(e)}")


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
