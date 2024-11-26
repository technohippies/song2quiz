"""Prefect tasks for vocabulary analysis."""
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from prefect import task

from src.tasks.api.openrouter_tasks import complete_openrouter_prompt
from src.prompts.lyrics_analysis.vocabulary.system import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

@task(name="analyze_fragment", retries=2, retry_delay_seconds=2)
async def analyze_fragment(fragment: str, index: int, total: int) -> Dict[str, Any]:
    """Analyze a single fragment."""
    try:
        # Clean fragment to avoid filters
        clean_fragment = fragment.replace("nigga", "n***a").replace("fuck", "f***")
        
        prompt = """Return ONLY a valid JSON object in this exact format analyzing the lyric:
{
  "vocabulary": [
    {
      "term": "example",
      "vocabulary_type": "slang",
      "definition": "brief meaning",
      "usage_notes": "brief context",
      "variants": []
    }
  ]
}

DO NOT include any explanatory text or markdown formatting.
DO NOT leave any fields incomplete or empty.
ALWAYS complete the entire JSON object.
Analyze this lyric: """ + clean_fragment

        logger.info(f"Processing fragment {index}/{total}")
        
        result = await complete_openrouter_prompt(
            formatted_prompt=prompt,
            task_type="vocabulary",
            system_prompt=SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=512
        )
        
        # Validate and clean the result
        if isinstance(result, str):
            try:
                # Try to parse the string as JSON, strip any markdown
                result = result.strip('`').strip()
                if result.startswith('```json'):
                    result = result[7:]
                if result.endswith('```'):
                    result = result[:-3]
                result = json.loads(result)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Fragment {index}/{total} returned invalid JSON string: {str(e)}")
                return {"vocabulary": []}
                
        if not isinstance(result, dict):
            logger.warning(f"⚠️ Fragment {index}/{total} returned non-dict result: {type(result)}")
            return {"vocabulary": []}
            
        if "vocabulary" not in result:
            logger.warning(f"⚠️ Fragment {index}/{total} missing vocabulary key: {result.keys()}")
            return {"vocabulary": []}
            
        # Validate each vocabulary term
        valid_terms = []
        for term in result.get("vocabulary", []):
            if not isinstance(term, dict):
                continue
                
            # Check required fields
            required_fields = ["term", "vocabulary_type", "definition", "usage_notes", "variants"]
            if not all(field in term for field in required_fields):
                continue
                
            # Validate field types
            if not isinstance(term["term"], str) or not term["term"]:
                continue
            if not isinstance(term["vocabulary_type"], str) or not term["vocabulary_type"]:
                continue
            if not isinstance(term["definition"], str) or not term["definition"]:
                continue
            if not isinstance(term["usage_notes"], str):
                continue
            if not isinstance(term["variants"], list):
                continue
                
            # Clean up variants list
            term["variants"] = [v for v in term["variants"] if isinstance(v, str) and v]
            
            valid_terms.append(term)
            
        terms = len(valid_terms)
        logger.info(f"✓ Fragment {index}/{total} - found {terms} valid terms")
        return {"vocabulary": valid_terms}
            
    except Exception as e:
        logger.error(f"❌ Error in fragment {index}/{total}: {str(e)}")
        return {"vocabulary": []}

@task(name="analyze_song_vocabulary")
async def analyze_song_vocabulary(song_path: str) -> bool:
    """Analyze vocabulary for a song."""
    try:
        # Load lyrics
        lyrics_file = Path(song_path) / "lyrics_with_annotations.json"
        if not lyrics_file.exists():
            logger.warning(f"❌ No lyrics found at {lyrics_file}")
            return False
            
        with open(lyrics_file) as f:
            lyrics_data = json.load(f)
            
        logger.info(f"Loaded lyrics data from {lyrics_file}")
            
        # Extract fragments from lyrics_with_annotations.json format
        fragments: List[str] = []
        if isinstance(lyrics_data, dict) and "lyrics" in lyrics_data:
            for line in lyrics_data["lyrics"]:
                if isinstance(line, dict) and "text" in line:
                    fragments.append(line["text"])
                    logger.debug(f"Added fragment: {line['text']}")
            
        if not fragments:
            logger.warning("❌ No lyrics fragments found to analyze")
            return False
            
        total_fragments = len(fragments)
        logger.info(f"Starting analysis of {total_fragments} fragments")
        
        # Process fragments in smaller batches
        batch_size = 5
        all_results = []
        
        for i in range(0, total_fragments, batch_size):
            batch = fragments[i:i + batch_size]
            batch_results = []
            
            # Process each fragment in the batch
            for j, fragment in enumerate(batch, 1):
                if fragment and isinstance(fragment, str):
                    index = i + j
                    logger.info(f"Processing fragment {index}/{total_fragments}")
                    try:
                        result = await analyze_fragment(fragment, index, total_fragments)
                        if isinstance(result, dict) and "vocabulary" in result:
                            batch_results.append(result)
                            logger.info(f"Completed fragment with {len(result.get('vocabulary', []))} terms")
                    except Exception as e:
                        logger.error(f"Failed to process fragment {index}: {str(e)}")
            
            all_results.extend(batch_results)
            await asyncio.sleep(1)  # Rate limiting
        
        # Combine results
        all_vocabulary = []
        total_terms = 0
        seen_terms = set()  # Track unique terms to avoid duplicates
        
        for result in all_results:
            if result and "vocabulary" in result:
                terms = result["vocabulary"]
                for term in terms:
                    # Only add unique terms
                    term_key = (term["term"].lower(), term["vocabulary_type"])
                    if term_key not in seen_terms:
                        seen_terms.add(term_key)
                        total_terms += 1
                        all_vocabulary.append(term)
                        logger.info(f"Found term: {term['term']} ({term['vocabulary_type']})")
        
        # Save results
        output_file = Path(song_path) / "vocabulary_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"vocabulary": all_vocabulary}, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✓ Analysis complete - found {total_terms} unique vocabulary terms")
        logger.info(f"Results saved to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error analyzing vocabulary for {song_path}: {str(e)}")
        logger.exception("Full error:")
        return False