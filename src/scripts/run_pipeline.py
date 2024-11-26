"""CLI to run the full lyrics processing pipeline."""

import click
from pathlib import Path
import json
import glob
from src.flows.ingestion.subflows import song_ingestion_flow
from src.flows.preprocessing.subflows import process_song_annotations_flow
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
def main(song: str, artist: str, data_dir: str, steps: str):
    """Run the full lyrics processing pipeline.
    
    Example:
        python -m src.scripts.run_pipeline --song "In My Life" --artist "The Beatles"
        python -m src.scripts.run_pipeline -s "In My Life" -a "The Beatles" -t ingest
    """
    result = None
    
    if steps in ['ingest', 'all']:
        result = song_ingestion_flow(
            song_name=song,
            artist_name=artist,
            base_path=data_dir
        )
        print("\nIngestion Results:")
        for key, value in result.items():
            print(f"{key}: {value}")
            
        if not result.get('id'):
            print("❌ Ingestion failed - no song ID returned")
            return

    if steps in ['preprocess', 'all']:
        # If we're only preprocessing, try to find the song ID from metadata
        if not result:
            # Look through all song directories for matching metadata
            songs_dir = get_songs_dir(data_dir)
            song_id = None
            
            for song_dir in songs_dir.glob("*"):
                if not song_dir.is_dir():
                    continue
                    
                try:
                    with open(song_dir / "genius_metadata.json") as f:
                        metadata = json.load(f)
                        if metadata['title'].lower() == song.lower() and \
                           metadata['primary_artist_names'].lower() == artist.lower():
                            song_id = metadata['id']
                            break
                except (FileNotFoundError, KeyError, json.JSONDecodeError):
                    continue
            
            if not song_id:
                print("❌ Could not find song metadata. Please run ingestion first.")
                return
        else:
            song_id = result['id']
            
        success = process_song_annotations_flow(
            song_id=song_id,
            base_path=data_dir
        )
        if success:
            print("✨ Successfully processed annotations")
        else:
            print("❌ Failed to process annotations")

if __name__ == "__main__":
    main()