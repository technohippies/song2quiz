from unittest.mock import patch

from click.testing import CliRunner

from src.scripts.preprocess_song import main as preprocess_cli


def test_preprocess_song_cli_with_id(tmp_path):
    """Test preprocessing with song ID"""
    runner = CliRunner()

    # Create data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)

    with patch('src.flows.preprocessing.subflows.process_song_annotations_flow') as mock_flow:
        mock_flow.return_value = True  # Mock successful preprocessing

        result = runner.invoke(
            preprocess_cli,
            ['--song-id', '2236',
             '--data-dir', str(tmp_path)]
        )

        assert result.exit_code == 0
        mock_flow.assert_called_once_with(song_id=2236, base_path=str(tmp_path))

def test_preprocess_song_cli_with_name(tmp_path):
    """Test preprocessing with song name and artist"""
    runner = CliRunner()

    # Create mock metadata file
    song_dir = tmp_path / "data" / "songs" / "2236"
    song_dir.mkdir(parents=True)
    with open(song_dir / "genius_metadata.json", "w") as f:
        import json
        json.dump({
            "title": "Yesterday",
            "artist": "The Beatles"
        }, f)

    with patch('src.flows.preprocessing.subflows.process_song_annotations_flow') as mock_flow:
        mock_flow.return_value = True

        result = runner.invoke(
            preprocess_cli,
            ['--song', 'Yesterday',
             '--artist', 'The Beatles',
             '--data-dir', str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✅ Preprocessing completed successfully" in result.output
