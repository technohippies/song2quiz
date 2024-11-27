"""Prefect tasks for semantic units analysis."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from prefect import task, get_run_logger
import asyncio

from src.tasks.api.openrouter_tasks import complete_openrouter_prompt
from src.prompts.lyrics_analysis.semantic_units.system import SYSTEM_PROMPT
from src.prompts.lyrics_analysis.semantic_units.examples import EXAMPLES
from src.models.lyrics_analysis.semantic_unit import SemanticUnitsAnalysis
from src.utils.io.paths import get_song_dir

logger = logging.getLogger(__name__)

@task(name="analyze_fragment",
      retries=3,
      retry_delay_seconds=2,
      tags=["api"])
async def analyze_fragment(fragment: Dict[str, str], index: int, total: int) -> Optional[Dict[str, Any]]:
    """Analyze a single fragment for semantic units."""
    log = get_run_logger()
    try:
        # Build prompt with examples for few-shot learning
        examples_text = "\n\n".join([
            f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'], indent=2)}"
            for ex in EXAMPLES[:2]  # Use first 2 examples for few-shot learning
        ])
        
        # Format the prompt
        formatted_prompt = f"Now analyze this line:\n{fragment['original']}"
        
        # Make API request
        response = await complete_openrouter_prompt(
            formatted_prompt=formatted_prompt,
            system_prompt=f"{SYSTEM_PROMPT}\n\nHere are some examples:\n{examples_text}",
            task_type="analysis",  # Use analysis model from OPENROUTER_MODELS
            temperature=0.1  # Low temperature for consistent analysis
        )
        
        if not response:
            log.error(f"[{index}/{total}] No response from API")
            return None
            
        try:
            # Parse and validate response
            result = json.loads(response["choices"][0]["message"]["content"])
            analysis = SemanticUnitsAnalysis(**result)
            return analysis.dict()
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            log.error(f"[{index}/{total}] Error parsing response: {e}")
            return None
            
    except Exception as e:
        log.error(f"[{index}/{total}] Error analyzing fragment: {e}")
        return None

@task(name="process_batch")
async def process_batch(fragments: List[Dict[str, str]], start_index: int, total: int) -> List[Dict[str, Any]]:
    """Process a batch of fragments concurrently."""
    tasks = []
    for i, fragment in enumerate(fragments, start=start_index):
        tasks.append(analyze_fragment(fragment, i, total))
    return [result for result in await asyncio.gather(*tasks) if result is not None]

@task(name="analyze_song_semantic_units")
async def analyze_song_semantic_units(song_path: str) -> None:
    """Analyze semantic units for a song."""
    log = get_run_logger()
    
    # Convert string path to Path object
    song_path = Path(song_path)
    
    # Load lyrics with annotations
    lyrics_path = song_path / "lyrics_with_annotations.json"
    if not lyrics_path.exists():
        log.error(f" No lyrics with annotations found at {lyrics_path}")
        return
        
    with open(lyrics_path) as f:
        lyrics_data = json.load(f)
    
    # Extract lyrics lines
    fragments = [{"id": line["id"], "original": line["text"]} for line in lyrics_data["lyrics"]]
    total_fragments = len(fragments)
    
    # Process in batches
    batch_size = 5
    results = []
    
    for batch_start in range(0, total_fragments, batch_size):
        batch = fragments[batch_start:batch_start + batch_size]
        batch_results = await process_batch(batch, batch_start + 1, total_fragments)
        results.extend([r for r in batch_results if r])
    
    # Save results
    output_path = song_path / "semantic_units_analysis.json"
    with open(output_path, "w") as f:
        json.dump({"semantic_units": results}, f, indent=2)
    
    log.info(f" Saved semantic units analysis to {output_path}")