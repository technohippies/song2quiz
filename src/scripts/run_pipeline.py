"""Run the complete pipeline for a song."""
import argparse
import logging
from pathlib import Path
import asyncio
from typing import Optional

import src.flows.ingestion.subflows
import src.flows.preprocessing.subflows
import src.flows.generation.main

logger = logging.getLogger(__name__)

def find_song_id(artist: str, song: str) -> Optional[str]:
    """Find song ID from artist and song name."""
    import json
    
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

def run_pipeline(
    artist: Optional[str] = None,
    song: Optional[str] = None,
    song_id: Optional[str] = None,
    steps: str = "all",
    batch_size: int = 15,
    max_retries: int = 3
) -> None:
    """Run the complete pipeline for a song.
    
    Args:
        artist: Artist name (required for ingestion)
        song: Song title (required for ingestion)
        song_id: Genius song ID (can be provided instead of artist/song)
        steps: Pipeline steps to run ("all", "ingest", "preprocess", "analyze", "generate")
        batch_size: Batch size for analysis tasks
        max_retries: Maximum number of retries for failed tasks
    """
    try:
        # Validate parameters
        if steps not in ["all", "ingest", "preprocess", "analyze", "generate"]:
            print(f"Invalid steps parameter: {steps}")
            print("Valid options: all, ingest, preprocess, analyze, generate")
            return
            
        # If song_id not provided and we're not starting with ingestion,
        # try to find it from artist and song name
        if not song_id and steps not in ["ingest", "all"]:
            song_id = find_song_id(artist, song)
            if not song_id:
                print(f"Could not find song ID for {artist} - {song}")
                print("Please make sure the song is ingested first using the ingestion pipeline.")
                return
        
        # Set up paths
        song_path = Path("data/songs") / str(song_id) if song_id else None
        
        # Run ingestion if needed
        if steps in ["all", "ingest"]:
            print("\n🔄 Running ingestion...")
            if not song or not artist:
                print("\n❌ Ingestion failed: song and artist names are required for ingestion")
                return
            result = src.flows.ingestion.subflows.song_ingestion_flow(
                song_name=song,
                artist_name=artist,
                base_path=str(Path.cwd())
            )
            if not result or not result.get("song_path"):
                print("\n❌ Ingestion failed")
                return
                
            # Get the song ID from the ingestion result for subsequent steps
            song_id = str(result.get("id"))
            song_path = Path(result.get("song_path"))
            
        # Run preprocessing if needed
        if steps in ["all", "preprocess"]:
            print("\n🔄 Running preprocessing...")
            if not song_id:
                print("\n❌ Preprocessing failed: song_id is required")
                return
            try:
                song_id_int = int(song_id)
            except ValueError:
                print(f"\n❌ Preprocessing failed: invalid song_id '{song_id}'")
                return
                
            success = src.flows.preprocessing.subflows.process_song_annotations_flow(
                song_id=song_id_int,
                base_path=str(Path.cwd())
            )
            if not success:
                print("\n❌ Preprocessing failed")
                return
            
        # Run vocabulary analysis if needed
        if steps in ["all", "analyze", "generate"]:
            print("\n🔍 Running vocabulary analysis...")
            if not song_path or not song_path.exists():
                print("\n❌ Vocabulary analysis failed: song path not found")
                return
            success = asyncio.run(src.flows.generation.main.main(
                song_path=str(song_path)
            ))
            if not success:
                print("\n❌ Vocabulary analysis failed")
                return
            
        print("\n✅ Pipeline completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        return

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run the complete pipeline for a song")
    parser.add_argument("--song", "-s", help="Song title")
    parser.add_argument("--artist", "-a", help="Artist name")
    parser.add_argument("--song-id", "-i", help="Song ID (if already ingested)")
    parser.add_argument("--steps", default="all",
                      choices=["all", "ingest", "preprocess", "analyze", "generate"],
                      help="Pipeline steps to run")
    parser.add_argument("--batch-size", "-b", type=int, default=15,
                      help="Batch size for analysis tasks")
    parser.add_argument("--max-retries", "-r", type=int, default=3,
                      help="Maximum number of retries for failed tasks")
    
    args = parser.parse_args()
    run_pipeline(
        artist=args.artist,
        song=args.song,
        song_id=args.song_id,
        steps=args.steps,
        batch_size=args.batch_size,
        max_retries=args.max_retries
    )

if __name__ == "__main__":
    main()