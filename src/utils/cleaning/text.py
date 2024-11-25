"""Core text cleaning utilities."""
import re
from typing import Tuple, List, Dict, Any
from ftfy import fix_text
from ftfy.fixes import uncurl_quotes

class TextCleaningError(Exception):
    """Custom exception for text cleaning errors."""
    pass

def extract_parentheticals(text: str) -> Tuple[str, List[str]]:
    """Extract content in parentheses from text."""
    try:
        parentheticals = re.findall(r'\((.*?)\)', text)
        clean_text = re.sub(r'\s*\([^)]*\)', '', text).strip()
        clean_text = re.sub(r'\s+', ' ', clean_text)
        return clean_text, parentheticals
    except Exception as e:
        raise TextCleaningError(f"Failed to extract parentheticals: {str(e)}") from e

def clean_text(text: str) -> str:
    """Clean text using ftfy and other cleaning methods."""
    try:
        text = fix_text(text)
        text = uncurl_quotes(text)
        return text
    except Exception as e:
        raise TextCleaningError(f"Failed to clean text: {str(e)}") from e

def clean_annotation_text(text: str) -> str:
    """Clean annotation text more thoroughly while preserving newlines."""
    try:
        # First handle any HTML line breaks by converting to newlines
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Initial quote uncurling
        text = uncurl_quotes(text)
        
        # Split on all possible newline variants
        lines = re.split(r'[\n\r\u2028\u2029]+', text)
        cleaned_lines = []
        
        for line in lines:
            # Additional text fixes
            line = fix_text(line)
            
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
        raise TextCleaningError(f"Failed to clean annotation text: {str(e)}") from e

def clean_fragment(fragment: str) -> str:
    """Clean annotation fragment while preserving newlines."""
    try:
        fragment = uncurl_quotes(fragment)
        fragment = fix_text(fragment)
        fragment = re.sub(r'\[.*?\]', '', fragment)
        
        lines = re.split(r'[\n\r\u2028\u2029]+', fragment)
        cleaned_lines = []
        for line in lines:
            line = ' '.join(line.split())
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    except Exception as e:
        raise TextCleaningError(f"Failed to clean fragment: {str(e)}") from e

def extract_text_from_dom(dom: Dict[str, Any]) -> str:
    """Extract plain text from Genius DOM structure, preserving newlines."""
    try:
        text = []
        
        def process_node(node: Dict[str, Any]) -> None:
            if isinstance(node, str):
                text.append(node)
            elif isinstance(node, dict):
                # Add newline for block elements
                if node.get("tag") in {"p", "div", "br"}:
                    if text and not text[-1].endswith('\n'):
                        text.append('\n')
                
                # Process children
                if "children" in node:
                    for child in node["children"]:
                        process_node(child)
                        
                # Add newline after block elements
                if node.get("tag") in {"p", "div"}:
                    if text and not text[-1].endswith('\n'):
                        text.append('\n')
        
        process_node(dom)
        return ''.join(text).strip()
    except Exception as e:
        raise TextCleaningError(f"Failed to extract text from DOM: {str(e)}") from e