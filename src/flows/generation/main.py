"""Main flow for lyrics generation."""
import logging

from prefect import flow

from src.tasks.lyrics_analysis.semantic_units import analyze_song_semantic_units
from src.tasks.lyrics_analysis.vocabulary import analyze_song_vocabulary

logger = logging.getLogger(__name__)

@flow(name="lyrics_generation")
async def main(song_path: str) -> bool:
    """Main flow for lyrics generation."""
    try:
        # Run vocabulary analysis with parallel processing
        vocab_results = await analyze_song_vocabulary(song_path)
        if not vocab_results:
            logger.error("❌ Vocabulary analysis failed")
            return False

        # Run semantic units analysis
        semantic_results = await analyze_song_semantic_units(song_path)
        if not semantic_results:
            logger.error("❌ Semantic units analysis failed")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Error in lyrics generation flow: {str(e)}")
        return False
