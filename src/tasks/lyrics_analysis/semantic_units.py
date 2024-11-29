"""Task for analyzing semantic units in lyrics."""

import asyncio
import json
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, cast

from prefect import get_run_logger, task

from src.prompts.lyrics_analysis.semantic_units.examples import EXAMPLES
from src.prompts.lyrics_analysis.semantic_units.system import SYSTEM_PROMPT
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt

BATCH_SIZE = 5

T = TypeVar('T')

def format_prompt(examples: List[Dict[str, Any]], line: str) -> str:
    """Format prompt with examples."""
    examples_text = "\n".join(
        f"Input: {e['text']}\nOutput: {json.dumps(e['analysis'])}" for e in examples
    )
    return f"{SYSTEM_PROMPT}\n\nHere are some examples:\n{examples_text}\n\nNow analyze this line:\n{line}"


@task(name="analyze_fragment", retries=3, retry_delay_seconds=2)
async def analyze_fragment(
    fragment: Dict[str, str], index: int, total: int
) -> Optional[Dict[str, Any]]:
    """Analyze a single fragment for semantic units."""
    log = get_run_logger()

    try:
        prompt = format_prompt(EXAMPLES, fragment["text"])
        log.info(f"[{index}/{total}] Formatted prompt for text: {fragment['text'][:50]}...")

        async def _try_analyze() -> Optional[Dict[str, Any]]:
            openrouter_fn = cast(
                Callable[..., Awaitable[Optional[Dict[str, Any]]]],
                complete_openrouter_prompt
            )
            try:
                response = await openrouter_fn(
                    formatted_prompt=prompt,
                    system_prompt="",
                    task_type="analysis",
                    temperature=0.1,
                )
                if not response or 'choices' not in response:
                    log.error(f"[{index}/{total}] Invalid API response: {response}")
                    return None
                return response
            except Exception as e:
                log.error(f"[{index}/{total}] Error in _try_analyze: {str(e)}")
                raise  # Re-raise for retry logic in outer try block

        for attempt in range(3):
            try:
                result = await _try_analyze()
                if result is not None:
                    return result
            except Exception as e:
                log.error(f"[{index}/{total}] Error analyzing fragment: {str(e)}")
                if "rate limit exceeded" in str(e).lower() and attempt < 2:
                    delay = 2 ** attempt
                    log.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/3)")
                    await asyncio.sleep(delay)
                    continue
                elif attempt < 2:  # For other errors, retry if not last attempt
                    continue
                else:
                    return None  # Return None after all retries are exhausted

        return None

    except Exception as e:
        log.error(f"[{index}/{total}] Error analyzing fragment: {str(e)}")
        return None  # Return None for any unhandled exceptions


@task(name="analyze_song_semantic_units", retries=3, retry_delay_seconds=2)
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
            batch = fragments[i : i + BATCH_SIZE]
            batch_tasks = [
                analyze_fragment(f, idx, total) for idx, f in enumerate(batch, i + 1)
            ]
            batch_results = await asyncio.gather(*[t for t in batch_tasks if t is not None])
            results.extend([r for r in batch_results if r])
            log.info(
                f"✓ Processed batch {i//BATCH_SIZE + 1} ({i+1}-{min(i+BATCH_SIZE, total)})"
            )

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
