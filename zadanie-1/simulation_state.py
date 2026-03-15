from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class ProbabilityRow:
    city: str
    d: float
    eta: float
    weight: float
    p: float
    cumulative: float


@dataclass
class StepState:
    step_no: int

    current_before: str
    current_after: str

    visited_before: List[str]
    visited_after: List[str]

    unvisited_before: List[str]

    rows: List[ProbabilityRow]

    rand_value: Optional[float]
    chosen: str

    path_before: List[str]
    path_after: List[str]

    total_length_before: float
    total_length_after: float
    step_distance: float