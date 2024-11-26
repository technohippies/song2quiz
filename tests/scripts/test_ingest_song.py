"""Test the song ingestion CLI."""

from click.testing import CliRunner
from unittest.mock import patch
from src.scripts.ingest_song import main as ingest_cli

def test_ingest_song_cli_success(tmp_path):
    """Test successful song ingestion via CLI"""
    runner = CliRunner()
    with patch('src.flows.ingestion.subflows.song_ingestion_flow') as mock_flow:
        # Mock successful ingestion
        mock_flow.return_value = {
            "song_path": str(tmp_path / "data/songs/2236"),
            "id": 2236,
            "song_name": "Yesterday",
            "artist_name": "The Beatles"
        }
        
        result = runner.invoke(
            ingest_cli, 
            ['--song', 'Yesterday', 
             '--artist', 'The Beatles',
             '--data-dir', str(tmp_path)]
        )
        
        assert result.exit_code == 0
        mock_flow.assert_called_once_with(
            song_name="Yesterday",
            artist_name="The Beatles",
            base_path=str(tmp_path)
        )

def test_ingest_song_cli_failure(tmp_path):
    """Test CLI behavior when ingestion fails"""
    runner = CliRunner()
    with patch('src.flows.ingestion.subflows.song_ingestion_flow') as mock_flow:
        # Mock failed ingestion
        mock_flow.return_value = {"song_path": None}
        
        result = runner.invoke(
            ingest_cli, 
            ['--song', 'Nonexistent', 
             '--artist', 'Unknown',
             '--data-dir', str(tmp_path)]
        )
        
        print("\nTest Debug Output:")
        print(f"Exit Code: {result.exit_code}")
        print(f"Output: {result.output}")
        print(f"Exception: {result.exception}")
        
        assert result.exit_code != 0