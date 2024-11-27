"""Script to test semantic units analysis with high concurrency."""
import asyncio
import logging
from pathlib import Path
from prefect import flow

from src.tasks.lyrics_analysis.semantic_units import analyze_song_semantic_units

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@flow(name="test_semantic_units")
async def test_semantic_units(song_id: str):
    """Test semantic units analysis with high concurrency."""
    song_path = f"data/songs/{song_id}"
    logger.info(f"🚀 Starting semantic units analysis for {song_path}")
    
    result = await analyze_song_semantic_units(song_path)
    if result:
        logger.info("✅ Analysis complete!")
        logger.info(f"📊 Processed {len(result['semantic_units_analysis'])} units")
    return result

if __name__ == "__main__":
    # Use a song with lots of lines
    asyncio.run(test_semantic_units("52019")) 