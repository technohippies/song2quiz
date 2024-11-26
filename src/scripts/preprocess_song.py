"""CLI to run song preprocessing flows."""

import click
from pathlib import Path
from src.flows.preprocessing.subflows import process_song_annotations_flow
from src.utils.io.paths import get_songs_dir
import json

@click.command()
@click.option('--song-id', '-i', type=int, help='ID of the song to preprocess')
@click.option('--song', '-s', help='Name of the song (if ID not provided)')
@click.option('--artist', '-a', help='Name of the artist (if ID not provided)')
@click.option('--data-dir', '-d', 
              default=str(Path(__file__).parent.parent.parent / "data"),
              help='Base directory for data storage')
def main(song_id: int, song: str, artist: str, data_dir: str):
    """Run preprocessing flow for a single song.
    
    Can be run either with a song ID directly, or with song name and artist
    which will be used to look up the ID from metadata.
    
    Example:
        python -m src.scripts.preprocess_song --song-id 2236
        python -m src.scripts.preprocess_song --song "In My Life" --artist "The Beatles"
    """
    if not song_id:
        if not (song and artist):
            raise click.UsageError("Must provide either --song-id or both --song and --artist")
        
        # Look through all song directories for matching metadata
        songs_dir = get_songs_dir(data_dir)
        for song_dir in songs_dir.glob("*"):
            metadata_file = song_dir / "genius_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                if metadata['title'].lower() == song.lower() and \
                   metadata['artist'].lower() == artist.lower():
                    song_id = int(song_dir.name)
                    break
        
        if not song_id:
            print(f"❌ Could not find song ID for {song} by {artist}")
            return

    success = process_song_annotations_flow(song_id=song_id, base_path=data_dir)
    
    if success:
        print("\n✅ Preprocessing completed successfully")
    else:
        print("\n❌ Preprocessing failed")

if __name__ == "__main__":
    main()
