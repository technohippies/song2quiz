import json

from src.flows.preprocessing.subflows import process_song_annotations_flow


def test_process_song_annotations_flow(tmp_path):
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

    # Create mock lyrics.json
    lyrics = {
        "timestamped_lines": [{"timestamp": "00:00", "text": "Test fragment"}],
        "source": "test",
    }

    with open(song_dir / "lyrics.json", "w") as f:
        json.dump(lyrics, f)

    # Run the flow
    result = process_song_annotations_flow(song_id, base_path=tmp_path)

    assert result is True
    assert (song_dir / "annotations_cleaned.json").exists()
    assert (song_dir / "lyrics_with_annotations.json").exists()
