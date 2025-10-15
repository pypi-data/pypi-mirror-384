from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Solution:
    """
    Representation of a proposed elemental formula solution.

    :param formula: Human-readable formula string (Hill notation).
    :type formula: str
    :param counts: Mapping element symbol -> integer count for the solution.
    :type counts: Dict[str, int]
    :param mass_calc: Calculated mass (float) of the proposed formula.
    :type mass_calc: float
    :param abs_error: Absolute error (float) between target mass and mass_calc.
    :type abs_error: float
    :param dbe: (Optional) double-bond equivalents computed for the counts.
    :type dbe: Optional[float]
    """

    formula: str
    counts: Dict[str, int]
    mass_calc: float
    abs_error: float
    dbe: Optional[float] = None
