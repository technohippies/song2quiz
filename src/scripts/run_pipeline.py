"""Run the complete pipeline for a song."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import click
from langfuse.decorators import langfuse_context, observe

import src.flows.generation.main
import src.flows.ingestion.subflows
import src.flows.preprocessing.subflows
from src.services.langfuse import create_song_session_id

logger = logging.getLogger(__name__)

T = TypeVar("T")


def ensure_type(value: Any, expected_type: type[T]) -> T:
    """Ensure a value is of the expected type."""
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(value).__name__}"
        )
    return value


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG level
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
# Set specific loggers to DEBUG level
logging.getLogger("src").setLevel(logging.DEBUG)
logging.getLogger("src.tasks").setLevel(logging.DEBUG)
logging.getLogger("src.services").setLevel(logging.DEBUG)


def find_song_id(artist: str, song: str) -> Optional[str]:
    """Find song ID from artist and song name."""
    import json

    try:
        # Load songs.json which contains the mapping
        with open("data/songs.json", "r") as f:
            songs = json.load(f)

        # Look for matching song in list
        for song_data in songs:
            if (
                song_data.get("artist_name", "").lower() == artist.lower()
                and song_data.get("song_name", "").lower() == song.lower()
            ):
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


def typed_observe() -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Type-safe wrapper for observe decorator."""
    return observe()


@typed_observe()
def run_pipeline(
    artist: Optional[str] = None,
    song: Optional[str] = None,
    song_id: Optional[str] = None,
    steps: str = "all",
    batch_size: int = 15,
    max_retries: int = 3,
    data_dir: str = "data",
) -> None:
    """Run the complete pipeline for a song."""
    try:
        # Create a session ID for this pipeline run
        session_id = create_song_session_id(song_id, artist, song)

        # Update the trace with session ID
        langfuse_context.update_current_trace(
            name="song_pipeline",
            session_id=session_id,
            metadata={
                "artist": artist,
                "song": song,
                "song_id": song_id,
                "steps": steps,
            },
        )

        # Validate parameters
        if steps not in ["all", "ingest", "preprocess", "analyze", "generate"]:
            print(f"Invalid steps parameter: {steps}")
            print("Valid options: all, ingest, preprocess, analyze, generate")
            return

        # If song_id not provided and we're not starting with ingestion,
        # try to find it from artist and song name
        if not song_id and steps not in ["ingest", "all"]:
            if artist is None or song is None:
                print("Artist and song name are required")
                return
            song_id = find_song_id(artist, song)
            if not song_id:
                print(f"Could not find song ID for {artist} - {song}")
                print(
                    "Please make sure the song is ingested first using the ingestion pipeline."
                )
                return

        # Set up paths
        song_path = Path(data_dir) / "songs" / str(song_id) if song_id else None

        # Run ingestion if needed
        if steps in ["all", "ingest"]:
            print("\n🔄 Running ingestion...")
            if not song or not artist:
                print(
                    "\n❌ Ingestion failed: song and artist names are required for ingestion"
                )
                return

            # Decorate the ingestion flow to capture it in the session
            @typed_observe()
            def run_ingestion() -> dict:
                langfuse_context.update_current_trace(
                    name="song_ingestion", session_id=session_id
                )
                return src.flows.ingestion.subflows.song_ingestion_flow(
                    song_name=song, artist_name=artist, base_path=str(Path(data_dir))
                )

            result = run_ingestion()
            if not result or not result.get("song_path"):
                print("\n❌ Ingestion failed")
                return

            # Get the song ID from the ingestion result for subsequent steps
            song_id = str(result.get("id", ""))
            song_path_str = result.get("song_path")
            if song_path_str is None:
                print("Error: song_path not found in result")
                return
            song_path = Path(song_path_str)

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

            @typed_observe()
            def run_preprocessing() -> bool:
                langfuse_context.update_current_trace(
                    name="song_preprocessing", session_id=session_id
                )
                return src.flows.preprocessing.subflows.process_song_annotations_flow(
                    song_id=song_id_int, base_path=str(Path(data_dir))
                )

            success = run_preprocessing()
            if not success:
                print("\n❌ Preprocessing failed")
                return

        # Run vocabulary analysis if needed
        if steps in ["all", "analyze", "generate"]:
            print("\n🔍 Running vocabulary analysis...")
            if not song_path or not song_path.exists():
                print("\n❌ Vocabulary analysis failed: song path not found")
                return

            @typed_observe()
            def run_analysis() -> bool:
                langfuse_context.update_current_trace(
                    name="song_analysis", session_id=session_id
                )
                return asyncio.run(
                    src.flows.generation.main.main(song_path=str(song_path))
                )

            success = run_analysis()
            if not success:
                print("\n❌ Vocabulary analysis failed")
                return

        print("\n✅ Pipeline completed successfully!")

    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        return


@click.group(name="song2quiz")
def cli_group() -> None:
    """Song2Quiz CLI tool for managing song analysis pipeline."""
    pass


@cli_group.command(name="run-pipeline")
@click.option("--artist", help="Artist name")
@click.option("--song", help="Song name")
@click.option("--song-id", help="Song ID")
@click.option(
    "--steps",
    default="all",
    help="Pipeline steps to run (all, ingest, preprocess, generate)",
)
@click.option("--batch-size", default=15, help="Batch size for processing")
@click.option("--max-retries", default=3, help="Maximum number of retries")
@click.option(
    "--data-dir",
    default="data",
    help="Directory containing song data",
)
def run_pipeline_cli(
    artist: Optional[str] = None,
    song: Optional[str] = None,
    song_id: Optional[str] = None,
    steps: str = "all",
    batch_size: int = 15,
    max_retries: int = 3,
    data_dir: str = "data",
) -> None:
    """Run the complete pipeline for a song."""
    run_pipeline(artist, song, song_id, steps, batch_size, max_retries, data_dir)


cli = cli_group  # For backwards compatibility with tests

if __name__ == "__main__":
    cli()
