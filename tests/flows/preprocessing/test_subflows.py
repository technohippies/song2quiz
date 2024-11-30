import json
from pathlib import Path

from src.flows.preprocessing.subflows import process_song_annotations_flow


def test_process_song_annotations_flow(tmp_path: Path) -> None:
    """Test the preprocessing flow end-to-end"""
    # Create mock song directory with required files
    song_id = 2236
    song_dir = tmp_path / "data" / "songs" / str(song_id)
    song_dir.mkdir(parents=True)

    # Create mock genius_annotations.json
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

    # Create mock lyrics.json with synced lyrics
    lyrics = {
        "id": 123,
        "name": "Test Song",
        "artistName": "Test Artist",
        "syncedLyrics": "[00:00.00] Test fragment\n[00:05.00] Another line",
        "plainLyrics": "Test fragment\nAnother line",
    }

    with open(song_dir / "lyrics.json", "w") as f:
        json.dump(lyrics, f)

    # Run the flow
    result = process_song_annotations_flow(song_id, base_path=tmp_path)

    assert result is True

    # Check all expected files exist
    assert (song_dir / "lyrics_processed.json").exists()
    assert (song_dir / "annotations_cleaned.json").exists()
    assert (song_dir / "lyrics_with_annotations.json").exists()

    # Verify processed lyrics format
    with open(song_dir / "lyrics_processed.json") as f:
        processed_lyrics = json.load(f)
        assert "source" in processed_lyrics
        assert "has_timestamps" in processed_lyrics
        assert "timestamped_lines" in processed_lyrics
        assert len(processed_lyrics["timestamped_lines"]) == 2

    # Verify annotations were matched
    with open(song_dir / "lyrics_with_annotations.json") as f:
        matched_data = json.load(f)
        assert matched_data["lyrics_source"] == "lrclib"
        assert matched_data["annotations_source"] == "genius"
        assert matched_data["has_timestamps"] is True
        assert len(matched_data["lyrics"]) == 2
        assert matched_data["lyrics"][0]["text"] == "Test fragment"
        assert matched_data["lyrics"][0]["annotation"] is not None
