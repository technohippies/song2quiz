"""Task for analyzing vocabulary in lyrics."""
from typing import Dict, List
from functools import lru_cache

from src.constants.lyrics_analysis.vocabulary import VocabularyType, VocabularyEntry
from src.services.openrouter import OpenRouterClient

@lru_cache()
def get_vocabulary_prompt() -> str:
    """Get the system prompt for vocabulary analysis."""
    return '''You are an expert linguist specializing in vocabulary analysis, particularly in music lyrics and vernacular language.

Your task is to analyze terms and phrases, identifying:
1. Their vocabulary type (VERNACULAR, STANDARD, SLANG, etc.)
2. Precise definitions
3. Usage context and notes
4. Register (formal/informal)
5. Domain (e.g., music, general speech)
6. Any relevant variants

Focus on:
- Musical and cultural context
- Accurate representation of AAVE and other dialects
- Maintaining original meaning and cultural significance'''

def parse_vocabulary_response(response: Dict) -> List[VocabularyEntry]:
    """Parse the LLM response into VocabularyEntry objects."""
    entries = []
    for item in response.get("vocabulary", []):
        entry = VocabularyEntry(
            term=item["term"],
            vocabulary_type=VocabularyType(item["vocabulary_type"]),
            definition=item["definition"],
            usage_notes=item.get("usage_notes", ""),
            domain=item.get("domain", "general"),
            register=item.get("register", "informal")
        )
        entries.append(entry)
    return entries

async def analyze_vocabulary(line: str) -> List[VocabularyEntry]:
    """Analyze vocabulary terms in the line."""
    llm = OpenRouterClient()
    system_prompt = get_vocabulary_prompt()
    
    result = await llm.analyze(
        system_prompt=system_prompt,
        user_prompt=f"Analyze the vocabulary in this line: {line}"
    )
    
    return parse_vocabulary_response(result)