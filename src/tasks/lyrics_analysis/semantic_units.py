"""Task for analyzing semantic units in lyrics."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from prefect import get_run_logger, task

from src.prompts.lyrics_analysis.semantic_units.examples import EXAMPLES
from src.prompts.lyrics_analysis.semantic_units.system import SYSTEM_PROMPT
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt

logger = logging.getLogger(__name__)

BATCH_SIZE = 20

def format_prompt(examples: List[Dict[str, Any]], line: str) -> str:
    """Format prompt with examples."""
    examples_text = "\n\n".join([
        f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'], indent=2)}"
        for ex in examples[:2]  # Use first 2 examples
    ])

    return f"{SYSTEM_PROMPT}\n\nHere are some examples:\n{examples_text}\n\nNow analyze this line:\n{line}"

@task(name="analyze_fragment",
      retries=3,
      retry_delay_seconds=2)
async def analyze_fragment(fragment: Dict[str, str], index: int, total: int) -> Optional[Dict[str, Any]]:
    """Analyze a single fragment for semantic units."""
    log = get_run_logger()
    try:
        # Format prompt with examples
        prompt = format_prompt(EXAMPLES, fragment['text'])

        response = await complete_openrouter_prompt(
            formatted_prompt=prompt,
            system_prompt="",  # System prompt included in formatted prompt
            task_type="analysis",
            temperature=0.1
        )

        if not response:
            log.error(f"[{index}/{total}] Invalid API response")
            return None

        return response

    except Exception as e:
        log.error(f"[{index}/{total}] Error analyzing fragment: {e}")
        return None

@task(name="analyze_song_semantic_units",
      retries=3,
      retry_delay_seconds=2)
async def analyze_song_semantic_units(song_path: str) -> Optional[Dict[str, Any]]:
    """Analyze semantic units for a song."""
    log = get_run_logger()
    try:
        # Convert string path to Path object for proper path handling
        path = Path(song_path)

        # Read lyrics with annotations
        lyrics_path = path / "lyrics_with_annotations.json"
        if not lyrics_path.exists():
            log.error("No lyrics found")
            return None

        with open(lyrics_path, "r") as f:
            lyrics_data = json.load(f)

        # Extract lines for analysis
        fragments = [{"text": line["text"]} for line in lyrics_data["lyrics"]]

        # Process fragments in batches
        results = []
        total = len(fragments)

        for i in range(0, total, BATCH_SIZE):
            batch = fragments[i:i + BATCH_SIZE]
            batch_tasks = [analyze_fragment(f, idx, total)
                         for idx, f in enumerate(batch, i + 1)]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend([r for r in batch_results if r])
            log.info(f"✓ Processed batch {i//BATCH_SIZE + 1} ({i+1}-{min(i+BATCH_SIZE, total)})")

        if not results:
            log.error("No valid results from analysis")
            return None

        output = {"semantic_units_analysis": results}
        output_path = path / "semantic_units_analysis.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        log.info(f"✓ Analysis complete - processed {len(results)} fragments")
        return output

    except Exception as e:
        log.error(f"Error analyzing song: {e}")
        return None
