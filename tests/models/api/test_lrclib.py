"""Tests for LRCLib models."""

from datetime import timedelta

from src.models.api.lrclib import LRCLibLyrics, TimestampedLine


def test_timestamped_line_from_lrc() -> None:
    """Test parsing LRC format lines."""
    # Test valid line
    line = TimestampedLine.from_lrc_line("[00:01.23]Hello world")
    assert line is not None
    assert line.timestamp == timedelta(seconds=1, milliseconds=230)
    assert line.text == "Hello world"

    # Test invalid line
    assert TimestampedLine.from_lrc_line("Invalid line") is None


def test_empty_line_filtering() -> None:
    """Test that empty lines and '...' lines are filtered out."""
    lyrics_with_empty = """[00:01.00]First line
[00:02.00]
[00:03.00]...
[00:04.00]Second line
[00:05.00]
[00:06.00]Third line"""

    lyrics = LRCLibLyrics(
        lyrics=lyrics_with_empty,
        has_timestamps=True,
        plain_lyrics="First line\n\n...\nSecond line\n\nThird line",
    )

    # Test timestamped_lines property
    timestamped = lyrics.timestamped_lines
    assert len(timestamped) == 3
    assert [line.text for line in timestamped] == [
        "First line",
        "Second line",
        "Third line",
    ]

    # Test lines property
    plain_lines = lyrics.lines
    assert plain_lines == ["First line", "Second line", "Third line"]


def test_line_with_only_whitespace() -> None:
    """Test that lines with only whitespace are filtered out."""
    lyrics_with_spaces = """[00:01.00]First line
[00:02.00]  \t  \n
[00:03.00]Second line
[00:04.00]   \t   """

    lyrics = LRCLibLyrics(
        lyrics=lyrics_with_spaces,
        has_timestamps=True,
        plain_lyrics="First line\n  \t  \nSecond line\n   \t   ",
    )

    timestamped = lyrics.timestamped_lines
    assert len(timestamped) == 2
    assert [line.text for line in timestamped] == ["First line", "Second line"]

    plain_lines = lyrics.lines
    assert plain_lines == ["First line", "Second line"]


def test_line_with_only_dots() -> None:
    """Test that lines with variations of '...' are filtered out."""
    lyrics_with_dots = """[00:01.00]First line
[00:02.00]...
[00:03.00]Second line
[00:04.00].....
[00:05.00]Third line"""

    lyrics = LRCLibLyrics(
        lyrics=lyrics_with_dots,
        has_timestamps=True,
        plain_lyrics="First line\n...\nSecond line\n.....\nThird line",
    )

    timestamped = lyrics.timestamped_lines
    assert len(timestamped) == 3
    assert [line.text for line in timestamped] == [
        "First line",
        "Second line",
        "Third line",
    ]

    plain_lines = lyrics.lines
    assert plain_lines == ["First line", "Second line", "Third line"]
