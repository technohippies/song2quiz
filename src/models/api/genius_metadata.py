from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class Artist:
    """Artist information from Genius."""

    api_path: str
    id: int
    name: str
    url: str
    header_image_url: Optional[str] = None
    image_url: Optional[str] = None
    is_verified: bool = False
    is_meme_verified: bool = False
    iq: Optional[int] = None  # Some artists have an IQ field


@dataclass
class Album:
    """Album information from Genius."""

    api_path: str
    id: int
    name: str
    url: str
    full_title: str
    cover_art_url: Optional[str] = None
    release_date_for_display: Optional[str] = None
    artist: Optional[Artist] = None
    primary_artists: List[Artist] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "api_path": self.api_path,
            "url": self.url,
            "full_title": self.full_title,
            "cover_art_url": self.cover_art_url,
            "release_date_for_display": self.release_date_for_display,
        }


@dataclass
class Performance:
    """Custom performance credits."""

    label: str
    artists: List[Artist]


@dataclass
class Stats:
    """Song statistics from Genius."""

    pageviews: int = 0
    accepted_annotations: int = 0
    contributors: int = 0
    iq_earners: int = 0
    transcribers: int = 0
    unreviewed_annotations: int = 0
    verified_annotations: int = 0
    hot: bool = False
    concurrents: Optional[int] = None


@dataclass
class Description:
    """Song description with DOM structure."""

    dom: Dict[str, Any]  # Storing as raw dict since DOM structure varies


class GeniusMetadata(BaseModel):
    """Complete song metadata from Genius."""

    id: int
    title: str
    primary_artist_names: str
    album: Optional[Album] = None
    # ... other fields

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeniusMetadata":
        """Create from Genius API response."""
        # Convert nested structures
        album_data = data.get("album", {})
        if album_data:
            album = Album(
                api_path=album_data.get("api_path", ""),
                id=album_data.get("id", 0),
                name=album_data.get("name", ""),
                url=album_data.get("url", ""),
                full_title=album_data.get("full_title", album_data.get("name", "")),
                cover_art_url=album_data.get("cover_art_url"),
                release_date_for_display=album_data.get("release_date_for_display"),
            )
        else:
            album = None

        # Map API fields to our model fields
        metadata = {
            "id": data.get("id", 0),
            "title": data.get("title", ""),
            "primary_artist_names": data.get("primary_artist", {}).get("name", ""),
            "album": album,
        }

        return cls(**metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "primary_artist_names": self.primary_artist_names,
        }

        if self.album:
            result["album"] = self.album.to_dict()

        return result
