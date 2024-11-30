"""LRCLib API client for fetching timestamped lyrics."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict, cast

import requests
from requests.exceptions import HTTPError, RequestException, Timeout

from src.models.api.lrclib import LRCLibLyrics

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class LRCResponse(TypedDict, total=False):
    """Type definition for LRCLib API response."""

    syncedLyrics: str
    plainLyrics: str
    error: str


class LRCLibAPI:
    """Client for the LRCLib API."""

    def __init__(self) -> None:
        """Initialize the LRCLib API client."""
        self.base_url = "https://lrclib.net/api"
        self.headers = {"Accept": "application/json"}
        self.rate_limit = 1.0  # Rate limit in seconds
        self.last_request_time = 0.0
        logger.debug("Initialized LRCLibAPI client")

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a rate-limited request to the LRCLib API."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.rate_limit:
                time.sleep(self.rate_limit - time_since_last)

        url = f"{self.base_url}/{endpoint}"
        try:
            logger.debug(f"Making request to LRCLib API - URL: {url}, Params: {params}")
            response = requests.get(
                url, headers=self.headers, params=params, timeout=10
            )
            self.last_request_time = time.time()

            response.raise_for_status()
            return cast(Dict[str, Any], response.json())

        except (HTTPError, RequestException, Timeout) as e:
            logger.error(f"Error making request to LRCLib API: {str(e)}")
            raise

    def search_lyrics(self, artist: str, title: str) -> Dict[str, Any]:
        """Search for lyrics by artist and title.

        Args:
            artist: Artist name
            title: Track/song title

        Returns:
            Dictionary containing lyrics data or error
        """
        try:
            return self._make_request(
                "get", params={"artist_name": artist, "track_name": title}
            )
        except RequestException as e:
            logger.error(f"Error searching for lyrics: {e}")
            return {"error": str(e)}

    def get_lyrics(self, artist_name: str, track_name: str) -> Dict[str, Any] | None:
        """Get lyrics for a song from LRCLib.

        Args:
            artist_name: Name of the artist
            track_name: Name of the track

        Returns:
            Dictionary containing lyrics data if found, None otherwise
        """
        try:
            logger.debug(f"Making request to LRCLib API - URL: {self.base_url}/get")
            response = requests.get(
                f"{self.base_url}/get",
                params={
                    "artist_name": artist_name,
                    "track_name": track_name,
                },
                headers=self.headers,
            )
            logger.debug(f"LRCLib API Status Code: {response.status_code}")

            if response.status_code == 200:
                data = cast(Dict[str, Any], response.json())
                log_data = {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "artistName": data.get("artistName"),
                    "albumName": data.get("albumName"),
                    "duration": data.get("duration"),
                    "instrumental": data.get("instrumental"),
                }
                logger.debug(
                    f"LRCLib API Response Data: {json.dumps(log_data, indent=2)}"
                )
                return data
            elif response.status_code == 404:
                logger.warning(f"No lyrics found for '{track_name}' by {artist_name}")
                return None
            else:
                logger.warning(
                    f"LRCLib API returned status code: {response.status_code}"
                )
                return None

        except Exception as e:
            logger.error(f"Error fetching lyrics: {str(e)}")
            return None

    def save_lyrics(self, lyrics: LRCLibLyrics, song_path: Path) -> Optional[Path]:
        """
        Save lyrics data to the song folder

        Args:
            lyrics: LRCLibLyrics object containing lyrics information
            song_path: Path to the song folder

        Returns:
            Path where lyrics were saved, None if error
        """
        try:
            # Save to lrclib_lyrics.json for raw data
            lrclib_path = song_path / "lrclib_lyrics.json"
            with open(lrclib_path, "w", encoding="utf-8") as f:
                json.dump(lyrics.to_dict(), f, ensure_ascii=False, indent=2)

            # Save to lyrics.json in the expected format for matching
            lyrics_path = song_path / "lyrics.json"
            with open(lyrics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "source": lyrics.source,
                        "has_timestamps": lyrics.has_timestamps,
                        "timestamped_lines": [
                            line.to_dict() for line in lyrics.timestamped_lines
                        ],
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            return lyrics_path

        except Exception as e:
            logger.error(f"Error saving lyrics: {str(e)}")
            return None
