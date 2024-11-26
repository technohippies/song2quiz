"""Prefect tasks for vocabulary analysis."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from prefect import task, get_run_logger

from src.tasks.api.openrouter_tasks import complete_openrouter_prompt
from src.prompts.lyrics_analysis.vocabulary.system import SYSTEM_PROMPT
from src.prompts.lyrics_analysis.vocabulary.examples import EXAMPLES

logger = logging.getLogger(__name__)

@task(name="analyze_fragment", 
      retries=3,
      retry_delay_seconds=2,
      tags=["api"])
async def analyze_fragment(fragment: str, index: int, total: int) -> Dict[str, Any]:
    """Analyze a single fragment."""
    log = get_run_logger()
    try:
        # Build prompt with examples for few-shot learning
        examples_text = "\n\n".join([
            f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'], indent=2)}"
            for ex in EXAMPLES[:2]  # Use first 2 examples
        ])
        
        prompt = f"""Here are some examples:

{examples_text}

Now analyze this lyric: {fragment}"""
        
        log.info(f"Processing fragment {index}/{total}")
        
        result = await complete_openrouter_prompt(
            formatted_prompt=prompt,
            task_type="vocabulary",
            system_prompt=SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=256
        )
        
        # Validate and clean the result
        if isinstance(result, str):
            try:
                result = result.strip('`').strip()
                if result.startswith('```json'):
                    result = result[7:]
                if result.endswith('```'):
                    result = result[:-3]
                log.debug(f"Attempting to parse JSON for fragment {index}: {result}")
                result = json.loads(result)
            except json.JSONDecodeError as e:
                log.error(f"❌ Fragment {index}/{total} JSON parsing error: {str(e)}")
                log.error(f"Raw result that failed parsing: {result}")
                return {"vocabulary": []}
                
        if not isinstance(result, dict):
            log.error(f"❌ Fragment {index}/{total} returned non-dict result: {type(result)}")
            return {"vocabulary": []}
            
        if "vocabulary" not in result:
            log.error(f"❌ Fragment {index}/{total} missing 'vocabulary' key in result: {result}")
            return {"vocabulary": []}
            
        # Validate each vocabulary term
        valid_terms = []
        for term_idx, term in enumerate(result.get("vocabulary", []), 1):
            if not isinstance(term, dict):
                log.warning(f"Term {term_idx} in fragment {index} is not a dict: {type(term)}")
                continue
                
            # Check required fields
            required_fields = ["term", "vocabulary_type", "definition", "usage_notes", "variants"]
            missing_fields = [field for field in required_fields if field not in term]
            if missing_fields:
                log.warning(f"Term {term_idx} in fragment {index} missing required fields: {missing_fields}")
                continue
                
            # Validate field types
            invalid_fields = []
            for field in ["term", "vocabulary_type", "definition", "usage_notes"]:
                if not isinstance(term[field], str):
                    invalid_fields.append(f"{field} (expected str, got {type(term[field])})")
            
            if not isinstance(term["variants"], list):
                invalid_fields.append(f"variants (expected list, got {type(term['variants'])})")
                
            if invalid_fields:
                log.warning(f"Term {term_idx} in fragment {index} has invalid field types: {invalid_fields}")
                continue
                
            # Clean up variants list
            term["variants"] = [v for v in term["variants"] if isinstance(v, str) and v]
            
            valid_terms.append(term)
            log.debug(f"Added valid term from fragment {index}: {term['term']}")
            
        terms = len(valid_terms)
        log.info(f"✓ Fragment {index}/{total} - found {terms} valid terms")
        return {"vocabulary": valid_terms}
            
    except Exception as e:
        log.error(f"❌ Error in fragment {index}/{total}: {str(e)}")
        log.exception("Full traceback:")
        raise  # Let Prefect handle the retry

@task(name="process_batch",
      retries=2,
      retry_delay_seconds=5,
      tags=["batch"])
async def process_batch(fragments: List[str], start_index: int, total: int) -> List[Dict[str, Any]]:
    """Process a batch of fragments concurrently."""
    log = get_run_logger()
    
    # Filter out invalid fragments
    valid_fragments = [(i+start_index, f) for i, f in enumerate(fragments, 1) 
                      if f and isinstance(f, str)]
    
    if not valid_fragments:
        return []
    
    # Create tasks for all fragments
    tasks = []
    for index, fragment in valid_fragments:
        future = analyze_fragment.submit(fragment, index, total)
        tasks.append(future)
    
    try:
        # Wait for all tasks to complete
        results = []
        for future in tasks:
            try:
                result = future.result()  # No await needed here
                if result is not None:
                    results.append(result)
            except Exception as e:
                log.error(f"❌ Task failed: {str(e)}")
                log.exception("Full traceback:")
                
        return results
    except Exception as e:
        log.error(f"❌ Batch processing failed: {str(e)}")
        log.exception("Full traceback:")
        return []

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
        fragments: List[str] = []
        if isinstance(lyrics_data, dict) and "lyrics" in lyrics_data:
            for line in lyrics_data["lyrics"]:
                if isinstance(line, dict) and "text" in line:
                    fragments.append(line["text"])
                    log.debug(f"Added fragment: {line['text']}")
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
                terms = result["vocabulary"]
                for term in terms:
                    # Only add unique terms
                    term_key = (term["term"].lower(), term["vocabulary_type"])
                    if term_key not in seen_terms:
                        seen_terms.add(term_key)
                        total_terms += 1
                        all_vocabulary.append(term)
                        log.info(f"Found unique term: {term['term']} ({term['vocabulary_type']})")
        
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