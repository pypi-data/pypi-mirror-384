from __future__ import annotations
from typing import Dict, List
from .elements import VALENCE


def hill_formula(counts: Dict[str, int]) -> str:
    """
    Produce a chemical formula string in Hill notation with hydrogen-like grouping.

    Hill notation rules used here:
      - If carbon (C) is present: put C first, then hydrogen-like elements (H, D, T),
        then all other element symbols in alphabetical order.
      - If carbon is not present: put hydrogen-like elements (H, D, T) first,
        then all other element symbols in alphabetical order.

    :param counts: Mapping from element symbol (e.g. "C", "H", "O") to integer counts.
                   Elements with zero or negative counts are omitted.
    :type counts: Dict[str, int]
    :returns: Hill-formatted formula string (empty string for empty/zero counts).
    :rtype: str
    """
    if not counts:
        return ""
    items: List[str] = []
    h_like = ("H", "D", "T")
    c_present = counts.get("C", 0) > 0

    def append_elem(e: str) -> None:
        n = counts.get(e, 0)
        if n > 0:
            items.append(f"{e}{'' if n == 1 else n}")

    if c_present:
        append_elem("C")
        for e in h_like:
            append_elem(e)
        others = sorted(e for e in counts.keys() if e not in ("C",) + h_like)
        for e in others:
            append_elem(e)
    else:
        for e in h_like:
            append_elem(e)
        others = sorted(e for e in counts.keys() if e not in h_like)
        for e in others:
            append_elem(e)
    return "".join(items)


def compute_dbe(counts: Dict[str, int]) -> float:
    """
    Compute the double-bond equivalents (DBE) using a simple valence heuristic.

    DBE is computed as:
        DBE = 1 + 0.5 * sum_i n_i * (valence_i - 2)

    Typical valences are taken from elements.VALENCE; elements missing from that table
    are treated as valence 0 (thus ignored for DBE).

    :param counts: Mapping from element symbol to integer counts.
    :type counts: Dict[str, int]
    :returns: Computed DBE as a float. Small negative numerical noise near zero is
              tidied to exactly 0.0.
    :rtype: float
    """
    s = 0.0
    for e, n in counts.items():
        if n <= 0:
            continue
        v = VALENCE.get(e, 0)
        s += n * (v - 2)
    dbe = 1.0 + 0.5 * s
    # numeric tidy
    if -1e-9 < dbe < 0:
        dbe = 0.0
    return float(dbe)
