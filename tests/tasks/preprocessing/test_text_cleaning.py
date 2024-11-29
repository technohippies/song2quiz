import json

import pytest
from prefect.logging.loggers import disable_run_logger

from src.tasks.preprocessing.text_cleaning import process_annotations


@pytest.fixture
def mock_song_path(tmp_path):
    """Create a temporary song directory with mock annotation data"""
    song_dir = tmp_path / "test_song"
    song_dir.mkdir()

    # Create mock annotations file
    annotations = [
        {
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

    with open(song_dir / "genius_annotations.json", "w") as f:
        json.dump(annotations, f)

    return song_dir


def test_process_annotations_success(mock_song_path):
    """Test successful processing of annotations"""
    with disable_run_logger():
        result = process_annotations.fn(mock_song_path)

    assert result is True

    # Check output file exists and contains expected data
    output_file = mock_song_path / "annotations_cleaned.json"
    assert output_file.exists()

    with open(output_file) as f:
        cleaned_data = json.load(f)

    assert len(cleaned_data) == 1
    assert cleaned_data[0]["id"] == 1
    assert "fragment" in cleaned_data[0]
    assert "annotation_text" in cleaned_data[0]


def test_process_annotations_no_input_file(tmp_path):
    """Test behavior when input file doesn't exist"""
    empty_dir = tmp_path / "empty_song"
    empty_dir.mkdir()

    with disable_run_logger():
        result = process_annotations.fn(empty_dir)

    assert result is False
