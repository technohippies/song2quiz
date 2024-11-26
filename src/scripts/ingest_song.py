"""Script to ingest a song into the system."""
import argparse
from pathlib import Path
from src.flows.ingestion.subflows import song_ingestion_flow

def main():
    parser = argparse.ArgumentParser(description="Ingest a song into the system")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--song", required=True, help="Song title")
    parser.add_argument("--base-path", default=str(Path(__file__).parent.parent.parent),
                       help="Base path for data storage")
    
    args = parser.parse_args()
    
    print(f"Ingesting {args.song} by {args.artist}...")
    results = song_ingestion_flow(
        song_name=args.song,
        artist_name=args.artist,
        base_path=args.base_path
    )
    
    if results.get("song_path"):
        print(f"Successfully ingested song to {results['song_path']}")
    else:
        print("Failed to ingest song")

if __name__ == "__main__":
    main()
