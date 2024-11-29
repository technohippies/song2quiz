"""Task for matching lyrics with their corresponding annotations."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prefect import task

from src.utils.io.paths import get_song_dir

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def find_matching_annotation(
    text: str, annotations: List[Dict]
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Find the annotation that best matches the given text.
    Returns (annotation, match_type) where match_type is 'exact', 'fragment', or 'line'
    """
    if not text or text.strip() in ["[", "]"] or text.strip().isdigit():
        return None, None

    text = text.lower().strip()

    # Try exact match first
    for ann in annotations:
        fragment = ann["fragment"].lower().strip()
        if fragment == text:
            logger.debug(f"Found exact match: '{text[:30]}...'")
            return ann, "exact"

    # Try matching fragment within line
    for ann in annotations:
        fragment = ann["fragment"].lower().strip()
        # Skip very short fragments and empty fragments
        if len(fragment) > 3 and fragment in text:
            logger.debug(
                f"Found fragment '{fragment[:30]}...' in line '{text[:30]}...'"
            )
            return ann, "fragment"

    # Try matching line within fragment
    for ann in annotations:
        fragment = ann["fragment"].lower().strip()
        # Skip very short lines to avoid false matches
        if len(text) > 3 and text in fragment:
            logger.debug(
                f"Found line '{text[:30]}...' in fragment '{fragment[:30]}...'"
            )
            return ann, "line"

    logger.debug(f"No match found for '{text[:30]}...'")
    return None, None


def get_line_id(text: str) -> str:
    """Generate deterministic ID for a line of text."""
    # Use SHA-256 to generate a stable hash, taking first 8 chars
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def update_song_processing_metadata(
    song_id: int, base_path: Path, processing_data: Dict
) -> bool:
    """
    Update the processing metadata for a song in songs.json.

    Args:
        song_id: The ID of the song to update
        base_path: Base project directory
        processing_data: Dictionary containing processing metadata

    Returns:
        True if successful, False otherwise
    """
    try:
        from src.utils.io.paths import get_songs_catalog_path

        songs_path = get_songs_catalog_path(base_path)

        # Read current songs.json
        with open(songs_path) as f:
            songs = json.load(f)

        # Find and update the target song
        for song in songs:
            if song["id"] == song_id:
                # Initialize processing field if it doesn't exist
                if "processing" not in song:
                    song["processing"] = {}

                # Update with new processing data
                song["processing"].update(processing_data)
                break

        # Write back to songs.json
        with open(songs_path, "w", encoding="utf-8") as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        logger.error(f"Error updating song processing metadata: {str(e)}")
        return False


@task(name="match_lyrics_annotations")
def match_lyrics_with_annotations(song_path: Path) -> bool:
    """Match lyrics with their cleaned annotations."""
    try:
        logger.info(f"Starting lyrics-annotation matching for {song_path.name}")

        # Load lyrics
        lyrics_path = song_path / "lyrics.json"
        if not lyrics_path.exists():
            logger.error(f"Lyrics not found at {lyrics_path}")
            return False

        with open(lyrics_path) as f:
            lyrics_data: Dict[str, Any] = json.load(f)

        # Load cleaned annotations
        annotations_path = song_path / "annotations_cleaned.json"
        if not annotations_path.exists():
            logger.error(f"Cleaned annotations not found at {annotations_path}")
            return False

        with open(annotations_path) as f:
            annotations: List[Dict[str, Any]] = json.load(f)

        # Track matches by type
        matches: Dict[str, Any] = {
            "total": 0,
            "by_type": {"exact": 0, "fragment": 0, "line": 0}
        }

        # Track which annotations have been matched
        matched_annotation_ids: set[str] = set()
        lyrics_with_annotations: List[Dict[str, Any]] = []

        timestamped_lines = lyrics_data.get("timestamped_lines", [])
        if not isinstance(timestamped_lines, list):
            logger.error("Invalid timestamped_lines format")
            return False

        for line in timestamped_lines:
            if not isinstance(line, dict):
                continue

            line_text = line.get("text", "").strip()
            annotation, match_type = find_matching_annotation(line_text, annotations)

            if annotation:
                ann_id = annotation["id"]
                if ann_id not in matched_annotation_ids:
                    matched_annotation_ids.add(ann_id)
                    matches["total"] += 1
                    if match_type:
                        matches["by_type"][match_type] += 1

            annotated_line = {
                "id": get_line_id(line_text),
                "timestamp": line.get("timestamp"),
                "text": line_text,
                "annotation": annotation["annotation_text"] if annotation else None,
                "fragment": annotation["fragment"] if annotation else None,
                "annotation_id": annotation["id"] if annotation else None,
            }
            lyrics_with_annotations.append(annotated_line)

        logger.info("Match summary:")
        logger.info(f"- Total annotations: {len(annotations)}")
        logger.info(f"- Total matches: {matches['total']}")
        logger.info("- By type:")
        logger.info(f"  - Exact: {matches['by_type']['exact']}")
        logger.info(f"  - Fragment in line: {matches['by_type']['fragment']}")
        logger.info(f"  - Line in fragment: {matches['by_type']['line']}")

        # Save matched lyrics and annotations
        output = {
            "lyrics_source": lyrics_data.get("source"),
            "annotations_source": "genius",
            "has_timestamps": True,
            "stats": {
                "total_lyrics_lines": len(lyrics_data.get("timestamped_lines", [])),
                "total_annotations": len(annotations),
                "matches": matches,
            },
            "lyrics": lyrics_with_annotations,
        }

        output_path = song_path / "lyrics_with_annotations.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        # Update processing metadata in songs.json
        song_id = int(song_path.name)  # Song ID is the directory name
        processing_data = {
            "lyrics": {
                "source": lyrics_data.get("source"),
                "has_timestamps": True,
                "total_lines": len(lyrics_data.get("timestamped_lines", [])),
                "processed_at": datetime.now().isoformat(),
            },
            "annotations": {
                "source": "genius",
                "total_annotations": len(annotations),
                "matches": matches,
                "processed_at": datetime.now().isoformat(),
            },
        }

        if not update_song_processing_metadata(
            song_id, song_path.parent.parent, processing_data
        ):
            logger.warning("Failed to update processing metadata in songs.json")

        logger.info(f"Successfully saved matches to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error matching lyrics with annotations: {str(e)}")
        return False


# CLI for testing
if __name__ == "__main__":
    import sys

    from src.utils.io.paths import get_song_dir

    # Set debug logging when running directly
    logger.setLevel(logging.DEBUG)

    if len(sys.argv) != 2:
        print(
            "Usage: python -m src.tasks.preprocessing.match_lyrics_to_annotations <song_id>"
        )
        sys.exit(1)

    song_id = int(sys.argv[1])
    song_dir = get_song_dir(Path.cwd(), song_id)

    if match_lyrics_with_annotations.fn(song_dir):
        print("✨ Successfully matched lyrics with annotations")
    else:
        print("❌ Failed to match lyrics with annotations")
