"""Test the song ingestion CLI."""

from unittest.mock import patch

from click.testing import CliRunner

from src.scripts.ingest_song import ingest_song_cli as cli


@patch('src.flows.ingestion.subflows.song_ingestion_flow')
def test_ingest_song_cli_success(mock_flow):
    """Test successful CLI invocation"""
    runner = CliRunner()
    # Mock a successful response
    mock_flow.return_value = {
        "song_path": "data/songs/2236",
        "id": 2236
    }

    result = runner.invoke(cli, ['--song', 'Yesterday', '--artist', 'The Beatles'])
    assert result.exit_code == 0
    mock_flow.assert_called_once_with(
        song_name='Yesterday',
        artist_name='The Beatles',
        base_path='data'
    )


def test_ingest_song_cli_failure(tmp_path):
    """Test CLI behavior when ingestion fails"""
    runner = CliRunner()
    with patch("src.flows.ingestion.subflows.song_ingestion_flow") as mock_flow:
        # Mock failed ingestion
        mock_flow.return_value = {"song_path": None}

        result = runner.invoke(
            cli,
            [
                "--song",
                "Nonexistent",
                "--artist",
                "Unknown",
                "--data-dir",
                str(tmp_path),
            ],
        )

        assert result.exit_code != 0
