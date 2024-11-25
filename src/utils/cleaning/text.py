"""Core text cleaning utilities."""
import re
from typing import Tuple, List, Dict, Any

def extract_parentheticals(text: str) -> Tuple[str, List[str]]:
    """Extract content in parentheses from text."""
    parentheticals = re.findall(r'\((.*?)\)', text)
    clean_text = re.sub(r'\s*\([^)]*\)', '', text).strip()
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text, parentheticals

def clean_text(text: str) -> str:
    """Clean text by removing punctuation and normalizing whitespace."""
    text = re.sub(r'[^\w\s\'-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def extract_text_from_dom(dom: Dict[str, Any]) -> str:
    """Extract plain text from Genius DOM structure, preserving newlines."""
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