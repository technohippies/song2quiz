"""LRCLib API client for fetching timestamped lyrics."""

from typing import Dict, Optional
import logging
import requests
from pathlib import Path
import json
import time
from requests.exceptions import RequestException, HTTPError, Timeout

from src.models.api.lrclib import LRCLibLyrics

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LRCLibAPI:
    """Client for the LRCLib API with rate limiting and error handling"""
    
    def __init__(self, rate_limit: float = 0.5):
        """
        Initialize the LRCLib API client
        
        Args:
            rate_limit: Minimum time in seconds between API requests
        """
        self.base_url = "https://lrclib.net/api"
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "song2quiz/1.0"
        }
        logger.debug("Initialized LRCLibAPI client")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make rate-limited request to LRCLib API
        
        Args:
            endpoint: API endpoint to request
            params: Optional query parameters
            
        Returns:
            JSON response from the API
            
        Raises:
            RequestException: For network or API errors
        """
        # Apply rate limiting
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        
        url = f"{self.base_url}/{endpoint}"
        try:
            logger.debug(f"Making request to LRCLib API - URL: {url}, Params: {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            self.last_request_time = time.time()
            
            logger.debug(f"LRCLib API Status Code: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
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

    def search_lyrics(self, song_name: str, artist_name: str) -> Optional[LRCLibLyrics]:
        """
        Search for timestamped lyrics on LRCLib
        
        Args:
            song_name: Name of the song
            artist_name: Name of the artist
            
        Returns:
            LRCLibLyrics if found, None otherwise
        """
        try:
            # Search for the song
            search_results = self._make_request(
                "search",
                params={
                    "track_name": song_name,
                    "artist_name": artist_name
                }
            )
            
            if not search_results or not isinstance(search_results, list):
                logger.warning(f"No lyrics found for {song_name} by {artist_name}")
                return None

            # Find the best match - prefer results with synced lyrics
            best_match = None
            for result in search_results:
                if result.get('syncedLyrics'):
                    best_match = result
                    break
                elif result.get('plainLyrics') and not best_match:
                    best_match = result

            if not best_match:
                logger.warning(f"No usable lyrics found for {song_name} by {artist_name}")
                return None
                
            return LRCLibLyrics(
                lyrics=best_match.get('syncedLyrics', ''),
                has_timestamps=bool(best_match.get('syncedLyrics')),
                plain_lyrics=best_match.get('plainLyrics', '')
            )
            
        except Exception as e:
            logger.error(f"Error searching for lyrics: {str(e)}")
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
            lyrics_path = song_path / "lrclib_lyrics.json"
            
            # Save as JSON, dataclass has built-in asdict() method
            with open(lyrics_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "source": lyrics.source,
                    "match_score": lyrics.match_score,
                    "lyrics": lyrics.lyrics,
                    "has_timestamps": lyrics.has_timestamps,
                    "plain_lyrics": lyrics.plain_lyrics,
                    "timestamped_lines": [
                        {"timestamp": str(line.timestamp), "text": line.text}
                        for line in lyrics.timestamped_lines
                    ] if lyrics.has_timestamps else []
                }, f, ensure_ascii=False, indent=2)
                
            return lyrics_path
            
        except Exception as e:
            logger.error(f"Error saving lyrics: {str(e)}")
            return None