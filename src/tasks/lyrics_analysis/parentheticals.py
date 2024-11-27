"""Task for analyzing parenthetical content in lyrics."""
import logging
from typing import Dict, Any, List

from src.utils.cleaning.text import extract_parentheticals

logger = logging.getLogger(__name__)

def analyze_parentheticals(lyrics: str) -> Dict[str, Any]:
    """Extract parenthetical content from lyrics.
    
    Args:
        lyrics: The lyrics line to analyze
        
    Returns:
        Dictionary containing:
        {
            "line_without_parentheses": str,  # Original line with parenthetical content removed
            "parentheticals": List[str]  # List of extracted parenthetical content
        }
    """
    try:
        # Extract parentheticals
        line_without_parens, parens = extract_parentheticals(lyrics)
        
        return {
            "line_without_parentheses": line_without_parens,
            "parentheticals": [p["content"] for p in parens]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to extract parentheticals: {str(e)}")
        return {
            "line_without_parentheses": lyrics,
            "parentheticals": []
        }
