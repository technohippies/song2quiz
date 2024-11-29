"""Script to ingest a song into the system."""

import click

from src.flows.ingestion.subflows import song_ingestion_flow


@click.command()
@click.option("--artist", required=True, help="Artist name")
@click.option("--song", required=True, help="Song title")
@click.option("--data-dir",
              default="data",
              help="Base path for data storage",
              type=click.Path(exists=True, file_okay=False, dir_okay=True))
def ingest_song_cli(artist: str, song: str, data_dir: str):
    """Ingest a song into the system."""
    print(f"Ingesting {song} by {artist}...")
    results = song_ingestion_flow(
        song_name=song,
        artist_name=artist,
        base_path=data_dir
    )

    if results.get("song_path"):
        print(f"Successfully ingested song to {results['song_path']}")
    else:
        print("Failed to ingest song")
        raise click.ClickException("Failed to ingest song")

if __name__ == "__main__":
    ingest_song_cli()
