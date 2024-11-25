"""Task for matching lyrics with their corresponding annotations."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from prefect import task

from src.utils.io.paths import get_song_dir

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def find_matching_annotation(text: str, annotations: List[Dict]) -> Optional[Dict]:
    """Find the annotation that best matches the given text."""
    if not text or text.strip() in ['[', ']'] or text.strip().isdigit():
        return None
        
    text = text.lower().strip()
    
    # Try exact match first
    for ann in annotations:
        fragment = ann['fragment'].lower().strip()
        if fragment == text:
            logger.debug(f"Found exact match: '{text[:30]}...'")
            return ann
            
    # Try matching fragment within line
    for ann in annotations:
        fragment = ann['fragment'].lower().strip()
        # Skip very short fragments and empty fragments
        if len(fragment) > 3 and fragment in text:
            logger.debug(f"Found fragment '{fragment[:30]}...' in line '{text[:30]}...'")
            return ann
            
    # Try matching line within fragment
    for ann in annotations:
        fragment = ann['fragment'].lower().strip()
        # Skip very short lines to avoid false matches
        if len(text) > 3 and text in fragment:
            logger.debug(f"Found line '{text[:30]}...' in fragment '{fragment[:30]}...'")
            return ann
            
    logger.debug(f"No match found for '{text[:30]}...'")
    return None

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
            lyrics_data = json.load(f)
        logger.info(f"Loaded {len(lyrics_data.get('timestamped_lines', []))} lyrics lines")
            
        # Load cleaned annotations
        annotations_path = song_path / "annotations_cleaned.json"
        if not annotations_path.exists():
            logger.error(f"Cleaned annotations not found at {annotations_path}")
            return False
            
        with open(annotations_path) as f:
            annotations = json.load(f)
        logger.info(f"Loaded {len(annotations)} annotations")
            
        # Match annotations to timestamped lyrics lines
        lyrics_with_annotations = []
        matches_found = 0
        exact_matches = 0
        fragment_matches = 0
        line_matches = 0
        
        for line in lyrics_data.get('timestamped_lines', []):
            line_text = line['text'].strip()
            annotation = find_matching_annotation(line_text, annotations)
            
            if annotation:
                matches_found += 1
                if annotation['fragment'].lower().strip() == line_text.lower().strip():
                    exact_matches += 1
                elif annotation['fragment'].lower().strip() in line_text.lower():
                    fragment_matches += 1
                else:
                    line_matches += 1
            
            annotated_line = {
                "timestamp": line['timestamp'],
                "text": line_text,
                "annotation": annotation['annotation_text'] if annotation else None,
                "fragment": annotation['fragment'] if annotation else None,
                "annotation_id": annotation['id'] if annotation else None
            }
            lyrics_with_annotations.append(annotated_line)
            
        logger.info(f"Match summary:")
        logger.info(f"- Total matches: {matches_found}/{len(lyrics_with_annotations)} lines")
        logger.info(f"- Exact matches: {exact_matches}")
        logger.info(f"- Fragment in line matches: {fragment_matches}")
        logger.info(f"- Line in fragment matches: {line_matches}")
        
        # Save matched lyrics and annotations
        output = {
            "source": lyrics_data.get('source'),
            "match_score": lyrics_data.get('match_score'),
            "has_timestamps": True,
            "lyrics": lyrics_with_annotations
        }
        
        output_path = song_path / "lyrics_with_annotations.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
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
        print("Usage: python -m src.tasks.preprocessing.match_lyrics_to_annotations <song_id>")
        sys.exit(1)
        
    song_id = int(sys.argv[1])
    song_dir = get_song_dir(Path.cwd(), song_id)
    
    if match_lyrics_with_annotations.fn(song_dir):
        print("✨ Successfully matched lyrics with annotations")
    else:
        print("❌ Failed to match lyrics with annotations")
