"""Models for semantic unit analysis."""

from typing import List, Optional

from pydantic import BaseModel

from src.constants.lyrics_analysis.rhetorical import SemanticLayer, SemanticUnitType


class SemanticUnit(BaseModel):
    """A semantic unit with its analysis."""

    id: str
    text: str
    type: SemanticUnitType
    meaning: str
    layers: List[SemanticLayer]
    annotation: Optional[str] = (
        None  # Optional since we'll add annotations manually later
    )


class SemanticUnitsAnalysis(BaseModel):
    """Container for semantic units analysis of a line."""

    semantic_units: List[SemanticUnit]
