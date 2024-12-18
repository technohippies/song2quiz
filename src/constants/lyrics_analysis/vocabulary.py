"""Vocabulary-related constants and types."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class VocabularyType(str, Enum):
    """Types of vocabulary terms that need special tracking and explanation"""

    # Named Entities
    PROPER_NOUN = "proper_noun"  # Specific names of people, places, organizations
    BRAND = "brand"  # Commercial products, companies, services

    # Informal Language
    SLANG = "slang"  # Informal terms not in standard dictionaries
    AAVE = "aave"  # Terms specific to African American Vernacular English
    VERNACULAR = (
        "vernacular"  # Terms specific to a regional dialect or speech community
    )

    # Common Informal Usage
    COLLOQUIALISM = (
        "colloquialism"  # Informal words/phrases used broadly in everyday speech
    )

    # Abbreviations & Compounds
    ACRONYM = "acronym"  # Abbreviated terms (GDs, POTUS)
    COMPOUND = "compound"  # New combinations of words
    PORTMANTEAU = "portmanteau"  # Blended words

    # Phrases & Expressions
    IDIOM = "idiom"  # Established phrases with non-literal meaning
    PHRASAL_VERB = "phrasal_verb"  # Verb + preposition with specific meaning

    # Creative Language
    NEOLOGISM = "neologism"  # Newly created terms
    WORDPLAY = "wordplay"  # Creative use of language


class VocabularyEntry(BaseModel):
    """A vocabulary term that needs special tracking or explanation"""

    term: str
    vocabulary_type: VocabularyType
    definition: str
    usage_notes: Optional[str] = None  # Additional context and usage examples
    variants: Optional[List[str]] = (
        None  # Alternative forms, spellings, or closely related terms
    )
    domain: Optional[str] = None  # Field or area of use (music, street, etc.)
