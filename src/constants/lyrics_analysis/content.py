"""Content analysis and classification constants."""
from typing import List
from enum import Enum
from pydantic import BaseModel

class ContentRating(str, Enum):
    G = "G"           # General Audience
    PG = "PG"         # Parental Guidance
    PG13 = "PG-13"    # Parental Guidance 13+
    R = "R"           # Restricted

class ContentWarning(str, Enum):
    VIOLENCE = "violence"
    PROFANITY = "profanity"
    SEXUAL_CONTENT = "sexual content"
    DRUG_REFERENCES = "drug references"
    GANG_REFERENCES = "gang references"
    IMPLICIT_VIOLENCE = "implicit violence"

class ProfanityType(str, Enum):
    MILD = "mild"        # damn, hell, etc.
    MODERATE = "moderate"  # shit, ass, etc.
    STRONG = "strong"    # f-word and stronger
    SLUR = "slur"       # discriminatory terms

class ProfanityReplacement(BaseModel):
    original: str
    clean_version: str
    profanity_type: ProfanityType
    semantic_role: str  # e.g., "intensifier", "noun", "expletive"

# Theme Categories
THEME_CATEGORIES: List[str] = [
    "IDENTITY",
    "RELATIONSHIPS",
    "SOCIAL_COMMENTARY",
    "SUCCESS",
    "STRUGGLE",
    "WEALTH",
    "POWER",
    "CULTURE",
    "POLITICS",
    "EMOTION",
    "MUSIC",
    "TECHNOLOGY",
    "PERSONAL_EXPERIENCE",
    "FAMILY",
    "LUXURY",
    "STATUS",
    "LOCATION",
    "CONFLICT",
    "RELIGION",
    "LOYALTY",
    "MATERIALISM",
    "AUTHENTICITY",
    "REPUTATION",
    "ENTERTAINMENT"
]
