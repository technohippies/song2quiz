import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict

from prefect import flow, get_run_logger, task

from ...services.genius import GeniusAPI
from ...services.lrclib import LRCLibAPI
from ...utils.io.paths import ensure_song_dir, get_songs_catalog_path


@task(name="Update Song Catalog")
def update_song_catalog(results: Dict[str, Any], base_path: str) -> None:
    """Update the central song catalog with new song metadata."""
    catalog_path = get_songs_catalog_path(base_path)

    # Create data directory if it doesn't exist
    catalog_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize empty catalog if file doesn't exist
    if not catalog_path.exists():
        with open(catalog_path, "w") as f:
            json.dump([], f, indent=4)

    # Read existing catalog
    with open(catalog_path, "r") as f:
        try:
            catalog = json.load(f)
        except json.JSONDecodeError:
            catalog = []

    # Check if song already exists in catalog by song ID
    song_exists = any(song.get("id") == results["id"] for song in catalog)

    if not song_exists:
        # Only append if song doesn't exist
        catalog.append(results)

        # Write updated catalog
        with open(catalog_path, "w") as f:
            json.dump(catalog, f, indent=4)


@task(name="Copy to Songs Directory")
def copy_to_songs_dir(song_path: str, base_path: str) -> None:
    """Copy song data to the songs directory."""
    logger = get_run_logger()
    if not song_path:
        logger.warning("No song path provided, skipping songs directory copy")
        return

    songs_dir = Path(base_path) / "songs"
    songs_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(song_path)
    dest_path = songs_dir / source_path.name

    # Copy the entire song directory
    if source_path.exists():
        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        logger.info(f"Copied song data to songs directory: {dest_path}")
    else:
        logger.error(f"Source path does not exist: {source_path}")


@task
def ensure_song_directory(base_path: str) -> str:
    """Ensure the songs directory exists and return its path."""
    songs_dir = os.path.join(base_path, "songs")
    os.makedirs(songs_dir, exist_ok=True)
    return songs_dir


@flow(name="Song Ingestion")
def song_ingestion_flow(
    song_name: str,
    artist_name: str,
    base_path: str = str(Path(__file__).parent.parent.parent.parent),
) -> Dict[str, Any]:
    """Ingest a song into the system."""
    logger = get_run_logger()
    logger.info(f"Starting ingestion for {song_name} by {artist_name}")

    # Initialize APIs
    genius = GeniusAPI()
    lrclib = LRCLibAPI()

    # Get metadata first
    logger.info("Fetching song metadata from Genius")
    metadata = genius.search_song(song_name, artist_name)
    if not metadata:
        logger.error("No metadata found for song")
        return {"song_path": None}

    # Use path utilities to create song directory using ID
    song_path = ensure_song_dir(base_path, metadata.id)

    # Save metadata
    metadata_path = song_path / "genius_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

    results = {
        "song_path": str(song_path),
        "album_name": metadata.album.name if metadata.album else "singles",
        "album_id": metadata.album.id if metadata.album else None,
        "annotations_path": None,
        "lyrics_path": None,
        "song_name": song_name,
        "artist_name": artist_name,
        "primary_artist_names": metadata.primary_artist_names,
        "id": metadata.id,
    }

    # Get annotations
    annotations = genius.get_song_annotations(metadata.id)
    if annotations:
        annotations_path = song_path / "genius_annotations.json"
        with open(annotations_path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, ensure_ascii=False, indent=2)
        results["annotations_path"] = str(annotations_path)

    # Get lyrics
    lyrics = lrclib.search_lyrics(song_name, artist_name)
    if lyrics:
        lyrics_path = song_path / "lyrics.json"
        with open(lyrics_path, "w", encoding="utf-8") as f:
            json.dump(lyrics, f, ensure_ascii=False, indent=2)
        results["lyrics_path"] = str(lyrics_path)

    # Update catalog using the same base_path
    update_song_catalog(results, base_path)

    logger.info(f"Successfully completed ingestion for {song_name}")
    return results
