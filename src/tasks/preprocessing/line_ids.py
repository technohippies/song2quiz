"""Task for generating deterministic line IDs."""
import json
import logging
from pathlib import Path
import hashlib
from prefect import task

logger = logging.getLogger(__name__)

def get_line_id(text: str) -> str:
    """Generate deterministic ID for a line of text.
    
    Args:
        text: Line text to generate ID for
        
    Returns:
        First 8 characters of SHA-256 hash of text
    """
    return hashlib.sha256(text.encode()).hexdigest()[:8]

@task(name="add_line_ids")
def add_line_ids(song_path: Path) -> bool:
    """Add deterministic IDs to each line in lyrics_with_annotations.json.
    
    Args:
        song_path: Path to song directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        lyrics_path = song_path / "lyrics_with_annotations.json"
        if not lyrics_path.exists():
            logger.error(f"lyrics_with_annotations.json not found at {lyrics_path}")
            return False
            
        # Load existing file
        with open(lyrics_path) as f:
            data = json.load(f)
            
        # Add IDs to each line
        for line in data["lyrics"]:
            line["id"] = get_line_id(line["text"])
            
        # Save updated file
        with open(lyrics_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Successfully added line IDs to {lyrics_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding line IDs: {str(e)}")
        return False
