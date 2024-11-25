"""CLI to run song ingestion flows."""

import click
from pathlib import Path
from src.flows.ingestion.subflows import song_ingestion_flow

@click.command()
@click.option('--song', '-s', required=True, help='Name of the song')
@click.option('--artist', '-a', required=True, help='Name of the artist')
@click.option('--data-dir', '-d', 
              default=str(Path(__file__).parent.parent.parent / "data"),
              help='Base directory for data storage')
def main(song: str, artist: str, data_dir: str):
    """Run song ingestion flow for a single song.
    
    Example:
        python -m src.scripts.ingest_song --song "In My Life" --artist "The Beatles"
    """
    result = song_ingestion_flow(
        song_name=song,
        artist_name=artist,
        base_path=data_dir
    )
    
    print("\nIngestion Results:")
    for key, value in result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
