"""Script to test semantic units analysis with high concurrency."""

import asyncio
import logging
from typing import Any, Dict, Optional, cast

from prefect import flow

from src.tasks.lyrics_analysis.semantic_units import analyze_fragment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@flow(name="test_semantic_units")
async def test_semantic_units(song_id: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """Test semantic units analysis with high concurrency."""
    song_path = f"data/songs/{song_id}"
    logger.info(f"🚀 Starting semantic units analysis for {song_path}")

    result = await analyze_fragment.fn({"text": "Test fragment"}, 1, 1)
    if result is None:
        return None
    return cast(Dict[str, Dict[str, Any]], result)


if __name__ == "__main__":
    # Use a song with lots of lines
    asyncio.run(test_semantic_units("52019"))
