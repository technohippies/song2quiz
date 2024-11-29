"""Models for vocabulary analysis."""

from typing import List, Optional

from pydantic import BaseModel

from src.constants.lyrics_analysis.vocabulary import VocabularyType


class VocabularyEntry(BaseModel):
    """A vocabulary term with its analysis."""

    term: str
    vocabulary_type: VocabularyType
    definition: str
    usage_notes: Optional[str] = None
    variants: List[str] = []
    domain: str = "general"
