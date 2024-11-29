from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from src.scripts.run_pipeline import run_pipeline_cli as cli


def test_run_pipeline_cli_ingest_only(tmp_path):
    """Test running only ingestion step"""
    runner = CliRunner()

    with patch("src.scripts.run_pipeline.find_song_id") as mock_find_id, \
         patch("src.flows.ingestion.subflows.song_ingestion_flow", new_callable=AsyncMock) as mock_ingest:
        # Mock find_song_id to return a valid ID
        mock_find_id.return_value = "2236"
        mock_ingest.return_value = {
            "song_path": str(tmp_path / "data/songs/2236"),
            "id": 2236,
        }

        result = runner.invoke(
            cli, [
                "--song", "Yesterday",
                "--artist", "The Beatles",
                "--data-dir", str(tmp_path),
                "--steps", "ingest"
            ]
        )

        assert result.exit_code == 0
        mock_ingest.assert_called_once()


def test_run_pipeline_cli_all_steps(tmp_path, mock_genius):
    """Test running full pipeline"""
    runner = CliRunner()

    with patch("src.scripts.run_pipeline.find_song_id") as mock_find_id, \
         patch("src.flows.ingestion.subflows.song_ingestion_flow", new_callable=AsyncMock) as mock_ingest, \
         patch("src.flows.preprocessing.subflows.process_song_annotations_flow", new_callable=AsyncMock) as mock_process, \
         patch("src.flows.generation.main.main", new_callable=AsyncMock) as mock_generate:
        # Mock find_song_id to return a valid ID
        mock_find_id.return_value = "2236"
        song_path = str(tmp_path / "data/songs/2236")
        mock_ingest.return_value = {
            "song_path": song_path,
            "id": 2236,
            "song_name": "Yesterday",
            "artist_name": "The Beatles",
        }
        mock_process.return_value = True
        mock_generate.return_value = True

        result = runner.invoke(
            cli, ["--song", "Yesterday", "--artist", "The Beatles"]
        )

        assert result.exit_code == 0
        mock_ingest.assert_called_once()
        mock_process.assert_called_once_with(
            song_id=2236,
            batch_size=15,
            max_retries=3
        )
        mock_generate.assert_called_once_with(
            song_id="2236",
            batch_size=15,
            max_retries=3
        )
