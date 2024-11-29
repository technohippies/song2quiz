import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

from src.flows.ingestion.subflows import song_ingestion_flow
from src.models.api.genius_metadata import Album, GeniusMetadata
from src.utils.io.paths import get_song_dir, get_songs_catalog_path


class MockGeniusAPI:
    """Mock implementation of GeniusAPI"""

    def __init__(
        self,
        metadata: Optional[GeniusMetadata] = None,
        annotations: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.metadata = metadata
        self.annotations = annotations

    def search_song(self, song_name: str, artist_name: str) -> Optional[GeniusMetadata]:
        return self.metadata

    def get_song_annotations(self, song_id: int) -> Optional[List[Dict[str, Any]]]:
        return self.annotations


class MockLRCLibAPI:
    """Mock implementation of LRCLibAPI"""

    def __init__(self, lyrics: Optional[Dict[str, str]] = None) -> None:
        self.lyrics = lyrics

    def search_lyrics(
        self, song_name: str, artist_name: str
    ) -> Optional[Dict[str, str]]:
        return self.lyrics


@pytest.fixture
def mock_genius_response() -> Dict[str, Any]:
    """Mock response for Genius API"""
    return {
        "id": 2236,
        "title": "Yesterday",
        "full_title": "Yesterday by The Beatles",
        "artist_names": "The Beatles",
        "path": "/The-beatles-yesterday-lyrics",
        "url": "https://genius.com/The-beatles-yesterday-lyrics",
        "annotation_count": 6,
        "primary_artist_names": "The Beatles",
    }


@pytest.fixture
def mock_lyrics_response() -> Dict[str, str]:
    """Mock response for LRCLib API"""
    return {"lyrics": "Test lyrics", "syncedLyrics": "[00:00.00]Test lyrics"}


@pytest.fixture
def mock_annotations() -> List[Dict[str, Any]]:
    """Mock Genius annotations"""
    return [
        {
            "_type": "referent",
            "id": 1,
            "fragment": "Test fragment",
            "annotations": [
                {
                    "body": {
                        "dom": {
                            "tag": "root",
                            "children": [
                                {
                                    "tag": "text",
                                    "children": ["This is a test annotation"],
                                }
                            ],
                        }
                    }
                }
            ],
        }
    ]


@pytest.fixture
def mock_genius_metadata() -> GeniusMetadata:
    """Mock GeniusMetadata object"""
    return GeniusMetadata(
        id=2236,
        title="Yesterday",
        primary_artist_names="The Beatles",
        album=Album(
            api_path="/albums/1234",
            id=1234,
            name="Help!",
            url="http://genius.com/albums/1234",
            full_title="Help! by The Beatles",
            cover_art_url="http://example.com/cover.jpg",
            release_date_for_display="1965",
        ),
    )


def test_song_ingestion_flow(
    tmp_path: Path,
    mock_genius_metadata: GeniusMetadata,
    mock_lyrics_response: Dict[str, str],
    mock_annotations: List[Dict[str, Any]],
) -> None:
    """Test the song ingestion flow with mocked API responses"""
    # Create mock API instances with test data
    mock_genius = MockGeniusAPI(
        metadata=mock_genius_metadata, annotations=mock_annotations
    )
    mock_lrclib = MockLRCLibAPI(lyrics=mock_lyrics_response)

    # Patch the API classes to return our mock instances
    with (
        patch("src.flows.ingestion.subflows.GeniusAPI", return_value=mock_genius),
        patch("src.flows.ingestion.subflows.LRCLibAPI", return_value=mock_lrclib),
    ):
        # Run the flow
        result = song_ingestion_flow(
            song_name="Yesterday", artist_name="The Beatles", base_path=str(tmp_path)
        )

        # Verify the result
        assert result["song_name"] == "Yesterday"
        assert result["artist_name"] == "The Beatles"
        assert result["id"] == 2236

        # Check that files were created
        song_dir = get_song_dir(tmp_path, 2236)
        assert (song_dir / "genius_metadata.json").exists()
        assert (song_dir / "genius_annotations.json").exists()
        assert (song_dir / "lyrics.json").exists()

        # Verify catalog was updated
        catalog_path = get_songs_catalog_path(tmp_path)
        assert catalog_path.exists()
        with open(catalog_path) as f:
            catalog = json.load(f)
            assert len(catalog) == 1
            assert catalog[0]["id"] == 2236


def test_song_ingestion_flow_no_metadata(tmp_path: Path) -> None:
    """Test the flow when no metadata is found"""
    mock_genius = MockGeniusAPI(metadata=None, annotations=None)

    with patch("src.flows.ingestion.subflows.GeniusAPI", return_value=mock_genius):
        result = song_ingestion_flow(
            song_name="Nonexistent Song",
            artist_name="Unknown Artist",
            base_path=str(tmp_path),
        )
        assert result == {"song_path": None}
