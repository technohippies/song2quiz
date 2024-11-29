"""Script to run semantic units analysis on a song."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from src.flows.generation.main import main
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

        if not Path(song_path, "lyrics_with_annotations.json").exists():
            logger.error(
                f"❌ No lyrics file found at {song_path}/lyrics_with_annotations.json"
            )
            sys.exit(1)

        result = await main(str(song_path))
        if result:
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
