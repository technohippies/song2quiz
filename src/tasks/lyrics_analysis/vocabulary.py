"""Prefect tasks for vocabulary analysis."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from prefect import task, get_run_logger
import asyncio

from src.tasks.api.openrouter_tasks import complete_openrouter_prompt
from src.prompts.lyrics_analysis.vocabulary.system import SYSTEM_PROMPT
from src.prompts.lyrics_analysis.vocabulary.examples import EXAMPLES

logger = logging.getLogger(__name__)

@task(name="analyze_fragment", 
      retries=3,
      retry_delay_seconds=2,
      tags=["api"])
async def analyze_fragment(fragment: Dict[str, str], index: int, total: int) -> Optional[Dict[str, Any]]:
    """Analyze a single fragment."""
    log = get_run_logger()
    try:
        # Build prompt with examples for few-shot learning
        examples_text = "\n\n".join([
            f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'], indent=2)}"
            for ex in EXAMPLES[:2]
        ])
        
        annotation_text = ""
        if fragment.get("annotation"):
            annotation_text = f"\n\nHere's annotations from Genius.com about this line of lyrics: {fragment['annotation']}"
        
        prompt = f"""Here are some examples:

{examples_text}

IMPORTANT: Analyze ALL non-standard vocabulary terms in the line, including slang terms like 'whip', 'cap', and 'fire'.
Now analyze this lyric: {fragment['text']}{annotation_text}"""
        
        log.info(f"Processing fragment {index}/{total}")
        
        # Get vocabulary analysis from API
        api_result = await complete_openrouter_prompt(
            formatted_prompt=prompt,
            task_type="vocabulary",
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512
        )
        
        # Create response with the vocabulary terms
        if isinstance(api_result, dict) and "vocabulary" in api_result:
            # Only create response if we have terms
            if api_result["vocabulary"]:  # Check if vocabulary list is not empty
                response = {
                    "vocabulary": [
                        {
                            "original": fragment["text"],
                            "id": fragment["id"],
                            "timestamp": fragment["timestamp"],
                            "vocabulary": api_result["vocabulary"]
                        }
                    ]
                }
                return response
            
        return None
        
    except Exception as e:
        log.error(f"Failed to analyze fragment {index}: {str(e)}")
        log.exception("Full traceback:")
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
      retries=2,
      retry_delay_seconds=10,
      tags=["song"])
async def analyze_song_vocabulary(song_path: str) -> bool:
    """Analyze vocabulary for a song."""
    log = get_run_logger()
    try:
        # Load lyrics
        lyrics_file = Path(song_path) / "lyrics_with_annotations.json"
        if not lyrics_file.exists():
            log.error(f"❌ No lyrics found at {lyrics_file}")
            return False
            
        try:
            with open(lyrics_file) as f:
                lyrics_data = json.load(f)
        except json.JSONDecodeError as e:
            log.error(f"❌ Failed to parse lyrics file: {str(e)}")
            return False
            
        log.info(f"Loaded lyrics data from {lyrics_file}")
            
        # Extract fragments from lyrics_with_annotations.json format
        fragments: List[Dict[str, str]] = []
        if isinstance(lyrics_data, dict) and "lyrics" in lyrics_data:
            for line in lyrics_data["lyrics"]:
                if isinstance(line, dict) and "text" in line and "id" in line and "timestamp" in line:
                    fragment = {
                        "text": line["text"],
                        "id": line["id"],
                        "timestamp": line["timestamp"],
                        "annotation": line.get("annotation", "")  # Get annotation if it exists
                    }
                    fragments.append(fragment)
                    log.debug(f"Added fragment: {fragment['text']}")
        else:
            log.error(f"❌ Invalid lyrics data format: {type(lyrics_data)}")
            return False
            
        if not fragments:
            log.error("❌ No lyrics fragments found to analyze")
            return False
            
        total_fragments = len(fragments)
        log.info(f"Starting analysis of {total_fragments} fragments")
        
        # Process fragments in batches
        batch_size = 5
        all_results = []
        
        # Process batches sequentially but fragments within batch concurrently
        for i in range(0, total_fragments, batch_size):
            batch = fragments[i:i + batch_size]
            try:
                batch_results = await process_batch(batch, i, total_fragments)
                all_results.extend(batch_results)
                log.info(f"Completed batch {i//batch_size + 1}/{(total_fragments + batch_size - 1)//batch_size}")
            except Exception as e:
                log.error(f"❌ Batch processing failed at index {i}: {str(e)}")
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
        output_file = Path(song_path) / "vocabulary_analysis.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"vocabulary": all_vocabulary}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"❌ Failed to save results: {str(e)}")
            log.exception("Full traceback:")
            return False
            
        log.info(f"✓ Analysis complete - found {total_terms} unique vocabulary terms")
        log.info(f"Results saved to {output_file}")
        return True
        
    except Exception as e:
        log.error(f"❌ Error analyzing vocabulary for {song_path}: {str(e)}")
        log.exception("Full traceback:")
        raise  # Let Prefect handle the retry