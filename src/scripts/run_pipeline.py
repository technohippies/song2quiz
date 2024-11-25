"""CLI to run the full lyrics processing pipeline."""

import click
from pathlib import Path
from src.flows.ingestion.subflows import song_ingestion_flow
from src.flows.preprocessing.subflows import process_song_annotations_flow

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
        success = process_song_annotations_flow(
            song_id=result['id'],
            base_path=data_dir
        )
        if success:
            print("✨ Successfully processed annotations")
        else:
            print("❌ Failed to process annotations")

if __name__ == "__main__":
    main() 