"""Main generation flow."""
import json
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from prefect import flow, task

from src.tasks.lyrics_analysis.vocabulary import analyze_vocabulary_batch
from src.constants.lyrics_analysis.vocabulary import VocabularyEntry

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def find_song_id(artist: str, song: str) -> Optional[str]:
    """Find song ID from artist and song name."""
    try:
        # Load songs.json which contains the mapping
        with open("data/songs.json", "r") as f:
            songs = json.load(f)
            
        # Look for matching song in list
        for song_data in songs:
            if song_data.get("artist_name", "").lower() == artist.lower() and \
               song_data.get("song_name", "").lower() == song.lower():
                return str(song_data.get("id"))
                
        print(f"No match found for {artist} - {song}")
        print("Available songs:")
        for song_data in songs:
            print(f"  - {song_data.get('artist_name')} - {song_data.get('song_name')}")
    except FileNotFoundError:
        print("songs.json not found. Please make sure the song is ingested first.")
    except json.JSONDecodeError:
        print("Error reading songs.json. File may be corrupted.")
    
    return None

@task(name="analyze_song_vocabulary")
async def analyze_song_vocabulary(lyrics_path: str, initial_batch_size: int = 5) -> Dict[str, List[VocabularyEntry]]:
    """Analyze vocabulary for all lines in a song."""
    # Load lyrics with annotations
    with open(lyrics_path, 'r') as f:
        lyrics_data = json.load(f)
        logger.debug(f"Loaded lyrics file: {lyrics_path}")
    
    # Extract all lines with text and annotations
    lines_with_text = []
    for line in lyrics_data.get('lyrics', []):
        if line.get('text'):
            # Create a dictionary with text and annotations
            line_data = {
                'text': line['text'],
                'annotations': []
            }
            
            # Add any annotations for this line
            for annotation in line.get('annotations', []):
                if annotation.get('fragment') and annotation.get('annotation_text'):
                    line_data['annotations'].append({
                        'fragment': annotation['fragment'],
                        'annotation_text': annotation['annotation_text']
                    })
            
            lines_with_text.append(line_data)
            logger.debug(f"Added line with {len(line_data['annotations'])} annotations: {line_data['text'][:50]}...")
    
    if not lines_with_text:
        logger.warning("No lines with text found in lyrics file")
        return {}
    
    logger.info(f"Processing {len(lines_with_text)} lines with annotations")
    
    # Process all lines in parallel batches
    entries = await analyze_vocabulary_batch(
        lines=lines_with_text, 
        initial_batch_size=initial_batch_size
    )
    
    # Group entries by line
    results = {}
    for entry in entries:
        # Find the line this entry came from
        for line_data in lines_with_text:
            if entry.term in line_data['text']:
                if line_data['text'] not in results:
                    results[line_data['text']] = []
                results[line_data['text']].append(entry)
                break
    
    logger.info(f"Found vocabulary entries for {len(results)} lines")
    return results

@flow(name="lyrics_generation")
async def main(song_id: Optional[str] = None, artist: Optional[str] = None, song: Optional[str] = None, batch_size: int = 5) -> None:
    """Run the main generation pipeline."""
    # If song_id not provided, try to find it from artist and song name
    if not song_id and artist and song:
        song_id = find_song_id(artist, song)
        if not song_id:
            print(f"Could not find song ID for {artist} - {song}")
            print("Please make sure the song is ingested first using the ingestion pipeline.")
            return
    
    if not song_id:
        print("Either song_id or both artist and song name must be provided")
        return
        
    # Set up paths
    data_dir = Path("data/songs") / str(song_id)
    lyrics_path = data_dir / "lyrics_with_annotations.json"
    
    if not lyrics_path.exists():
        print(f"Could not find lyrics file at {lyrics_path}")
        print("Please make sure the song is ingested first.")
        return
    
    # Run vocabulary analysis
    print(f"Analyzing vocabulary for song {song_id}...")
    vocab_results = await analyze_song_vocabulary(str(lyrics_path), initial_batch_size=batch_size)
    
    # Save results
    output_path = data_dir / "vocabulary_analysis.json"
    with open(output_path, 'w') as f:
        # Convert VocabularyEntry objects to dictionaries
        serializable_results = {
            line: [entry.dict() for entry in entries]
            for line, entries in vocab_results.items()
        }
        json.dump(serializable_results, f, indent=2)
    
    print(f"Vocabulary analysis complete. Results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run lyrics generation pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--song-id", help="Direct song ID to process")
    group.add_argument("--artist", help="Artist name (must be used with --song)")
    parser.add_argument("--song", help="Song title (required if using --artist)")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of lines to process in parallel")
    
    args = parser.parse_args()
    
    if args.artist and not args.song:
        parser.error("--artist requires --song")
    
    asyncio.run(main(song_id=args.song_id, artist=args.artist, song=args.song, batch_size=args.batch_size))
