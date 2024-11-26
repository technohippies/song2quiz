"""Rhetorical and semantic analysis constants."""
from enum import Enum

class RhetoricalDevice(str, Enum):
    DOUBLE_ENTENDRE = "DOUBLE_ENTENDRE"      # Words/phrases with multiple meanings
    ALLITERATION = "ALLITERATION"            # Repeated consonant sounds
    ASSONANCE = "ASSONANCE"                  # Repeated vowel sounds
    CONSONANCE = "CONSONANCE"                # Consonant repetition
    RHYME = "RHYME"                          # End rhymes
    INTERNAL_RHYME = "INTERNAL_RHYME"        # Rhymes within lines
    SLANT_RHYME = "SLANT_RHYME"             # Near/partial rhymes
    WORDPLAY = "WORDPLAY"                    # Clever manipulation of words
    PUN = "PUN"                              # Play on words
    METAPHOR = "METAPHOR"                    # Implicit comparison
    SIMILE = "SIMILE"                        # Explicit comparison
    PERSONIFICATION = "PERSONIFICATION"      # Human attributes to non-human
    HYPERBOLE = "HYPERBOLE"                  # Exaggeration
    METONYMY = "METONYMY"                    # Associated term substitution
    SYNECDOCHE = "SYNECDOCHE"                # Part represents whole

class SemanticLayer(str, Enum):
    LITERAL = "LITERAL"                      # Surface meaning
    FIGURATIVE = "FIGURATIVE"                # Non-literal meaning
    CULTURAL = "CULTURAL"                    # Cultural context meaning
    HISTORICAL = "HISTORICAL"                # Historical reference meaning
    PERSONAL = "PERSONAL"                    # Artist-specific meaning
    INTERTEXTUAL = "INTERTEXTUAL"           # Reference to other texts/songs

class SemanticUnitType(str, Enum):
    AAVE = "AAVE"                     # African American Vernacular English
    SLANG = "SLANG"                   # Informal/colloquial language
    IDIOM = "IDIOM"                   # Fixed expressions
    METAPHOR = "METAPHOR"             # Figurative language
    SIMILE = "SIMILE"                 # Comparative figures of speech
    PHRASE = "PHRASE"                 # Standard phrases
    COLLOCATION = "COLLOCATION"       # Word partnerships
    PROPER_NOUN = "PROPER_NOUN"       # Names, places, brands
    CULTURAL_REFERENCE = "CULTURAL_REFERENCE"  # Cultural allusions
    WORDPLAY = "WORDPLAY"             # Puns, double meanings
    NEOLOGISM = "NEOLOGISM"           # Newly created words
    ONOMATOPOEIA = "ONOMATOPOEIA"     # Sound words
    DOUBLE_MEANING = "DOUBLE_MEANING"        # Words with dual interpretations
    ENTENDRE = "ENTENDRE"                    # Intentional multiple meanings
    REFERENCE = "REFERENCE"                  # External references
    CALLBACK = "CALLBACK"                    # Internal reference to other lyrics
    INTERPOLATION = "INTERPOLATION"          # Borrowed/referenced lyrics
    SAMPLE = "SAMPLE"                        # Referenced musical elements
