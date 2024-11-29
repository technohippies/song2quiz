"""Test the song ingestion CLI."""

import pytest
from click.testing import CliRunner

from src.scripts.ingest_song import ingest_song_cli as cli


@pytest.mark.integration  # Mark as integration test that requires API access
def test_ingest_song_cli_integration(tmp_path):
    """Test actual API integration and response structure"""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["--song", "Yesterday", "--artist", "The Beatles", "--data-dir", str(tmp_path)],
    )

    assert result.exit_code == 0

    # Look for any JSON files
    json_files = list(tmp_path.glob("**/*.json"))
    assert len(json_files) > 0, "No JSON files were created"
