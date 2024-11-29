import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import requests
from dotenv import load_dotenv
from requests.exceptions import HTTPError, RequestException, Timeout

from src.models.api.genius_metadata import GeniusMetadata

from ..utils.io.paths import sanitize_filename

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GeniusAPI:
    """Client for the Genius API with rate limiting and error handling"""

    def __init__(self, rate_limit: float = 0.5):
        """
        Initialize the Genius API client

        Args:
            rate_limit: Minimum time in seconds between API requests
        """
        self.base_url = "https://api.genius.com"
        self.rate_limit = rate_limit
        self.last_request_time: float = 0

        api_token = os.getenv("GENIUS_API_TOKEN")
        if not api_token:
            raise ValueError("GENIUS_API_TOKEN environment variable not set")

        self.headers = {
            "Accept": "application/json",
            "User-Agent": "song2quiz/1.0",
            "Host": "api.genius.com",
            "Authorization": f"Bearer {api_token}",
        }
        logger.debug("Initialized GeniusAPI client")

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited request to the Genius API."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.rate_limit:
                time.sleep(self.rate_limit - time_since_last)

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            self.last_request_time = time.time()

            response.raise_for_status()
            return cast(Dict[str, Any], response.json())

        except Timeout:
            logger.error(f"Request to {endpoint} timed out")
            raise
        except HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting before retry")
                time.sleep(60)  # Wait a minute before retrying
                return self._make_request(endpoint, params)
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}")
            raise
        except RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def search_song(self, song_name: str, artist_name: str) -> Optional[GeniusMetadata]:
        """
        Search for a song on Genius

        Args:
            song_name: Name of the song
            artist_name: Name of the artist

        Returns:
            GeniusMetadata if found, None otherwise
        """
        try:
            # Search for the song
            search_results = self._make_request(
                "search", params={"q": f"{song_name} {artist_name}"}
            )

            # Get all matching songs
            matches = []
            hits = search_results["response"]["hits"]

            # Split artist name for multiple artists
            artist_parts = []
            # Handle different separators
            for separator in ["_", "&", "and", ","]:
                if separator in artist_name:
                    artist_parts.extend(
                        [part.strip().lower() for part in artist_name.split(separator)]
                    )

            # If no separators found, use the whole name
            if not artist_parts:
                artist_parts = [artist_name.lower()]

            for hit in hits:
                if hit["type"] == "song":
                    result = hit["result"]
                    # Check if any of the artists match
                    result_artist = result["primary_artist"]["name"].lower()

                    # Check if any part of the artist name matches
                    if any(part in result_artist for part in artist_parts):
                        # Get full song data
                        song_response = self._make_request(f"songs/{result['id']}")
                        full_song_data = song_response["response"]["song"]

                        # Skip remixes unless specifically searching for one
                        title = full_song_data["title"].lower()
                        if "remix" in title and "remix" not in song_name.lower():
                            continue

                        matches.append(full_song_data)

            if not matches:
                logger.warning(
                    f"No matching songs found for {song_name} by {artist_name}"
                )
                return None

            # Sort by pageviews and return the most popular
            matches.sort(
                key=lambda x: x.get("stats", {}).get("pageviews", 0), reverse=True
            )
            chosen_song = matches[0]

            logger.info(
                f"Selected '{chosen_song['title']}' with {chosen_song['stats'].get('pageviews', 0)} pageviews"
            )
            return GeniusMetadata.from_dict(chosen_song)

        except Exception as e:
            logger.error(f"Error searching for song: {str(e)}")
            return None

    def get_song_annotations(self, song_id: int) -> List[Dict[str, Any]]:
        """Get annotations for a song.

        Args:
            song_id: Genius song ID

        Returns:
            List of annotation dictionaries
        """
        try:
            data = self._make_request(
                f"songs/{song_id}/referents",
                params={
                    "song_id": str(song_id),
                    "text_format": "dom",
                    "per_page": "50",
                },
            )
            return cast(
                List[Dict[str, Any]], data.get("response", {}).get("referents", [])
            )
        except Exception as e:
            logger.error(f"Failed to get annotations: {e}")
            return []

    def save_song_metadata(
        self, metadata: GeniusMetadata, base_path: str
    ) -> Optional[Path]:
        """
        Save song metadata to the appropriate folder structure

        Args:
            metadata: Song metadata to save
            base_path: Base path for saving data

        Returns:
            Path where the data was saved, None if error
        """
        try:
            # Extract relevant data
            artist_name = metadata.primary_artist_names
            album_name = metadata.album.name if metadata.album else None
            song_name = metadata.title

            if not all([artist_name, song_name]):
                logger.error("Missing required song metadata")
                return None

            # Sanitize names for filesystem
            artist_folder = sanitize_filename(artist_name)
            album_folder = sanitize_filename(album_name) if album_name else "singles"
            song_folder = sanitize_filename(song_name)

            # Create folder structure
            song_path = Path(base_path) / artist_folder / album_folder / song_folder
            song_path.mkdir(parents=True, exist_ok=True)

            # Save metadata
            metadata_path = song_path / "genius_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)

            # If this is part of an album, update album metadata
            if metadata.album:
                self.update_album_metadata(metadata, song_path.parent)

            return song_path

        except Exception as e:
            logger.error(f"Error saving song metadata: {str(e)}")
            return None

    def update_album_metadata(self, metadata: GeniusMetadata, album_path: Path) -> None:
        """
        Update the album.json file with new song data

        Args:
            metadata: Song metadata containing album info
            album_path: Path to the album directory
        """
        try:
            if not metadata.album:
                return

            album_file = album_path / "album.json"
            album_data = {}

            # Load existing album data if it exists
            if album_file.exists():
                with open(album_file, "r", encoding="utf-8") as f:
                    album_data = json.load(f)

            # Update album metadata
            album_data.update(
                {
                    "genius_album_id": metadata.album.id,
                    "title": metadata.album.name,
                    "artist_name": metadata.primary_artist_names,
                    "release_date": metadata.album.release_date_for_display,
                    "cover_art_url": metadata.album.cover_art_url,
                }
            )

            # Save updated album data
            with open(album_file, "w", encoding="utf-8") as f:
                json.dump(album_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error updating album metadata: {str(e)}")
