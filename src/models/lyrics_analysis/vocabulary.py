"""Models for vocabulary analysis in lyrics."""
from typing import List, Dict, Any

from src.constants.lyrics_analysis.vocabulary import VocabularyEntry
from src.tasks.lyrics_analysis.vocabulary import analyze_vocabulary

class VocabularyAnalysis:
    """Analyzes vocabulary in lyrics, identifying special terms and their meanings."""
    
    async def analyze_line(self, line: str) -> List[VocabularyEntry]:
        """Analyze vocabulary in a single line of lyrics."""
        # Format the line string into the expected dictionary format
        line_dict: Dict[str, Any] = {
            'text': line,
            'annotations': []  # Empty annotations for raw text input
        }
        return await analyze_vocabulary(line_dict)