"""CLI to run the full lyrics processing pipeline."""

import click
from pathlib import Path
import json
from typing import Optional, Dict, Any
import src.flows.ingestion.subflows
import src.flows.preprocessing.subflows
from src.utils.io.paths import get_songs_dir

@click.command()
@click.option('--song', '-s', required=True, help='Name of the song')
@click.option('--artist', '-a', required=True, help='Name of the artist')
@click.option('--data-dir', '-d', 
              default=str(Path(__file__).parent.parent.parent / "data"),
              help='Base directory for data storage')
@click.option('--steps', '-t', 
              type=click.Choice(['ingest', 'preprocess', 'all']), 
              default='all',
              help='Pipeline steps to run')
def main(song: str, artist: str, data_dir: str, steps: str) -> int:
    """Run the full lyrics processing pipeline.
    
    Example:
        python -m src.scripts.run_pipeline --song "In My Life" --artist "The Beatles"
        python -m src.scripts.run_pipeline -s "In My Life" -a "The Beatles" -t ingest
    """
    try:
        result: Optional[Dict[str, Any]] = None
        song_id: Optional[int] = None
        
        if steps in ['ingest', 'all']:
            result = src.flows.ingestion.subflows.song_ingestion_flow(
                song_name=song,
                artist_name=artist,
                base_path=data_dir
            )
            
            if not result or not result.get('id'):
                print("❌ Ingestion failed - no song ID returned")
                return 1
                
            song_id = result['id']
            print("\nIngestion Results:")
            for key, value in result.items():
                print(f"{key}: {value}")
            
            # If we're only doing ingestion, return success
            if steps == 'ingest':
                print("\n✅ Ingestion completed successfully")
                return 0

        if steps in ['preprocess', 'all']:
            # If we're only preprocessing, try to find the song ID from metadata
            if not song_id:
                # Look through all song directories for matching metadata
                songs_dir = get_songs_dir(data_dir)
                if not songs_dir.exists():
                    print(f"❌ Songs directory not found at {songs_dir}")
                    return 1
                
                for song_dir in songs_dir.glob("*"):
                    metadata_file = song_dir / "genius_metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                            if metadata['title'].lower() == song.lower() and \
                               metadata['artist'].lower() == artist.lower():
                                song_id = int(song_dir.name)
                                break
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Warning: Invalid metadata file in {song_dir}: {e}")
                            continue
                
                if not song_id:
                    print(f"❌ Could not find song ID for {song} by {artist}")
                    return 1

            success = src.flows.preprocessing.subflows.process_song_annotations_flow(song_id=song_id, base_path=data_dir)
            if not success:
                print("\n❌ Preprocessing failed")
                return 1
            
        print("\n✅ Pipeline completed successfully")
        return 0
            
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())