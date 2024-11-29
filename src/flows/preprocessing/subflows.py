"""Preprocessing subflows for cleaning and matching song annotations."""

import json
import logging
from pathlib import Path
from typing import Optional, Union

from prefect import flow

from src.tasks.lyrics_analysis.parentheticals import analyze_parentheticals
from src.tasks.preprocessing.line_ids import add_line_ids
from src.tasks.preprocessing.match_lyrics_to_annotations import (
    match_lyrics_with_annotations,
)
from src.tasks.preprocessing.text_cleaning import process_annotations
from src.utils.io.paths import get_song_dir

logger = logging.getLogger(__name__)


@flow(name="process_song_annotations")
def process_song_annotations_flow(
    song_id: int, base_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Flow to process and match song annotations.

    Args:
        song_id: Genius song ID
        base_path: Base project path (defaults to current directory)

    Flow steps:
        1. Clean and standardize annotations
        2. Match annotations with lyrics
        3. Add deterministic line IDs
        4. Analyze parentheticals

    Returns:
        bool: True if all steps completed successfully
    """
    if base_path is None:
        base_path = Path.cwd()
    song_dir = get_song_dir(base_path, song_id)
    logger.info(f"Starting annotation processing flow for song {song_id}")

    # Step 1: Clean annotations
    clean_result = process_annotations(song_dir)
    if not clean_result:
        logger.error("Failed to clean annotations")
        return False

    # Step 2: Match with lyrics
    match_result = match_lyrics_with_annotations(song_dir)
    if not match_result:
        logger.error("Failed to match annotations with lyrics")
        return False

    # Step 3: Add line IDs
    id_result = add_line_ids(song_dir)
    if not id_result:
        logger.error("Failed to add line IDs")
        return False

    # Step 4: Analyze parentheticals
    try:
        # Load lyrics with IDs
        lyrics_path = song_dir / "lyrics_with_annotations.json"
        with open(lyrics_path) as f:
            lyrics_data = json.load(f)

        # Analyze each line and only keep ones with parentheticals
        results = []
        for line in lyrics_data["lyrics"]:
            result = analyze_parentheticals(line["text"])
            if result["parentheticals"]:  # Only include if it has parentheticals
                results.append(
                    {
                        "id": line["id"],
                        "timestamp": line["timestamp"],
                        "text": line["text"],
                        "line_without_parentheses": result["line_without_parentheses"],
                        "parentheticals": result["parentheticals"],
                    }
                )

        # Save results
        output_path = song_dir / "parentheticals_analysis.json"
        with open(output_path, "w") as f:
            json.dump(
                {
                    "lines_with_parentheticals": results,
                    "total_parenthetical_lines": len(results),
                },
                f,
                indent=2,
            )

        logger.info(f"✓ Found {len(results)} lines with parentheticals")

    except Exception as e:
        logger.error(f"Failed to analyze parentheticals: {str(e)}")
        return False

    logger.info(f"Successfully processed annotations for song {song_id}")
    return True


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python subflows.py <song_id>")
        sys.exit(1)

    song_id = int(sys.argv[1])
    process_song_annotations_flow(song_id)
