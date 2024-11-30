"""Task for analyzing semantic units in lyrics."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar, cast

from prefect import get_run_logger, task

from src.prompts.lyrics_analysis.semantic_units.examples import EXAMPLES
from src.prompts.lyrics_analysis.semantic_units.system import SYSTEM_PROMPT
from src.services.akash import complete_akash_prompt
from src.tasks.api.openrouter_tasks import complete_openrouter_prompt

BATCH_SIZE = 5
T = TypeVar("T")


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

        async def _try_analyze() -> (
            Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]
        ):
            """Returns a tuple of (full_response, semantic_units)"""
            openrouter_fn = cast(
                Callable[..., Awaitable[Optional[Dict[str, Any]]]],
                complete_openrouter_prompt,
            )
            try:
                response = await openrouter_fn(
                    formatted_prompt=prompt,
                    system_prompt="",
                    task_type="analysis",
                    temperature=0.1,
                )
                if not response or "choices" not in response:
                    log.error(f"[{index}/{total}] Invalid API response: {response}")
                    return None, None

                # Extract just the semantic units content from the response
                try:
                    content = response["choices"][0]["message"]["content"]
                    content_preview = content[:200]
                    if len(content_preview) < len(content):
                        content_preview += "..."
                    log.info(
                        f"[{index}/{total}] Raw content ({len(content)} chars): {content_preview}"
                    )

                    # Check for API truncation
                    is_truncated = False
                    try:
                        # Try to parse as JSON first
                        test_parse = json.loads(content)
                        if (
                            not isinstance(test_parse, dict)
                            or "semantic_units" not in test_parse
                        ):
                            is_truncated = True
                        else:
                            # If we can parse it and it has semantic units, use it directly
                            semantic_units = test_parse
                            return response, semantic_units
                    except json.JSONDecodeError:
                        is_truncated = True

                    if is_truncated or len(content) < 100 or not content.endswith("}"):
                        # Try to parse the original content first
                        original_units = None
                        try:
                            original = json.loads(content)
                            if (
                                "semantic_units" in original
                                and isinstance(original["semantic_units"], list)
                                and len(original["semantic_units"]) > 0
                            ):
                                original_units = original["semantic_units"]
                        except (json.JSONDecodeError, KeyError):
                            pass

                        log.warning(
                            f"[{index}/{total}] OpenRouter truncation detected:\n"
                            f"  - Length: {len(content)} chars\n"
                            f"  - Original text: {fragment['text']}\n"
                            f"Falling back to Akash API..."
                        )

                        # Try Akash API instead
                        akash_response = await complete_akash_prompt(
                            formatted_prompt=prompt,
                            system_prompt="",
                            temperature=0.1,
                        )
                        if not akash_response or "choices" not in akash_response:
                            log.error(
                                f"[{index}/{total}] Akash API failed: {akash_response}"
                            )
                            return None, None

                        content = akash_response["choices"][0]["message"]["content"]
                        response = akash_response  # Use Akash response for tracking
                        log.info(
                            f"[{index}/{total}] Akash API response: {content[:200]}..."
                        )

                        # Try to parse the Akash response
                        try:
                            semantic_units = json.loads(content)
                            if original_units:
                                # Preserve IDs from original response
                                for i, unit in enumerate(
                                    semantic_units["semantic_units"]
                                ):
                                    if i < len(original_units):
                                        if "id" in original_units[i]:
                                            unit["id"] = original_units[i]["id"]
                            return response, semantic_units
                        except (json.JSONDecodeError, KeyError) as e:
                            log.error(
                                f"[{index}/{total}] Failed to parse Akash response: {e}"
                            )
                            return None, None

                    # Clean any potential markdown or formatting
                    content = content.strip()
                    if content.startswith("```"):
                        log.info(f"[{index}/{total}] Found markdown code block")
                        content = "\n".join(content.split("\n")[1:-1])
                    content = content.strip()

                    # Check if we have valid JSON structure
                    if not content.startswith("{") or not content.endswith("}"):
                        log.error(
                            f"[{index}/{total}] Content boundaries: starts with '{content[:1]}', ends with '{content[-1:]}'"
                        )
                        log.error(
                            f"[{index}/{total}] Content is not a JSON object: {content}"
                        )
                        return response, None

                    # Try to parse the JSON
                    semantic_units = json.loads(content)

                    # Validate the expected structure
                    if (
                        not isinstance(semantic_units, dict)
                        or "semantic_units" not in semantic_units
                        or not isinstance(semantic_units["semantic_units"], list)
                    ):
                        log.error(
                            f"[{index}/{total}] Invalid semantic units structure: {semantic_units}"
                        )
                        return response, None

                    # Add missing fields with defaults if needed
                    for unit in semantic_units["semantic_units"]:
                        # Only generate ID if not present in original unit
                        if "id" not in unit:
                            # Try to preserve original ID from input if available
                            if isinstance(content, str) and '"id":' in content:
                                try:
                                    original = json.loads(content)
                                    if (
                                        "semantic_units" in original
                                        and len(original["semantic_units"]) > 0
                                        and "id" in original["semantic_units"][0]
                                    ):
                                        unit["id"] = original["semantic_units"][0]["id"]
                                        continue
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    pass
                            unit["id"] = str(uuid.uuid4())

                        if "type" not in unit:
                            unit["type"] = "PHRASE"
                        if "layers" not in unit:
                            unit["layers"] = ["LITERAL"]
                        if "meaning" not in unit:
                            unit["meaning"] = "Basic phrase or statement"
                        if "annotation" not in unit:
                            unit["annotation"] = "No additional context"

                    # Add the line ID from the original lyrics if present
                    if "id" in fragment:
                        semantic_units["id"] = fragment["id"]

                    # Return in the format tests expect
                    return {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(semantic_units),
                                    "role": "assistant",
                                }
                            }
                        ]
                    }, semantic_units

                except (KeyError, json.JSONDecodeError) as e:
                    log.error(
                        f"[{index}/{total}] Error parsing response content: {str(e)}"
                    )
                    log.error(f"[{index}/{total}] Problematic content: {content}")
                    return response, None

            except Exception as e:
                log.error(f"[{index}/{total}] Error in _try_analyze: {str(e)}")
                raise  # Re-raise for retry logic in outer try block

        # Main function logic
        for attempt in range(3):
            try:
                if not fragment["text"].strip() or fragment["text"].strip() == "...":
                    log.info(f"[{index}/{total}] Skipping empty line")
                    return {"semantic_units": []}

                # Format the prompt
                prompt = format_prompt(EXAMPLES, fragment["text"])

                # Try to analyze with retries
                response, semantic_units = await _try_analyze()

                # For Langfuse tracking, track the response
                if response is not None:
                    # TODO: Track with Langfuse here
                    pass

                # Return the response (which now includes semantic_units in the expected format)
                if response is not None:
                    return response

                if attempt < 2:  # Don't sleep on last attempt
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                continue

            except Exception as e:
                error_str = str(e)
                log.error(
                    f"[{index}/{total}] Error in attempt {attempt + 1}: {error_str}"
                )

                # If it's a rate limit error, wait longer
                if "rate limit exceeded" in error_str.lower():
                    if attempt < 2:
                        wait_time = 2 ** (attempt + 2)  # Longer waits for rate limits
                        log.info(
                            f"[{index}/{total}] Rate limit hit, waiting {wait_time}s before retry"
                        )
                        await asyncio.sleep(wait_time)
                elif attempt < 2:  # For other errors, use standard backoff
                    await asyncio.sleep(2**attempt)
                continue

        log.error(f"[{index}/{total}] All attempts failed")
        return None

    except Exception as e:
        log.error(f"[{index}/{total}] Error in analyze_fragment: {str(e)}")
        raise


@task(name="analyze_song_semantic_units")
async def analyze_song_semantic_units(song_path: str) -> Optional[Dict[str, Any]]:
    """Analyze semantic units for a song."""
    log = get_run_logger()
    song_dir = Path(song_path)

    # Load lyrics with annotations
    lyrics_file = song_dir / "lyrics_with_annotations.json"
    if not lyrics_file.exists():
        log.error(f"Lyrics file not found: {lyrics_file}")
        return None

    # Load output file
    output_file = song_dir / "semantic_units_analysis.json"
    if output_file.exists():
        log.info(f"Semantic units analysis already exists: {output_file}")
        with open(output_file) as f:
            return cast(Dict[str, Any], json.load(f))

    try:
        # Load lyrics data
        with open(lyrics_file) as f:
            lyrics_data = cast(Dict[str, Any], json.load(f))

        # Extract lines for analysis, skipping empty lines
        fragments = [
            {"text": line["text"], "id": line["id"]}
            for line in lyrics_data["lyrics"]
            if line["text"].strip() and line["text"].strip() != "..."
        ]

        # Process fragments in batches
        results = []
        for i in range(0, len(fragments), BATCH_SIZE):
            batch = fragments[i : i + BATCH_SIZE]
            batch_results = await asyncio.gather(
                *[
                    analyze_fragment.fn(fragment, idx + i + 1, len(fragments))
                    for idx, fragment in enumerate(batch)
                ]
            )
            results.extend(batch_results)
            log.info(
                f"✓ Processed batch {i // BATCH_SIZE + 1} ({i + 1}-{min(i + BATCH_SIZE, len(fragments))})"
            )

        # Filter out None results and save
        results = [r for r in results if r is not None]
        output_data = {"semantic_units_analysis": results}
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        log.info(f"✓ Saved semantic units analysis to {output_file}")
        return output_data

    except Exception as e:
        log.error(f"Error analyzing semantic units: {str(e)}")
        raise
