"""Script to run vocabulary analysis on a song."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from src.flows.generation.main import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


async def analyze_song_vocabulary(song_path: Path) -> Dict[str, Any]:
    """Analyze vocabulary in a song's lyrics."""
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
            logger.info("✓ Vocabulary analysis completed successfully")
            logger.info(f"✓ Results saved to {song_path}/vocabulary_analysis.json")
            return {"success": True, "result": result}
        else:
            logger.error("❌ Vocabulary analysis failed")
            return {"success": False, "error": "Analysis failed"}
    except Exception as e:
        logger.error(f"❌ Error running analysis: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.scripts.analyze_vocabulary <song_id>")
        print("Example: python -m src.scripts.analyze_vocabulary 51899")
        sys.exit(1)

    song_id = sys.argv[1]
    asyncio.run(analyze_song_vocabulary(Path(f"data/songs/{song_id}")))
