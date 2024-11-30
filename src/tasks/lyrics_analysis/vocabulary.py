"""Prefect tasks for vocabulary analysis."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Dict, List, Optional

from prefect import get_run_logger, task
from typing_extensions import cast

from src.prompts.lyrics_analysis.vocabulary.system import SYSTEM_PROMPT
from src.services.akash import complete_akash_prompt
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt

logger = logging.getLogger(__name__)

EXAMPLES = [
    {
        "text": "I'm finna pull up in my whip",
        "analysis": {
            "vocabulary": [
                {
                    "term": "finna",
                    "vocabulary_type": "aave",
                    "definition": "going to, about to",
                    "usage_notes": "informal contraction of 'fixing to'",
                    "variants": ["fixing to", "gonna"],
                    "domain": "informal speech",
                },
                {
                    "term": "whip",
                    "vocabulary_type": "slang",
                    "definition": "car, vehicle",
                    "usage_notes": "informal term for a car, especially a nice or expensive one",
                    "variants": ["ride", "wheels"],
                    "domain": "automotive",
                },
            ]
        },
    },
    {
        "text": "Got my Yeezys on with the Gucci drip",
        "analysis": {
            "vocabulary": [
                {
                    "term": "Yeezys",
                    "vocabulary_type": "brand",
                    "definition": "Kanye West's shoe line with Adidas",
                    "usage_notes": "popular sneaker brand",
                    "variants": [],
                    "domain": "fashion",
                },
                {
                    "term": "Gucci",
                    "vocabulary_type": "brand",
                    "definition": "luxury fashion brand",
                    "usage_notes": "high-end fashion house",
                    "variants": [],
                    "domain": "fashion",
                },
                {
                    "term": "drip",
                    "vocabulary_type": "slang",
                    "definition": "fashionable clothing or accessories",
                    "usage_notes": "refers to stylish appearance",
                    "variants": ["swag", "style"],
                    "domain": "fashion",
                },
            ]
        },
    },
]


def format_prompt(examples: List[Dict[str, Any]], text: str) -> str:
    """Format prompt with examples."""
    examples_text = "\n".join(
        f"Input: {e['text']}\nOutput: {json.dumps(e['analysis'])}" for e in examples
    )
    return f"{SYSTEM_PROMPT}\n\nHere are some examples:\n{examples_text}\n\nNow analyze this line:\n{text}"


@task(name="analyze_fragment", retries=3, retry_delay_seconds=2, tags=["api"])
async def analyze_fragment(
    fragment: Dict[str, Any], index: Optional[int] = None, total: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Analyze vocabulary in a lyrics fragment."""
    try:
        logger.info("\n" + "=" * 100)
        logger.info(f"INPUT TEXT ({index}/{total}): {fragment.get('text', 'NO TEXT')}")

        # Try OpenRouter first
        response = await cast(
            Awaitable[Optional[Dict[str, Any]]],
            complete_openrouter_prompt(
                formatted_prompt=format_prompt(EXAMPLES, fragment["text"]),
                system_prompt="",  # System prompt is included in formatted_prompt
                task_type="vocabulary",
            ),
        )

        if not response or "choices" not in response or not response["choices"]:
            logger.error("No valid response from OpenRouter API")
            return None

        content = response["choices"][0]["message"]["content"]
        logger.info("\nOpenRouter API Response:")
        logger.info("-" * 100)
        logger.info(content)
        logger.info("-" * 100)

        # Check for truncation or malformed JSON
        if len(content) < 100 or not content.endswith("}"):
            logger.warning(
                f"OpenRouter truncation detected:\n"
                f"  - Length: {len(content)} chars\n"
                f"  - Last char: '{content[-1] if content else ''}'\n"
                f"  - Original text: {fragment['text']}\n"
                f"Falling back to Akash API..."
            )
            # Try Akash API instead
            akash_response = await complete_akash_prompt(
                formatted_prompt=format_prompt(EXAMPLES, fragment["text"]),
                system_prompt="",  # System prompt is included in formatted_prompt
                temperature=0.7,
            )
            if not akash_response or "choices" not in akash_response:
                logger.error("Akash API failed")
                return None
            content = akash_response["choices"][0]["message"]["content"]
            response = akash_response  # Use Akash response for tracking
            logger.info("\nAkash API Response:")
            logger.info("-" * 100)
            logger.info(content)
            logger.info("-" * 100)

        try:
            # Clean any potential markdown or formatting
            content = content.strip()
            if content.startswith("```"):
                logger.info("Found markdown code block")
                content = "\n".join(content.split("\n")[1:-1])
            content = content.strip()

            # Parse JSON content
            vocabulary_data = json.loads(content)
            if (
                not isinstance(vocabulary_data, dict)
                or "vocabulary" not in vocabulary_data
            ):
                logger.error(f"Invalid vocabulary data structure: {vocabulary_data}")
                return None

            if not vocabulary_data["vocabulary"]:
                logger.info("No vocabulary terms found in this fragment")
                return None

            result = {
                "vocabulary": [
                    {
                        "original": fragment["text"],
                        "id": fragment["id"],
                        "timestamp": fragment["timestamp"],
                        "vocabulary": vocabulary_data["vocabulary"],
                    }
                ]
            }
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Raw content: {content}")
            return None
        except KeyError as e:
            logger.error(f"Missing key in response: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error in analyze_fragment: {str(e)}")
        return None


@task(name="process_batch", retries=2, retry_delay_seconds=5, tags=["batch"])
async def process_batch(
    fragments: List[Dict[str, str]], start_index: int, total: int
) -> List[Dict[str, Any]]:
    """Process a batch of fragments concurrently."""
    # Filter out invalid fragments
    valid_fragments = [
        (i + start_index, f)
        for i, f in enumerate(fragments, 1)
        if f and isinstance(f, dict) and "text" in f and "id" in f and "timestamp" in f
    ]

    if not valid_fragments:
        return []

    # Create tasks for all fragments
    tasks = [
        analyze_fragment(fragment, idx, total) for idx, fragment in valid_fragments
    ]

    # Run all tasks concurrently and collect results
    results = await asyncio.gather(*tasks)

    # Filter out None results
    return [r for r in results if r is not None]


@task(name="analyze_song_vocabulary", retries=3, retry_delay_seconds=2)
async def analyze_song_vocabulary(song_path: str) -> Optional[Dict[str, Any]]:
    """Analyze vocabulary for a song."""
    log = get_run_logger()
    try:
        # Convert string path to Path object for proper path handling
        path = Path(song_path)

        # Read lyrics with annotations
        lyrics_path = path / "lyrics_with_annotations.json"
        if not lyrics_path.exists():
            log.error(f" No lyrics found at {lyrics_path}")
            return None

        with open(lyrics_path, "r") as f:
            lyrics_data = json.load(f)
            log.info("\n Loaded lyrics data:")
            log.info(f"Keys in data: {list(lyrics_data.keys())}")
            log.info(f"Number of lines: {len(lyrics_data['lyrics'])}")
            if lyrics_data["lyrics"]:
                log.info("\n First line sample:")
                log.info(json.dumps(lyrics_data["lyrics"][0], indent=2))

        # Extract lines for analysis
        fragments = [
            {"text": line["text"], "id": line["id"], "timestamp": line["timestamp"]}
            for line in lyrics_data["lyrics"]
        ]
        log.info(f"\n Extracted {len(fragments)} fragments for analysis")
        log.info(f"First fragment: {json.dumps(fragments[0], indent=2)}")

        # Process fragments in batches
        batch_size = 5
        all_results = []

        # Process batches sequentially but fragments within batch concurrently
        for i in range(0, len(fragments), batch_size):
            batch = fragments[i : i + batch_size]
            try:
                log.info(
                    f"\n Processing batch {i//batch_size + 1}/{(len(fragments) + batch_size - 1)//batch_size}"
                )
                batch_results = await process_batch(batch, i, len(fragments))
                if batch_results:
                    log.info(f" Batch returned {len(batch_results)} results")
                    all_results.extend(batch_results)
                else:
                    log.warning(" Batch returned no results")
            except Exception as e:
                log.error(f" Batch processing failed at index {i}: {str(e)}")
                log.exception("Full traceback:")
                continue  # Skip failed batch but continue with others

        # Combine results
        all_vocabulary = []
        total_terms = 0
        seen_terms = set()  # Track unique terms to avoid duplicates

        try:
            # Process each batch result
            for batch_result in all_results:
                for entry in batch_result["vocabulary"]:
                    line_entry = {
                        "original": entry["original"],
                        "id": entry["id"],
                        "timestamp": entry["timestamp"],
                        "vocabulary": [],
                    }

                    # Add unique vocabulary terms
                    for term in entry["vocabulary"]:
                        term_key = f"{term['term']}:{term['vocabulary_type']}"
                        if term_key not in seen_terms:
                            seen_terms.add(term_key)
                            total_terms += 1
                            line_entry["vocabulary"].append(term)
                            log.info(
                                f"Found unique term: {term['term']} ({term['vocabulary_type']})"
                            )

                    if line_entry["vocabulary"]:
                        all_vocabulary.append(line_entry)

            # Save results
            output_file = path / "vocabulary_analysis.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"vocabulary": all_vocabulary}, f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            log.error(f" Failed to save results: {str(e)}")
            log.exception("Full traceback:")
            return None

        log.info(f"\n Analysis complete - found {total_terms} unique vocabulary terms")
        log.info(f"Results saved to {output_file}")
        return {"vocabulary": all_vocabulary}

    except Exception as e:
        log.error(f" Error analyzing vocabulary for {song_path}: {str(e)}")
        log.exception("Full traceback:")
        raise  # Let Prefect handle the retry
