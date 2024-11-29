"""CLI to run song preprocessing flows."""

import json
from pathlib import Path
from typing import Optional

import click

import src.flows.preprocessing.subflows
from src.utils.io.paths import get_songs_dir


@click.command()
@click.option('--song-id', '-i', type=int, help='ID of the song to preprocess')
@click.option('--song', '-s', help='Name of the song (if ID not provided)')
@click.option('--artist', '-a', help='Name of the artist (if ID not provided)')
@click.option('--data-dir', '-d',
              default=str(Path(__file__).parent.parent.parent / "data"),
              help='Base directory for data storage')
def main(song_id: Optional[int], song: Optional[str], artist: Optional[str], data_dir: str) -> int:
    """Run preprocessing flow for a single song.

    Can be run either with a song ID directly, or with song name and artist
    which will be used to look up the ID from metadata.

    Example:
        python -m src.scripts.preprocess_song --song-id 2236
        python -m src.scripts.preprocess_song --song "In My Life" --artist "The Beatles"
    """
    try:
        found_id: Optional[int] = song_id

        if not found_id:
            if not (song and artist):
                raise click.UsageError("Must provide either --song-id or both --song and --artist")

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
                            found_id = int(song_dir.name)
                            break
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Warning: Invalid metadata file in {song_dir}: {e}")
                        continue

            if not found_id:
                print(f"❌ Could not find song ID for {song} by {artist}")
                return 1

        success = src.flows.preprocessing.subflows.process_song_annotations_flow(song_id=found_id, base_path=data_dir)

        if success:
            print("\n✅ Preprocessing completed successfully")
            return 0
        else:
            print("\n❌ Preprocessing failed")
            return 1

    except Exception as e:
        print(f"\n❌ Preprocessing failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
