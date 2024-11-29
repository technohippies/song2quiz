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

            logger.debug(f"LRCLib API Status Code: {response.status_code}")
            response.raise_for_status()

            data = cast(Dict[str, Any], response.json())
            logger.debug(f"LRCLib API Response Data: {json.dumps(data, indent=2)}")
            return data

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

    def search_lyrics(self, artist: str, title: str) -> Dict[str, Any]:
        """Search for lyrics by artist and title."""
        try:
            response = requests.get(
                f"{self.base_url}/get",
                params={"artist": artist, "track": title},
                timeout=10,
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except RequestException as e:
            logger.error(f"Error searching for lyrics: {e}")
            return {"error": str(e)}

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
            lyrics_path = song_path / "lrclib_lyrics.json"

            # Save as JSON, dataclass has built-in asdict() method
            with open(lyrics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "source": lyrics.source,
                        "match_score": lyrics.match_score,
                        "lyrics": lyrics.lyrics,
                        "has_timestamps": lyrics.has_timestamps,
                        "plain_lyrics": lyrics.plain_lyrics,
                        "timestamped_lines": [
                            {"timestamp": str(line.timestamp), "text": line.text}
                            for line in lyrics.timestamped_lines
                        ]
                        if lyrics.has_timestamps
                        else [],
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            return lyrics_path

        except Exception as e:
            logger.error(f"Error saving lyrics: {str(e)}")
            return None
