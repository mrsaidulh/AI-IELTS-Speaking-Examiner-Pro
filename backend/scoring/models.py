from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


def round_to_ielts_band(score: float) -> float:
    """
    Applies standard IELTS band score rounding rules:
    - Decimal < 0.25 rounds down to the whole band (e.g. 6.1 -> 6.0, 6.2 -> 6.0)
    - 0.25 <= Decimal < 0.75 rounds to the half band (e.g. 6.25 -> 6.5, 6.6 -> 6.5)
    - Decimal >= 0.75 rounds up to the next whole band (e.g. 6.75 -> 7.0, 6.8 -> 7.0)
    """
    if score is None:
        return 6.0

    score = float(score)
    whole = int(score)
    decimal = score - whole

    if decimal < 0.25:
        return float(whole)
    elif decimal < 0.75:
        return float(whole) + 0.5
    else:
        return float(whole + 1)


def calculate_overall(fluency: float, lexical: float, grammar: float, pronunciation: float) -> float:
    """Calculates overall IELTS band from 4 criterion scores using IELTS rounding."""
    scores = [s for s in [fluency, lexical, grammar, pronunciation] if s is not None]
    if not scores:
        return 6.0
    average = sum(scores) / len(scores)
    return round_to_ielts_band(average)


@dataclass
class CriterionEvidence:
    observations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    score: Optional[float] = None


@dataclass
class SpeakingAssessment:
    fluency: CriterionEvidence = field(default_factory=CriterionEvidence)
    vocabulary: CriterionEvidence = field(default_factory=CriterionEvidence)
    grammar: CriterionEvidence = field(default_factory=CriterionEvidence)
    pronunciation: CriterionEvidence = field(default_factory=CriterionEvidence)
    overall_band: float = 6.0
    confidence: float = 0.85


@dataclass
class IELTSOverallReport:
    session_id: str
    overall_band: float
    confidence: float
    criteria: Dict[str, Any]
    strengths: List[str]
    priority_improvements: List[str]
    part_analysis: Dict[str, Any]
    plan_7_day: List[Dict[str, str]]
