from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class ErrorType(Enum):
    CORRECT = "correct"
    SEMANTIC = "SEMANTIC"
    REGISTER = "REGISTER"
    GRAMMAR = "GRAMMAR"

@dataclass
class Option:
    """A single option for a fill-in-blank exercise"""
    word: str
    explanation: str
    error_type: ErrorType
    is_correct: bool

@dataclass
class SemanticUnit:
    """Represents semantic analysis of a phrase"""
    text: str
    type: str
    meaning: str
    normalized_forms: List[str]
    layers: List[str]  # Could be expanded to a more specific type if needed

@dataclass
class Annotation:
    """Genius annotation data"""
    id: int
    fragment: str
    annotation_text: str

@dataclass
class SemanticContext:
    """Combined semantic analysis and annotation"""
    semantic_unit: SemanticUnit
    annotation: Annotation

@dataclass
class ExerciseMetadata:
    """Metadata for a fill-in-blank exercise"""
    timestamp: datetime
    contains_explicit: bool
    semantic_context: SemanticContext

@dataclass
class FillBlankExercise:
    """A complete fill-in-blank exercise"""
    text: str
    target_word: str
    options: List[Option]
    metadata: ExerciseMetadata

    @property
    def correct_answer(self) -> Option:
        """Get the correct option"""
        return next(opt for opt in self.options if opt.is_correct)

    @property
    def distractors(self) -> List[Option]:
        """Get the incorrect options"""
        return [opt for opt in self.options if not opt.is_correct]
