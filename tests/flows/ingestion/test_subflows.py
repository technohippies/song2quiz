import json
from unittest.mock import patch

import pytest

from src.flows.ingestion.subflows import song_ingestion_flow
from src.utils.io.paths import get_song_dir, get_songs_catalog_path


@pytest.fixture
def mock_genius_response():
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
def mock_lyrics_response():
    """Mock response for LRCLib API"""
    return {"lyrics": "Test lyrics", "syncedLyrics": "[00:00.00]Test lyrics"}


@pytest.fixture
def mock_annotations():
    """Mock Genius annotations - simplified structure based on actual API response"""
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


def test_song_ingestion_flow(
    tmp_path, mock_genius_response, mock_lyrics_response, mock_annotations
):
    """Test the song ingestion flow with mocked API responses"""

    # Mock the API calls
    with patch("src.services.genius.GeniusAPI") as MockGenius:
        # Configure mock responses
        genius_instance = MockGenius.return_value
        genius_instance.search_song.return_value = mock_genius_response
        genius_instance.get_song_annotations.return_value = mock_annotations

        # Run the flow
        result = song_ingestion_flow(
            song_name="Yesterday", artist_name="The Beatles", base_path=str(tmp_path)
        )

        # Verify the result
        assert result["song_name"] == "Yesterday"
        assert result["artist_name"] == "The Beatles"
        assert result["id"] == 2236

        # Check that files were created in the correct location
        song_dir = get_song_dir(tmp_path, 2236)
        assert (song_dir / "genius_metadata.json").exists()
        assert (song_dir / "genius_annotations.json").exists()
        assert (song_dir / "lyrics.json").exists()

        # Verify catalog was updated with correct path
        catalog_path = get_songs_catalog_path(tmp_path)
        assert catalog_path.exists(), f"Catalog file not found at {catalog_path}"

        with open(catalog_path) as f:
            catalog = json.load(f)
            assert len(catalog) == 1
            assert catalog[0]["id"] == 2236


def test_song_ingestion_flow_no_metadata(tmp_path):
    """Test the flow when no metadata is found"""

    with patch("src.services.genius.GeniusAPI") as MockGenius:
        # Configure mock to return None for metadata
        genius_instance = MockGenius.return_value
        genius_instance.search_song.return_value = None

        # Run the flow
        result = song_ingestion_flow(
            song_name="Nonexistent Song",
            artist_name="Unknown Artist",
            base_path=str(tmp_path),
        )

        # Verify the result indicates failure
        assert result["song_path"] is None
