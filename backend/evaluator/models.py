from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CriterionEvaluation:
    score: Optional[float]
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)


@dataclass
class IELTSEvaluation:
    fluency: CriterionEvaluation
    lexical_resource: CriterionEvaluation
    grammar: CriterionEvaluation
    pronunciation: CriterionEvaluation
    overall_band: float
    feedback: List[str] = field(default_factory=list)
