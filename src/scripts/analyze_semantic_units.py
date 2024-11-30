"""Script to run semantic units analysis on a song."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, cast

from src.flows.generation.main import main
from src.services.langfuse import create_llm_trace, create_song_session_id
from src.utils.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# Log Langfuse status
logger.info("Checking Langfuse configuration:")
logger.info(f"Public key set: {bool(settings.LANGFUSE_PUBLIC_KEY)}")
logger.info(f"Secret key set: {bool(settings.LANGFUSE_SECRET_KEY)}")
logger.info(f"Host: {settings.LANGFUSE_HOST}")


async def analyze_song_semantic_units(song_path: Path) -> Dict[str, Any]:
    """Analyze semantic units in a song's lyrics."""
    try:
        if not Path(song_path).exists():
            logger.error(f"❌ Song directory does not exist: {song_path}")
            sys.exit(1)

        lyrics_file = Path(song_path, "lyrics_with_annotations.json")
        if not lyrics_file.exists():
            logger.error(f"❌ No lyrics file found at {lyrics_file}")
            sys.exit(1)

        # Load song metadata for session ID
        with open(lyrics_file, "r") as f:
            lyrics_data = json.load(f)
            song_id = lyrics_data.get("song_id")
            artist = lyrics_data.get("artist")
            song = lyrics_data.get("title")

        # Create session ID for tracking
        session_id = create_song_session_id(
            song_id=song_id, artist=artist, song=song, pipeline_step="semantic_units"
        )

        raw_result = await main(str(song_path))
        result = cast(Optional[Dict[str, Any]], raw_result)

        if result and isinstance(result, dict):
            # Track LLM usage for each generation step
            for step, data in result.items():
                if isinstance(data, dict) and "prompt" in data and "completion" in data:
                    create_llm_trace(
                        session_id=session_id,
                        model_name=data.get("model", "unknown"),
                        prompt=data["prompt"],
                        completion=data["completion"],
                        input_tokens=data.get("input_tokens", 0),
                        output_tokens=data.get("output_tokens", 0),
                        metadata={"step": step},
                    )

            logger.info("✓ Analysis completed successfully")
            return {"success": True, "result": result}
        else:
            logger.error("❌ Analysis failed")
            return {"success": False, "error": "Analysis failed"}

    except Exception as e:
        logger.error(f"❌ Error running analysis: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.scripts.analyze_semantic_units <song_id>")
        print("Example: python -m src.scripts.analyze_semantic_units 51899")
        sys.exit(1)

    song_id = sys.argv[1]
    asyncio.run(analyze_song_semantic_units(Path(f"data/songs/{song_id}")))
