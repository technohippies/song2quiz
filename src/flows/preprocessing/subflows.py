"""Preprocessing subflows for cleaning and matching song annotations."""
from pathlib import Path
from typing import Union
import logging

from prefect import flow

from src.tasks.preprocessing.text_cleaning import process_annotations
from src.tasks.preprocessing.match_lyrics_to_annotations import match_lyrics_with_annotations
from src.utils.io.paths import get_song_dir

logger = logging.getLogger(__name__)

@flow(name="process_song_annotations")
def process_song_annotations_flow(song_id: int, base_path: Union[str, Path] = Path.cwd()) -> bool:
    """
    Flow to process and match song annotations.
    
    Args:
        song_id: Genius song ID
        base_path: Base project path (defaults to current directory)
        
    Flow steps:
        1. Clean and standardize annotations
        2. Match annotations with lyrics
        
    Returns:
        bool: True if all steps completed successfully
    """
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
        
    logger.info(f"Successfully processed annotations for song {song_id}")
    return True

# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python -m src.flows.preprocessing.subflows <song_id>")
        sys.exit(1)
        
    song_id = int(sys.argv[1])
    if process_song_annotations_flow(song_id):
        print("✨ Successfully processed song annotations")
    else:
        print("❌ Failed to process song annotations")
