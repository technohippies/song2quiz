"""Models for LRCLib lyrics data."""

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional


@dataclass
class TimestampedLine:
    """A single line of lyrics with its timestamp."""
    timestamp: timedelta  # Stores as timedelta for easy manipulation
    text: str

    @classmethod
    def from_lrc_line(cls, line: str) -> Optional['TimestampedLine']:
        """Parse a line with LRC timestamp format [mm:ss.xx]"""
        match = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)', line)
        if not match:
            return None

        minutes, seconds, centiseconds = map(int, match.groups()[:3])
        text = match.group(4).strip()

        timestamp = timedelta(
            minutes=minutes,
            seconds=seconds,
            milliseconds=centiseconds*10
        )

        return cls(timestamp=timestamp, text=text)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        total_seconds = self.timestamp.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        centiseconds = int((total_seconds * 100) % 100)

        return {
            "timestamp": f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}",
            "text": self.text
        }

@dataclass
class LRCLibLyrics:
    """Complete lyrics data from LRCLib."""
    source: str = "lrclib"
    match_score: float = 1.0
    lyrics: str = ""  # Raw LRC format with timestamps
    has_timestamps: bool = False
    plain_lyrics: str = ""  # Just the text without timestamps

    @property
    def timestamped_lines(self) -> list[TimestampedLine]:
        """Parse lyrics into timestamped lines if has_timestamps is True."""
        if not self.has_timestamps:
            return []

        lines = []
        for line in self.lyrics.split('\n'):
            if parsed := TimestampedLine.from_lrc_line(line):
                lines.append(parsed)

        return sorted(lines, key=lambda x: x.timestamp)

    @property
    def lines(self) -> list[str]:
        """Get just the text lines without timestamps."""
        return [line.strip() for line in self.plain_lyrics.split('\n') if line.strip()]

    def get_line_at_time(self, time: timedelta) -> Optional[str]:
        """Get the lyrics line that should be displayed at a given time."""
        if not self.has_timestamps:
            return None

        lines = self.timestamped_lines
        for i, line in enumerate(lines):
            # If this is the last line or we're before the next timestamp
            if i == len(lines) - 1 or time < lines[i + 1].timestamp:
                if time >= line.timestamp:
                    return line.text
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "match_score": self.match_score,
            "lyrics": self.lyrics,
            "has_timestamps": self.has_timestamps,
            "plain_lyrics": self.plain_lyrics,
            "timestamped_lines": [line.to_dict() for line in self.timestamped_lines] if self.has_timestamps else []
        }
