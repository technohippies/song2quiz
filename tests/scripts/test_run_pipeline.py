import pytest
from click.testing import CliRunner
from unittest.mock import patch
from src.scripts.run_pipeline import main as pipeline_cli

def test_run_pipeline_cli_all_steps(tmp_path):
    """Test running full pipeline"""
    runner = CliRunner()
    
    # Create data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    
    with patch('src.flows.ingestion.subflows.song_ingestion_flow') as mock_ingest, \
         patch('src.flows.preprocessing.subflows.process_song_annotations_flow') as mock_preprocess:
        
        # Mock successful ingestion
        mock_ingest.return_value = {
            "song_path": str(tmp_path / "data/songs/2236"),
            "id": 2236,
            "song_name": "Yesterday",
            "artist_name": "The Beatles"
        }
        
        # Mock successful preprocessing
        mock_preprocess.return_value = True
        
        result = runner.invoke(
            pipeline_cli,
            ['--song', 'Yesterday',
             '--artist', 'The Beatles',
             '--data-dir', str(tmp_path)]
        )
        
        assert result.exit_code == 0
        mock_ingest.assert_called_once()
        mock_preprocess.assert_called_once()

def test_run_pipeline_cli_ingest_only(tmp_path):
    """Test running only ingestion step"""
    runner = CliRunner()
    
    with patch('src.flows.ingestion.subflows.song_ingestion_flow') as mock_ingest:
        mock_ingest.return_value = {
            "song_path": str(tmp_path / "data/songs/2236"),
            "id": 2236
        }
        
        result = runner.invoke(
            pipeline_cli,
            ['--song', 'Yesterday',
             '--artist', 'The Beatles',
             '--data-dir', str(tmp_path),
             '--steps', 'ingest']
        )
        
        assert result.exit_code == 0
        mock_ingest.assert_called_once() 