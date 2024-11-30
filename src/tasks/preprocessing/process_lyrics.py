"""Task for processing lyrics into the expected format."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from prefect import task

from src.models.api.lrclib import LRCLibLyrics

logger = logging.getLogger(__name__)


@task(name="process_lyrics")
def process_lyrics(song_path: Path) -> bool:
    """Process lyrics from LRCLib format to the expected format for matching."""
    try:
        # Load raw lyrics
        lyrics_path = song_path / "lyrics.json"
        if not lyrics_path.exists():
            logger.error(f"Lyrics not found at {lyrics_path}")
            return False

        with open(lyrics_path) as f:
            raw_lyrics: Dict[str, Any] = json.load(f)

        # Convert to LRCLibLyrics object using synced lyrics
        synced_lyrics = raw_lyrics.get("syncedLyrics", "")
        plain_lyrics = raw_lyrics.get("plainLyrics", "")
        if not synced_lyrics:
            logger.error("No synced lyrics found in lyrics.json")
            return False

        lyrics = LRCLibLyrics.from_synced_lyrics(synced_lyrics, plain_lyrics)

        # Save processed lyrics
        processed_path = song_path / "lyrics_processed.json"
        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "source": lyrics.source,
                    "has_timestamps": lyrics.has_timestamps,
                    "timestamped_lines": [
                        line.to_dict() for line in lyrics.timestamped_lines
                    ],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"Successfully processed lyrics to {processed_path}")
        return True

    except Exception as e:
        logger.error(f"Error processing lyrics: {str(e)}")
        return False
