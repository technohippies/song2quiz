"""Prefect tasks for text cleaning operations."""
import json
import logging
import re
from pathlib import Path
from prefect import task

from src.utils.cleaning.text import (
    extract_parentheticals,
    clean_text,
    extract_text_from_dom
)

logger = logging.getLogger(__name__)

import ftfy
import unicodedata

# Define patterns to preserve hyphenated terms
PRESERVE_HYPHENS = [
    r'\b\w+-\w+\b',  # General hyphenated terms
    # Add more specific patterns as needed
]

def clean_annotation_text(text: str) -> str:
    """Clean annotation text more thoroughly while preserving newlines."""
    try:
        # First handle any HTML line breaks by converting to newlines
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Initial quote uncurling
        text = ftfy.fixes.uncurl_quotes(text)
        
        # Split on all possible newline variants
        lines = re.split(r'[\n\r\u2028\u2029]+', text)
        cleaned_lines = []
        
        for line in lines:
            # Additional text fixes
            line = ftfy.fix_text(line)
            
            # Handle punctuation spacing
            patterns = [
                # Fix spacing around punctuation
                (r'\s+([.,!?:;])\s*', r'\1 '),
                
                # Make sure contractions are tight
                (r"(\w)\s+'(\w)", r"\1'\2"),  # e.g., "don' t" -> "don't"
                (r"(\w)'\s+(\w)", r"\1'\2"),  # e.g., "don 't" -> "don't"
            ]
            
            for pattern, replacement in patterns:
                line = re.sub(pattern, replacement, line)
            
            # Clean up extra whitespace within the line only
            line = ' '.join(line.split())
            cleaned_lines.append(line)
        
        # Join lines back together with newlines, preserving empty lines
        return '\n'.join(cleaned_lines)
        
    except Exception as e:
        logger.error(f"Error cleaning text: {str(e)}")
        return text  # Return original text if cleaning fails

def clean_fragment(fragment: str) -> str:
    """Clean annotation fragment while preserving newlines."""
    # First uncurl quotes
    fragment = ftfy.fixes.uncurl_quotes(fragment)
    
    # Additional text fixes
    fragment = ftfy.fix_text(fragment)
    
    # Remove bracketed content
    fragment = re.sub(r'\[.*?\]', '', fragment)
    
    # Split on newlines, clean each line, then rejoin
    lines = re.split(r'[\n\r\u2028\u2029]+', fragment)
    cleaned_lines = []
    for line in lines:
        # Clean up extra whitespace within each line
        line = ' '.join(line.split())
        if line:  # Only add non-empty lines
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

@task(name="process_annotations")
def process_annotations(song_path: Path) -> bool:
    """Process and clean annotations for a song."""
    try:
        input_file = song_path / "genius_annotations.json"
        if not input_file.exists():
            logger.warning(f"No annotations found at {input_file}")
            return False
            
        with open(input_file) as f:
            annotations = json.load(f)
            
        cleaned_annotations = []
        for ann in annotations:
            if ann.get('annotations') and len(ann['annotations']) > 0:
                # Extract and clean the annotation text
                raw_text = extract_text_from_dom(ann['annotations'][0]['body']['dom'])
                annotation_text = clean_annotation_text(raw_text)
                
                # Clean the fragment
                fragment = clean_fragment(ann["fragment"])
                
                # Skip empty or very short annotations
                if len(annotation_text) < 5 or len(fragment) < 3:
                    logger.debug(f"Skipping short annotation: {fragment[:20]}...")
                    continue
                
                cleaned_ann = {
                    "id": ann["id"],
                    "fragment": fragment,
                    "annotation_text": annotation_text
                }
                cleaned_annotations.append(cleaned_ann)
            
        output_file = song_path / "annotations_cleaned.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_annotations, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Processed {len(cleaned_annotations)} annotations for {song_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {song_path}: {str(e)}")
        return False
