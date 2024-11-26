"""Task for analyzing vocabulary in lyrics."""
from typing import Dict, List, Union, Any, Tuple
import asyncio
from itertools import islice
import logging
import json

from src.constants.lyrics_analysis.vocabulary import VocabularyType, VocabularyEntry
from src.tasks.api.openrouter_tasks import complete_prompt
from src.prompts.lyrics_analysis.vocabulary.system import SYSTEM_PROMPT
from src.prompts.lyrics_analysis.vocabulary.examples import EXAMPLES
from src.prompts.lyrics_analysis.vocabulary.schemas import SCHEMAS

# Set up logging
logger = logging.getLogger(__name__)

# Format examples into prompt once
EXAMPLES_PROMPT = "\n\nExamples:\n"
for example in EXAMPLES:
    EXAMPLES_PROMPT += f"\nInput: {example['input']}\nOutput: {example['output']}\n"

FULL_PROMPT = SYSTEM_PROMPT + EXAMPLES_PROMPT

def format_line_with_annotations(line: Dict[str, Any]) -> str:
    """Format a line and its annotations into a prompt."""
    text = line.get('text', '')
    annotations = line.get('annotations', [])
    
    prompt = f"Line: {text}\n"
    if annotations:
        prompt += "\nAnnotations/Context:\n"
        for i, annotation in enumerate(annotations, 1):
            fragment = annotation.get('fragment', '')
            explanation = annotation.get('annotation_text', '')
            if fragment and explanation:
                prompt += f"{i}. \"{fragment}\": {explanation}\n"
    
    # Log the complete prompt for verification
    logger.debug("=== FORMATTED PROMPT ===")
    logger.debug(f"Input line: {text}")
    logger.debug(f"Number of annotations: {len(annotations)}")
    logger.debug("Complete prompt:")
    logger.debug(prompt)
    logger.debug("=====================")
    
    return prompt

def is_valid_vocabulary_term(term: str, vocab_type: str) -> bool:
    """Check if a term is valid for vocabulary analysis."""
    # Allow phrasal verbs even if they're multiple words
    if vocab_type.lower() == 'phrasal_verb':
        return True
        
    # For all other types, only allow single words
    words = term.split()
    if len(words) > 1:
        logger.debug(f"Skipping multi-word term '{term}' (type: {vocab_type})")
        return False
    
    return True

async def process_batch_with_retries(batch: List[Dict[str, Any]], max_retries: int = 3) -> Tuple[List[Dict], int]:
    """Process a batch of lines with retries and error tracking."""
    tasks = [
        complete_prompt.fn(
            prompt=format_line_with_annotations(line),
            system_prompt=FULL_PROMPT,
            task_type="lyrics_analysis",
            temperature=0.7
        )
        for line in batch
    ]
    
    results = []
    error_count = 0
    
    for attempt in range(max_retries):
        try:
            # Run batch of API calls concurrently with timeout
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and track errors
            for result in batch_results:
                if isinstance(result, Exception):
                    error_count += 1
                    logger.warning(f"Error in batch processing: {str(result)}")
                    results.append({})  # Add empty result for failed calls
                elif isinstance(result, dict):
                    results.append(result)
                else:
                    results.append({})
            
            # If we got any successful results, return them
            if any(isinstance(r, dict) for r in results):
                return results, error_count
                
        except Exception as e:
            logger.error(f"Batch processing attempt {attempt + 1} failed: {str(e)}")
            error_count += len(batch)
            
        # Wait before retrying with exponential backoff
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)
    
    return results, error_count

async def analyze_vocabulary_batch(
    lines: List[Dict[str, Any]], 
    initial_batch_size: int = 5,
    min_batch_size: int = 2,
    error_threshold: float = 0.3
) -> List[VocabularyEntry]:
    """Analyze vocabulary terms in multiple lines concurrently with dynamic batch sizing."""
    all_entries = []
    seen_terms = set()  # Track terms we've already analyzed in this song
    current_batch_size = initial_batch_size
    total_errors = 0
    total_processed = 0
    
    logger.info(f"Starting vocabulary analysis with batch size {current_batch_size}")
    
    # Process lines in batches
    for i in range(0, len(lines), current_batch_size):
        batch = lines[i:i + current_batch_size]
        logger.info(f"Processing batch {i//current_batch_size + 1}/{(len(lines) + current_batch_size - 1)//current_batch_size}")
        
        # Process batch with retries
        batch_results, batch_errors = await process_batch_with_retries(batch)
        
        # Update error tracking
        total_errors += batch_errors
        total_processed += len(batch)
        error_rate = total_errors / total_processed if total_processed > 0 else 0
        
        # Adjust batch size based on error rate
        if error_rate > error_threshold and current_batch_size > min_batch_size:
            new_batch_size = max(min_batch_size, current_batch_size // 2)
            logger.warning(f"High error rate ({error_rate:.2%}), reducing batch size from {current_batch_size} to {new_batch_size}")
            current_batch_size = new_batch_size
        
        # Process results
        for result, line in zip(batch_results, batch):
            if isinstance(result, dict):
                entries = parse_vocabulary_response(result)
                if entries:
                    # Only add entries we haven't seen before in this song
                    for entry in entries:
                        if entry.term.lower() not in seen_terms:
                            seen_terms.add(entry.term.lower())
                            all_entries.append(entry)
                        else:
                            logger.debug(f"Skipping duplicate term '{entry.term}'")
        
        # Log progress
        logger.info(f"Processed {total_processed}/{len(lines)} lines, error rate: {error_rate:.2%}")
    
    return all_entries

async def analyze_vocabulary(line: Dict[str, Any]) -> List[VocabularyEntry]:
    """Analyze vocabulary terms in a single line."""
    try:
        result = await complete_prompt.fn(
            prompt=format_line_with_annotations(line),
            system_prompt=FULL_PROMPT,
            task_type="lyrics_analysis",
            temperature=0.7
        )
        
        # Handle both string and dictionary responses
        if isinstance(result, str):
            return []  # Return empty list if result is a string
        
        return parse_vocabulary_response(result)
        
    except Exception as e:
        logger.error(f"Error analyzing line: {str(e)}")
        return []

def parse_vocabulary_response(response: Dict[str, Any]) -> List[VocabularyEntry]:
    """Parse the LLM response into VocabularyEntry objects."""
    entries = []
    try:
        # Handle both direct response and nested response structures
        vocabulary_items = []
        if isinstance(response, dict):
            if "vocabulary" in response:
                vocabulary_items = response["vocabulary"]
            elif "choices" in response and response["choices"]:
                # Handle OpenRouter API response structure
                content = response["choices"][0].get("message", {}).get("content", "")
                if isinstance(content, str):
                    try:
                        content_json = json.loads(content)
                        if "vocabulary" in content_json:
                            vocabulary_items = content_json["vocabulary"]
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse content as JSON")
                elif isinstance(content, dict) and "vocabulary" in content:
                    vocabulary_items = content["vocabulary"]

        for item in vocabulary_items:
            try:
                # Skip entries with missing or invalid vocabulary_type
                vocab_type = item.get("vocabulary_type")
                if not vocab_type:
                    logger.warning(f"Skipping entry with missing vocabulary_type: {item}")
                    continue
                
                # Skip invalid terms
                term = item.get("term", "")
                if not is_valid_vocabulary_term(term, vocab_type):
                    continue
                    
                try:
                    vocab_type_enum = VocabularyType(vocab_type.lower())
                except ValueError:
                    logger.warning(f"Invalid vocabulary_type '{vocab_type}', skipping entry: {item}")
                    continue
                
                # Only create entry if we have all required fields
                if all(k in item for k in ["term", "definition"]):
                    entry = VocabularyEntry(
                        term=item["term"],
                        vocabulary_type=vocab_type_enum,
                        definition=item["definition"],
                        usage_notes=item.get("usage_notes", ""),
                        variants=item.get("variants", []),  # Ensure variants is always a list
                        domain=item.get("domain", "general")
                    )
                    entries.append(entry)
                    logger.debug(f"Successfully parsed entry: {entry}")
                else:
                    logger.warning(f"Skipping entry with missing required fields: {item}")
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing vocabulary entry: {str(e)}, item: {item}")
                continue
    except Exception as e:
        logger.error(f"Error parsing vocabulary response: {str(e)}")
        logger.error(f"Response that caused error: {response}")
    
    return entries