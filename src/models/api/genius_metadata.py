import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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


@dataclass
class GeniusMetadata:
    """Complete song metadata from Genius."""

    id: int
    title: str
    full_title: str
    artist_names: str
    path: str
    url: str
    annotation_count: int
    primary_artist_names: str
    language: str

    # Media
    header_image_url: Optional[str] = None
    header_image_thumbnail_url: Optional[str] = None
    song_art_image_url: Optional[str] = None
    song_art_image_thumbnail_url: Optional[str] = None

    # Colors
    song_art_primary_color: Optional[str] = None
    song_art_secondary_color: Optional[str] = None
    song_art_text_color: Optional[str] = None

    # Release info
    release_date: Optional[str] = None
    release_date_for_display: Optional[str] = None
    recording_location: Optional[str] = None

    # Related data
    album: Optional[Album] = None
    stats: Optional[Stats] = None
    description: Optional[Description] = None
    custom_performances: List[Performance] = field(default_factory=list)

    # State
    lyrics_state: str = "complete"
    pyongs_count: int = 0

    # External IDs
    apple_music_id: Optional[str] = None
    apple_music_player_url: Optional[str] = None

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

        stats = Stats(**data.get("stats", {})) if data.get("stats") else None
        description = (
            Description(data["description"]) if data.get("description") else None
        )

        performances = []
        for perf in data.get("custom_performances", []):
            artists = [Artist(**artist) for artist in perf["artists"]]
            performances.append(Performance(label=perf["label"], artists=artists))

        # Map API fields to our model fields
        metadata = {
            "id": data.get("id", 0),
            "title": data.get("title", ""),
            "full_title": data.get("full_title", ""),
            "artist_names": data.get("artist_names", ""),
            "path": data.get("path", ""),
            "url": data.get("url", ""),
            "annotation_count": data.get("annotation_count", 0),
            "primary_artist_names": data.get("primary_artist", {}).get("name", ""),
            "language": data.get("language", "en"),
            "header_image_url": data.get("header_image_url"),
            "header_image_thumbnail_url": data.get("header_image_thumbnail_url"),
            "song_art_image_url": data.get("song_art_image_url"),
            "song_art_image_thumbnail_url": data.get("song_art_image_thumbnail_url"),
            "song_art_primary_color": data.get("song_art_primary_color"),
            "song_art_secondary_color": data.get("song_art_secondary_color"),
            "song_art_text_color": data.get("song_art_text_color"),
            "release_date": data.get("release_date"),
            "release_date_for_display": data.get("release_date_for_display"),
            "recording_location": data.get("recording_location"),
            "lyrics_state": data.get("lyrics_state", "complete"),
            "pyongs_count": data.get("pyongs_count", 0),
            "apple_music_id": data.get("apple_music_id"),
            "apple_music_player_url": data.get("apple_music_player_url"),
            "album": album,
            "stats": stats,
            "description": description,
            "custom_performances": performances,
        }

        return cls(**metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
