"""Script to run semantic units analysis on a song."""
import asyncio
import logging
import sys
from pathlib import Path

from src.flows.generation.main import main
from src.utils.io.paths import get_song_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

async def run_analysis(song_id: str):
    """Run semantic units analysis on a song."""
    try:
        song_path = get_song_dir(".", song_id)
        if not song_path.exists():
            logger.error(f"❌ Song directory does not exist: {song_path}")
            sys.exit(1)
            
        if not (song_path / "lyrics_with_annotations.json").exists():
            logger.error(f"❌ No lyrics with annotations found at {song_path}/lyrics_with_annotations.json")
            sys.exit(1)
            
        result = await main(str(song_path))
        if result:
            logger.info("✓ Semantic units analysis completed successfully")
            logger.info(f"✓ Results saved to {song_path}/semantic_units_analysis.json")
        else:
            logger.error("❌ Semantic units analysis failed")
    except Exception as e:
        logger.error(f"❌ Error running analysis: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m src.scripts.analyze_semantic_units <song_id>")
        print("Example: python -m src.scripts.analyze_semantic_units 51899")
        sys.exit(1)
        
    song_id = sys.argv[1]
    asyncio.run(run_analysis(song_id))
