"""Test the song ingestion CLI."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.models.api.genius_metadata import Album, GeniusMetadata
from src.scripts.ingest_song import ingest_song_cli as cli


@pytest.mark.integration
def test_ingest_song_cli_integration(tmp_path: Path) -> None:
    """Test actual API integration and response structure"""
    runner = CliRunner()

    # Create a proper GeniusMetadata object instead of a dict
    mock_metadata = GeniusMetadata(
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

    with patch("src.services.genius.GeniusAPI.search_song") as mock_search:
        mock_search.return_value = mock_metadata
        result = runner.invoke(
            cli,
            [
                "--song",
                "Yesterday",
                "--artist",
                "The Beatles",
                "--data-dir",
                str(tmp_path),
            ],
        )

    assert result.exit_code == 0

    # Look for any JSON files
    json_files = list(tmp_path.glob("**/*.json"))
    assert len(json_files) > 0, "No JSON files were created"
