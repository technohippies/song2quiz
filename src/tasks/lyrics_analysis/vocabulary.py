"""Prefect tasks for vocabulary analysis."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from prefect import get_run_logger, task

from src.prompts.lyrics_analysis.vocabulary.system import SYSTEM_PROMPT
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt

logger = logging.getLogger(__name__)

@task(name="analyze_fragment",
      retries=3,
      retry_delay_seconds=2,
      tags=["api"])
async def analyze_fragment(
    fragment: Dict[str, Any],
    index: Optional[int] = None,
    total: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Analyze vocabulary in a lyrics fragment."""
    try:
        logger.info(f"Processing fragment {index}/{total}" if index and total else "Processing fragment")
        logger.info(f"Fragment text: {fragment['text']}")

        response = await complete_openrouter_prompt(
            formatted_prompt=fragment["text"],
            system_prompt=SYSTEM_PROMPT,
            task_type="vocabulary"
        )
        logger.info(f"OpenRouter Response: {response}")

        if response and "choices" in response and response["choices"]:
            try:
                content = response["choices"][0]["message"]["content"]
                logger.info(f"Response Content: {content}")

                if not content:
                    logger.error("Empty content in response")
                    return None

                vocabulary_data = json.loads(content)
                if not isinstance(vocabulary_data, dict) or "vocabulary" not in vocabulary_data:
                    logger.error(f"Invalid vocabulary data structure: {vocabulary_data}")
                    return None
                
                # Return None if there are no vocabulary terms
                if not vocabulary_data["vocabulary"]:
                    return None
                    
                # Create the expected response structure
                return {
                    "vocabulary": [
                        {
                            "original": fragment["text"],
                            "id": fragment["id"],
                            "timestamp": fragment["timestamp"],
                            "vocabulary": vocabulary_data["vocabulary"]
                        }
                    ]
                }
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Error parsing response: {str(e)}")
                logger.error(f"Response structure: {response}")
                return None
        else:
            logger.error(f"Invalid response structure: {response}")
            return None
    except Exception as e:
        logger.error(f"Error analyzing fragment: {str(e)}")
        return None

@task(name="process_batch",
      retries=2,
      retry_delay_seconds=5,
      tags=["batch"])
async def process_batch(fragments: List[Dict[str, str]], start_index: int, total: int) -> List[Dict[str, Any]]:
    """Process a batch of fragments concurrently."""
    # Filter out invalid fragments
    valid_fragments = [(i+start_index, f) for i, f in enumerate(fragments, 1)
                      if f and isinstance(f, dict) and "text" in f and "id" in f and "timestamp" in f]

    if not valid_fragments:
        return []

    # Create tasks for all fragments
    tasks = [analyze_fragment(fragment, idx, total) for idx, fragment in valid_fragments]

    # Run all tasks concurrently and collect results
    results = await asyncio.gather(*tasks)

    # Filter out None results
    return [r for r in results if r is not None]

@task(name="analyze_song_vocabulary",
      retries=3,
      retry_delay_seconds=2)
async def analyze_song_vocabulary(song_path: str) -> Optional[Dict[str, Any]]:
    """Analyze vocabulary for a song."""
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
        fragments = [{"original": line["text"]} for line in lyrics_data["lyrics"]]

        # Process fragments in batches
        batch_size = 5
        all_results = []

        # Process batches sequentially but fragments within batch concurrently
        for i in range(0, len(fragments), batch_size):
            batch = fragments[i:i + batch_size]
            try:
                batch_results = await process_batch(batch, i, len(fragments))
                all_results.extend(batch_results)
                log.info(f"Completed batch {i//batch_size + 1}/{(len(fragments) + batch_size - 1)//batch_size}")
            except Exception as e:
                log.error(f" Batch processing failed at index {i}: {str(e)}")
                log.exception("Full traceback:")
                continue  # Skip failed batch but continue with others

        # Combine results
        all_vocabulary = []
        total_terms = 0
        seen_terms = set()  # Track unique terms to avoid duplicates

        for result in all_results:
            if result and isinstance(result, dict) and "vocabulary" in result:
                terms = result["vocabulary"][0]["vocabulary"]
                original = result["vocabulary"][0].get("original", "")
                id = result["vocabulary"][0].get("id", "")
                timestamp = result["vocabulary"][0].get("timestamp", "")

                # Create an entry for this line if it has vocabulary terms
                if terms:
                    line_entry = {
                        "id": id,
                        "timestamp": timestamp,
                        "original": original,
                        "vocabulary": []
                    }

                    for term in terms:
                        # Only add unique terms
                        term_key = (term["term"].lower(), term["vocabulary_type"])
                        if term_key not in seen_terms:
                            seen_terms.add(term_key)
                            total_terms += 1
                            line_entry["vocabulary"].append(term)
                            log.info(f"Found unique term: {term['term']} ({term['vocabulary_type']})")

                    if line_entry["vocabulary"]:  # Only add if we found terms
                        all_vocabulary.append(line_entry)

        # Save results
        output_file = path / "vocabulary_analysis.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"vocabulary": all_vocabulary}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f" Failed to save results: {str(e)}")
            log.exception("Full traceback:")
            return None

        log.info(f" Analysis complete - found {total_terms} unique vocabulary terms")
        log.info(f"Results saved to {output_file}")
        return {"vocabulary": all_vocabulary}

    except Exception as e:
        log.error(f" Error analyzing vocabulary for {song_path}: {str(e)}")
        log.exception("Full traceback:")
        raise  # Let Prefect handle the retry
