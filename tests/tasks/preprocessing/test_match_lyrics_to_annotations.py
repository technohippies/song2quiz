import json

import pytest
from prefect.logging.loggers import disable_run_logger

from src.tasks.preprocessing.match_lyrics_to_annotations import (
    match_lyrics_with_annotations,
)


@pytest.fixture
def mock_song_dir(tmp_path):
    """Create a temporary song directory with mock lyrics and annotations"""
    song_dir = tmp_path / "2236"
    song_dir.mkdir()

    # Create mock cleaned annotations
    cleaned_annotations = [
        {
            "id": 1,
            "fragment": "Yesterday",
            "annotation_text": "This is an annotation about yesterday",
        }
    ]

    with open(song_dir / "annotations_cleaned.json", "w") as f:
        json.dump(cleaned_annotations, f)

    # Create mock lyrics
    lyrics = {
        "source": "test",
        "timestamped_lines": [
            {"timestamp": "00:00.00", "text": "Yesterday"},
            {"timestamp": "00:05.00", "text": "All my troubles seemed so far away"},
        ],
    }

    with open(song_dir / "lyrics.json", "w") as f:
        json.dump(lyrics, f)

    return song_dir


def test_match_lyrics_success(mock_song_dir):
    """Test successful matching of lyrics with annotations"""
    with disable_run_logger():
        result = match_lyrics_with_annotations.fn(mock_song_dir)

    assert result is True

    # Check output file exists
    output_file = mock_song_dir / "lyrics_with_annotations.json"
    assert output_file.exists()

    # Verify content
    with open(output_file) as f:
        matched_data = json.load(f)

    assert "lyrics" in matched_data
    assert len(matched_data["lyrics"]) == 2
    assert matched_data["lyrics"][0]["text"] == "Yesterday"
    assert matched_data["lyrics"][0]["annotation"] is not None
    assert matched_data["lyrics"][1]["annotation"] is None  # No match for this line


def test_match_lyrics_no_annotations_file(tmp_path):
    """Test behavior when annotations file is missing"""
    empty_dir = tmp_path / "2236"
    empty_dir.mkdir()

    # Create only lyrics file
    lyrics = {"timestamped_lines": [{"timestamp": "00:00.00", "text": "Test line"}]}

    with open(empty_dir / "lyrics.json", "w") as f:
        json.dump(lyrics, f)

    with disable_run_logger():
        result = match_lyrics_with_annotations.fn(empty_dir)

    assert result is False


def test_match_lyrics_no_lyrics_file(tmp_path):
    """Test behavior when lyrics file is missing"""
    empty_dir = tmp_path / "2236"
    empty_dir.mkdir()

    with disable_run_logger():
        result = match_lyrics_with_annotations.fn(empty_dir)

    assert result is False


def test_match_lyrics_exact_match(mock_song_dir):
    """Test exact matching between lyrics and annotations"""
    # Override with exact matching test case
    cleaned_annotations = [
        {"id": 1, "fragment": "Yesterday", "annotation_text": "About the past"}
    ]

    with open(mock_song_dir / "annotations_cleaned.json", "w") as f:
        json.dump(cleaned_annotations, f)

    lyrics = {"timestamped_lines": [{"timestamp": "00:00.00", "text": "Yesterday"}]}

    with open(mock_song_dir / "lyrics.json", "w") as f:
        json.dump(lyrics, f)

    with disable_run_logger():
        result = match_lyrics_with_annotations.fn(mock_song_dir)

    assert result is True

    with open(mock_song_dir / "lyrics_with_annotations.json") as f:
        matched_data = json.load(f)
        first_line = matched_data["lyrics"][0]
        assert first_line["text"] == "Yesterday"
        assert first_line["annotation"] == "About the past"
        assert first_line["annotation_id"] == 1
