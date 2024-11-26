"""CLI to run song ingestion flows."""

import click
from pathlib import Path
import sys
import src.flows.ingestion.subflows

@click.command()
@click.option('--song', '-s', required=True, help='Name of the song')
@click.option('--artist', '-a', required=True, help='Name of the artist')
@click.option('--preprocess', '-p', is_flag=True, help='Run preprocessing after ingestion')
@click.option('--data-dir', '-d', 
              default=str(Path(__file__).parent.parent.parent / "data"),
              help='Base directory for data storage')
def main(song: str, artist: str, data_dir: str, preprocess: bool = False) -> int:
    """Run song ingestion flow for a single song.
    
    Example:
        python -m src.scripts.ingest_song --song "In My Life" --artist "The Beatles"
    """
    try:
        result = src.flows.ingestion.subflows.song_ingestion_flow(
            song_name=song,
            artist_name=artist,
            base_path=data_dir
        )
        
        # Check if we got a result at all
        if not isinstance(result, dict):
            print("\n Ingestion failed - invalid result type", file=sys.stderr)
            sys.exit(1)
            
        # Check for required fields
        if not result.get('id'):
            print("\n Ingestion failed - no song ID returned", file=sys.stderr)
            sys.exit(1)
            
        # Check that song_path exists and is not None
        song_path = result.get('song_path')
        if not song_path:
            print("\n Ingestion failed - no song path returned", file=sys.stderr)
            sys.exit(1)
            
        print("\nIngestion Results:")
        for key, value in result.items():
            print(f"{key}: {value}")
            
        print("\n Ingestion completed successfully")
        return 0
        
    except Exception as e:
        print(f"\n Ingestion failed with error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
