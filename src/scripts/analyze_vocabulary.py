"""Script to run vocabulary analysis on a song."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from src.services.langfuse import create_llm_trace, create_song_session_id
from src.tasks.lyrics_analysis.vocabulary import analyze_song_vocabulary

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


async def analyze_song(song_path: Path) -> Dict[str, Any]:
    """Analyze vocabulary in a song's lyrics."""
    try:
        logger.info("\n" + "=" * 50 + " Starting Vocabulary Analysis " + "=" * 50)
        logger.info(f"📂 Song path: {song_path}")

        if not Path(song_path).exists():
            logger.error(f"❌ Song directory does not exist: {song_path}")
            sys.exit(1)

        lyrics_file = Path(song_path, "lyrics_with_annotations.json")
        if not lyrics_file.exists():
            logger.error(f"❌ No lyrics file found at {lyrics_file}")
            sys.exit(1)

        # Load song metadata
        with open(lyrics_file, "r") as f:
            lyrics_data = json.load(f)
            song_id = lyrics_data.get("song_id")
            artist = lyrics_data.get("artist")
            song = lyrics_data.get("title")

        # Create session ID for tracking
        session_id = create_song_session_id(
            song_id=song_id, artist=artist, song=song, pipeline_step="vocabulary"
        )

        result = await analyze_song_vocabulary(str(song_path))

        if result and isinstance(result, dict):
            # Track LLM usage for vocabulary analysis
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

            logger.info("\n✅ Analysis completed successfully")
            logger.info("\n📊 Analysis Results:")
            logger.info(json.dumps(result, indent=2))
            return {"success": True, "result": result}
        else:
            logger.error("\n❌ Vocabulary analysis failed - no results returned")
            return {"success": False, "error": "Analysis failed - no results returned"}

    except Exception as e:
        logger.error(f"❌ Error running analysis: {str(e)}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.scripts.analyze_vocabulary <song_id>")
        print("Example: python -m src.scripts.analyze_vocabulary 52019")
        sys.exit(1)

    song_id = sys.argv[1]
    song_path = Path(f"data/songs/{song_id}")
    asyncio.run(analyze_song(song_path))
