#!/usr/bin/env python3
"""Script to analyze parentheticals in song lyrics."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from src.tasks.lyrics_analysis.parentheticals import analyze_parentheticals
from src.utils.io.json import load_json
from src.utils.io.paths import get_songs_dir

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

logger = logging.getLogger(__name__)


async def analyze_song_parentheticals(song_path: Path) -> Dict[str, Any]:
    """Extract parentheticals from a song's lyrics."""
    try:
        # Load lyrics
        lyrics_path = song_path / "lyrics_with_annotations.json"
        if not lyrics_path.exists():
            logger.warning(f"❌ No lyrics found for {song_path.name}")
            return {}

        lyrics_data = load_json(lyrics_path)

        # Process each line
        results = []
        all_lyrics = [
            line["text"] for line in lyrics_data["lyrics"] if line["text"].strip()
        ]

        for line in all_lyrics:
            analysis = analyze_parentheticals(line)
            if analysis["parentheticals"]:
                results.append(
                    {
                        "line": line,
                        "line_without_parentheses": analysis[
                            "line_without_parentheses"
                        ],
                        "parentheticals": analysis["parentheticals"],
                    }
                )

        # Save results
        output = {
            "total_lines": len(all_lyrics),
            "lines_with_parentheticals": len(results),
            "results": results,
        }

        output_path = song_path / "parentheticals_analysis.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return output

    except Exception as e:
        logger.error(f"❌ Error analyzing song: {str(e)}")
        return {}


async def main() -> None:
    """Main entry point."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    songs_dir = get_songs_dir(base_dir)

    for song_dir in songs_dir.iterdir():
        if song_dir.is_dir():
            logger.info(f"Analyzing song in {song_dir.name}")
            output = await analyze_song_parentheticals(song_dir)
            if output:
                logger.info(
                    f"✅ Found {output['lines_with_parentheticals']} lines with parentheticals out of {output['total_lines']} total lines"
                )


if __name__ == "__main__":
    asyncio.run(main())
