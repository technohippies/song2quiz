"""Linguistic-related constants and enums."""
from typing import List
from enum import Enum

class CEFRLevel(str, Enum):
    A1 = "A1"  # Beginner
    A2 = "A2"  # Elementary
    B1 = "B1"  # Intermediate
    B2 = "B2"  # Upper Intermediate
    C1 = "C1"  # Advanced
    C2 = "C2"  # Mastery

class ParentheticalType(str, Enum):
    """Types of parenthetical content in lyrics."""
    ADLIB = "ADLIB"               # Ad-libs like "(yeah)", "(uh)"
    BACKGROUND = "BACKGROUND"      # Background vocals
    ALTERNATE = "ALTERNATE"        # Alternative lyrics
    CLARIFICATION = "CLARIFICATION"  # Explanatory text
    SOUND_EFFECT = "SOUND_EFFECT"  # Sound descriptions
    REPETITION = "REPETITION"      # Repeated phrases
    TRANSLATION = "TRANSLATION"    # Translations of foreign words
    OTHER = "OTHER"                # Other parenthetical content

class GrammaticalTense(str, Enum):
    PRESENT_SIMPLE = "PRESENT_SIMPLE"
    PRESENT_CONTINUOUS = "PRESENT_CONTINUOUS"
    PRESENT_PERFECT = "PRESENT_PERFECT"
    PAST_SIMPLE = "PAST_SIMPLE"
    PAST_CONTINUOUS = "PAST_CONTINUOUS"
    PAST_PERFECT = "PAST_PERFECT"
    FUTURE_SIMPLE = "FUTURE_SIMPLE"
    FUTURE_CONTINUOUS = "FUTURE_CONTINUOUS"
    FUTURE_PERFECT = "FUTURE_PERFECT"

class SentenceType(str, Enum):
    STATEMENT = "STATEMENT"
    QUESTION = "QUESTION"
    COMMAND = "COMMAND"
    EXCLAMATION = "EXCLAMATION"

class GrammaticalAspect(str, Enum):
    SIMPLE = "SIMPLE"
    CONTINUOUS = "CONTINUOUS"
    PERFECT = "PERFECT"
    PERFECT_CONTINUOUS = "PERFECT_CONTINUOUS"

# AAVE Features
AAVE_FEATURES: List[str] = [
    "copula_deletion",          # Absence of 'be' verb
    "habitual_be",             # Use of 'be' to indicate habitual action
    "completive_done",         # Use of 'done' to mark completed action
    "negative_concord",        # Multiple negation
    "zero_copula",            # Omission of linking verbs
    "verbal_marker_been",      # Remote past tense marker
    "possessive_they",        # Alternative possessive forms
    "existential_it",         # Alternative existential forms
    "auxiliary_deletion",     # Deletion of auxiliary verbs
    "consonant_cluster_reduction"  # Simplified consonant clusters
]

# Grammatical Structures
GRAMMATICAL_STRUCTURES: List[str] = [
    "subject_verb_object",
    "subject_verb_complement",
    "there_be",
    "cleft_sentence",
    "passive_voice",
    "reported_speech",
    "conditional",
    "relative_clause",
    "participle_clause",
    "infinitive_clause"
]
