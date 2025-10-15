from __future__ import annotations
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Set, FrozenSet

from .models import Solution
from .elements import MONO_MASS
from .chem import hill_formula, compute_dbe
from .constraints import (
    even_electron_ok,
    nitrogen_rule_ok,
    default_upper_bounds,
)


# ---------------------------------------------------------------------
# Mass-to-formula enumeration utilities
# ---------------------------------------------------------------------
def _dfs_search(
    order: List[str],
    W_units: Dict[str, int],
    upper_bounds: Dict[str, int],
    target_lo: int,
    target_hi: int,
    cum_max_weights: List[int],
    elements: List[str],
) -> List[Dict[str, int]]:
    results: List[Dict[str, int]] = []
    counts: Dict[str, int] = {e: 0 for e in order}

    def dfs(idx: int, mass_units_so_far: int) -> None:
        if mass_units_so_far > target_hi:
            return
        if mass_units_so_far + cum_max_weights[idx] < target_lo:
            return

        if idx == len(order):
            if target_lo <= mass_units_so_far <= target_hi:
                compact = {e: counts[e] for e in elements if counts.get(e, 0) > 0}
                results.append(compact)
            return

        e = order[idx]
        w = W_units[e]
        ub = upper_bounds[e]
        max_by_mass_hi = (target_hi - mass_units_so_far) // w if w > 0 else ub
        max_n = min(ub, int(max_by_mass_hi))
        for n_take in range(max_n, -1, -1):
            counts[e] = n_take
            dfs(idx + 1, mass_units_so_far + n_take * w)
        counts[e] = 0

    dfs(0, 0)
    return results


def _build_solution(
    compact: Dict[str, int], mm: Dict[str, Decimal], M_dec: Decimal
) -> Solution:
    mass_calc = sum(float(mm[e]) * n for e, n in compact.items())
    abs_err = abs(mass_calc - float(M_dec))
    return Solution(
        formula=hill_formula(compact),
        counts=compact,
        mass_calc=mass_calc,
        abs_error=abs_err,
        dbe=compute_dbe(compact),
    )


def _try_single_label_subs(
    base_counts: Dict[str, int],
    base_mass: float,
    target_mass: float,
    abs_tol: float,
    label: str,
    delta: float,
    max_k: int,
) -> List[Solution]:
    out: List[Solution] = []
    nH = base_counts.get("H", 0)
    if nH == 0:
        return out
    max_k = min(max_k, nH)
    for k in range(1, max_k + 1):
        mass_k = base_mass + k * delta
        if abs(mass_k - target_mass) <= abs_tol:
            counts = dict(base_counts)
            counts["H"] = nH - k
            counts[label] = counts.get(label, 0) + k
            out.append(
                Solution(
                    formula=hill_formula(counts),
                    counts=counts,
                    mass_calc=mass_k,
                    abs_error=abs(mass_k - target_mass),
                    dbe=compute_dbe(counts),
                )
            )
    return out


def _try_mixed_label_subs(
    base_counts: Dict[str, int],
    base_mass: float,
    target_mass: float,
    abs_tol: float,
    labels_deltas: List[Tuple[str, float]],
    max_labels: int,
) -> List[Solution]:
    out: List[Solution] = []
    if len(labels_deltas) < 2:
        return out
    (lbl1, dv1), (lbl2, dv2) = labels_deltas[0], labels_deltas[1]
    nH = base_counts.get("H", 0)
    if nH <= 1:
        return out
    maxk = min(nH, max_labels)
    for total_k in range(2, maxk + 1):
        for k1 in range(1, total_k):
            k2 = total_k - k1
            mass_k = base_mass + k1 * dv1 + k2 * dv2
            if abs(mass_k - target_mass) <= abs_tol and total_k <= nH:
                counts = dict(base_counts)
                counts["H"] = nH - total_k
                counts[lbl1] = counts.get(lbl1, 0) + k1
                counts[lbl2] = counts.get(lbl2, 0) + k2
                out.append(
                    Solution(
                        formula=hill_formula(counts),
                        counts=counts,
                        mass_calc=mass_k,
                        abs_error=abs(mass_k - target_mass),
                        dbe=compute_dbe(counts),
                    )
                )
    return out


def _expand_for_solution(
    s: Solution,
    target_mass: float,
    abs_tol: float,
    deltas: Dict[str, float],
    max_labels: int,
) -> List[Solution]:
    results: List[Solution] = [s]
    base_counts = s.counts
    base_mass = s.mass_calc
    nH = base_counts.get("H", 0)
    if nH == 0:
        return results
    max_possible_shift = max(deltas.values(), default=0.0) * min(nH, max_labels)
    if abs(target_mass - base_mass) > abs_tol + max_possible_shift:
        return results
    for lbl, dv in deltas.items():
        results.extend(
            _try_single_label_subs(
                base_counts, base_mass, target_mass, abs_tol, lbl, dv, max_labels
            )
        )
    labels_list = list(deltas.items())
    if len(labels_list) >= 2:
        results.extend(
            _try_mixed_label_subs(
                base_counts,
                base_mass,
                target_mass,
                abs_tol,
                labels_list[:2],
                max_labels,
            )
        )
    return results


def _expand_isotopologues(
    base_solutions: List[Solution],
    target_mass: float,
    abs_tol: float,
    labels: Tuple[str, ...] = ("D",),
    max_labels: int = 3,
) -> List[Solution]:
    mm = MONO_MASS
    deltas = {lbl: float((mm[lbl] - mm["H"])) for lbl in labels if lbl in mm}
    if not deltas:
        return base_solutions
    seen: Set[Tuple[str, int]] = set()
    SCALE = 10**7
    out: List[Solution] = []

    def push(sol: Solution) -> None:
        key = (sol.formula, int(round(sol.mass_calc * SCALE)))
        if key not in seen:
            seen.add(key)
            out.append(sol)

    for s in base_solutions:
        for sol in _expand_for_solution(s, target_mass, abs_tol, deltas, max_labels):
            push(sol)
    return out


def _prepare_enumeration(
    mass_da: float,
    elements: List[str],
    mono_masses: Dict[str, Decimal],
    abs_tol_da: float,
    ppm_tolerance: Optional[float],
    upper_bounds: Optional[Dict[str, int]],
):
    M_dec = Decimal(str(mass_da))
    if ppm_tolerance is not None:
        abs_tol_da = float((Decimal(str(ppm_tolerance)) * M_dec) / Decimal(1e6))
    SCALE = Decimal(10**7)
    M_units = int((M_dec * SCALE).to_integral_value(rounding="ROUND_HALF_UP"))
    tol_units = int(
        (Decimal(str(abs_tol_da)) * SCALE).to_integral_value(rounding="ROUND_HALF_UP")
    )
    if tol_units < 1:
        tol_units = 1
    W_units: Dict[str, int] = {
        e: int((mono_masses[e] * SCALE).to_integral_value(rounding="ROUND_HALF_UP"))
        for e in elements
    }
    if upper_bounds is None:
        upper_bounds = default_upper_bounds(M_dec, list(elements), mono_masses)
    else:
        for e in elements:
            if e not in upper_bounds:
                upper_bounds[e] = default_upper_bounds(M_dec, [e], mono_masses)[e]
    order = sorted(elements, key=lambda el: W_units[el], reverse=True)
    target_lo = M_units - tol_units
    target_hi = M_units + tol_units
    cum_max_weights = [0] * (len(order) + 1)
    for i in range(len(order) - 1, -1, -1):
        e = order[i]
        cum_max_weights[i] = cum_max_weights[i + 1] + W_units[e] * upper_bounds[e]
    return {
        "M_dec": M_dec,
        "W_units": W_units,
        "order": order,
        "target_lo": target_lo,
        "target_hi": target_hi,
        "cum_max_weights": cum_max_weights,
        "upper_bounds": upper_bounds,
        "abs_tol_da": abs_tol_da,
    }


def _filter_and_build_solutions(
    raw_counts_list: List[Dict[str, int]],
    mm: Dict[str, Decimal],
    M_dec: Decimal,
    enforce_dbe: bool,
    enforce_even_electron: bool,
    nitrogen_rule: bool,
    charge: int,
    max_candidates: Optional[int],
) -> List[Solution]:
    solutions: List[Solution] = []
    for compact in raw_counts_list:
        if enforce_dbe and compute_dbe(compact) < 0.0:
            continue
        if enforce_even_electron and not even_electron_ok(compact, charge=charge):
            continue
        if nitrogen_rule:
            nominal = int(M_dec.to_integral_value(rounding="ROUND_HALF_UP"))
            if not nitrogen_rule_ok(compact.get("N", 0), nominal):
                continue
        solutions.append(_build_solution(compact, mm, M_dec))
        if max_candidates is not None and len(solutions) >= max_candidates:
            break
    return solutions


def _sort_solutions(solutions: List[Solution], sort_by: str) -> None:
    if sort_by == "abs_error":
        solutions.sort(key=lambda s: (s.abs_error, s.formula))
    elif sort_by == "mass":
        solutions.sort(key=lambda s: (s.mass_calc, s.formula))
    elif sort_by == "formula":
        solutions.sort(key=lambda s: s.formula)
    elif sort_by == "dbe":
        solutions.sort(
            key=lambda s: (s.dbe if s.dbe is not None else 0.0, s.abs_error, s.formula)
        )
    else:
        solutions.sort(key=lambda s: (s.abs_error, s.formula))


def _build_masses_to_search(
    mass_da: float,
    mm: Dict[str, Decimal],
    labels: Tuple[str, ...],
    max_labels: int,
    allow_isotopes: bool,
) -> List[float]:
    """
    Return a deduplicated list of masses we will enumerate raw counts for.
    Always include mass_da. If allow_isotopes, also include mass_da - k*delta
    for k=1..max_labels for each label.
    """
    masses: List[float] = [mass_da]
    if allow_isotopes and labels and max_labels > 0:
        for lbl in labels:
            if lbl not in mm:
                continue
            delta = float(mm[lbl] - mm["H"])
            for k in range(1, max_labels + 1):
                masses.append(mass_da - k * delta)
    # deduplicate while preserving order (float keys)
    seen: Set[float] = set()
    out: List[float] = []
    for m in masses:
        if m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out


def _collect_raw_counts_for_masses(
    masses: List[float],
    elements: List[str],
    mm: Dict[str, Decimal],
    abs_tol_da: float,
    ppm_tolerance: Optional[float],
    upper_bounds: Optional[Dict[str, int]],
) -> List[Dict[str, int]]:
    """
    Run _dfs_search for each mass in masses, deduplicate compact counts and
    return a combined list.
    """
    raw_counts_combined: List[Dict[str, int]] = []
    seen_counts: Set[FrozenSet[Tuple[str, int]]] = set()
    for m in masses:
        prep = _prepare_enumeration(
            m, elements, mm, abs_tol_da, ppm_tolerance, upper_bounds
        )
        raw = _dfs_search(
            prep["order"],
            prep["W_units"],
            prep["upper_bounds"],
            prep["target_lo"],
            prep["target_hi"],
            prep["cum_max_weights"],
            elements,
        )
        for compact in raw:
            key = frozenset(compact.items())
            if key not in seen_counts:
                seen_counts.add(key)
                raw_counts_combined.append(compact)
    return raw_counts_combined


def enumerate_formulas(
    mass_da: float,
    elements: List[str] = ("C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"),
    mono_masses: Optional[Dict[str, Decimal]] = None,
    abs_tol_da: float = 1e-5,
    ppm_tolerance: Optional[float] = None,
    charge: int = 0,
    enforce_dbe: bool = False,
    enforce_even_electron: bool = False,
    nitrogen_rule: bool = False,
    upper_bounds: Optional[Dict[str, int]] = None,
    max_candidates: Optional[int] = None,
    sort_by: str = "abs_error",
    allow_isotopes: bool = False,
    labels: Tuple[str, ...] = ("D",),
    max_labels: int = 3,
) -> List[Solution]:
    """
    Enumerate plausible molecular formulas for a given monoisotopic mass.

    The function performs an integer-weight depth-first enumeration over the
    provided element set to find element-count combinations whose calculated
    monoisotopic mass lies within the specified absolute tolerance (or the
    derived tolerance from a ppm value). Optional chemical filters (DBE,
    even-electron rule, nitrogen rule) are applied and the results are
    returned as a list of :class:`~.models.Solution` objects.

    :param mass_da: Target monoisotopic mass (in daltons).
    :type mass_da: float
    :param elements: Iterable of element symbols to consider (defaults to common
    CHNOPS halogens).
    :type elements: List[str]
    :param mono_masses: Optional dictionary mapping element symbols to Decimal
    monoisotopic masses. If None, the module-level MONO_MASS is used.
    :type mono_masses: Optional[Dict[str, Decimal]]
    :param abs_tol_da: Absolute mass tolerance in daltons. Ignored if `
    `ppm_tolerance`` is provided.
    :type abs_tol_da: float
    :param ppm_tolerance: If provided, ppm tolerance will be converted to
    an absolute dalton tolerance using the target mass:
    abs_tol = ppm * mass / 1e6.
    :type ppm_tolerance: Optional[float]
    :param charge: Molecular charge used for even-electron filtering.
    :type charge: int
    :param enforce_dbe: If True, discard formulas with negative DBE
    (degree of unsaturation).
    :type enforce_dbe: bool
    :param enforce_even_electron: If True, enforce the even-electron rule
    (using provided charge).
    :type enforce_even_electron: bool
    :param nitrogen_rule: If True, apply the nominal-mass nitrogen rule check.
    :type nitrogen_rule: bool
    :param upper_bounds: Optional per-element upper bounds for counts.
    When omitted, defaults are computed.
    :type upper_bounds: Optional[Dict[str, int]]
    :param max_candidates: Optional maximum number of candidates to return
    (filters after enumeration).
    :type max_candidates: Optional[int]
    :param sort_by: Sorting key for final solutions. One of: "abs_error",
    "mass", "formula", "dbe".
    :type sort_by: str
    :param allow_isotopes: If True, expand candidate formulas to include simple
    isotopologue substitutions
                           (e.g. D for H) around matching masses.
    :type allow_isotopes: bool
    :param labels: Tuple of label element symbols (e.g. ("D",)) to consider for
    simple isotopologue expansion.
    :type labels: Tuple[str, ...]
    :param max_labels: Maximum number of label substitutions to consider when
    expanding isotopologues.
    :type max_labels: int

    :return: A list of :class:`~.models.Solution` objects matching the mass and filters.
    :rtype: List[Solution]

    :raises ValueError: If a requested element is missing from the provided
    monoisotopic mass table.

    Example
    -------

    Basic usage to enumerate CHO formulas near 180.063388104 Da:

    .. code-block:: python

        from synrecon.solver import enumerate_formulas
        sols = enumerate_formulas(
            180.063388104,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
            enforce_dbe=True
        )
        for s in sols[:5]:
            print(s.formula, s.mass_calc, s.abs_error)

    The function will return multiple Solution objects; inspect ``Solution.formula`` and
    ``Solution.abs_error`` to find the best matches.
    """
    mm = dict(MONO_MASS if mono_masses is None else mono_masses)
    for e in elements:
        if e not in mm:
            raise ValueError(f"Missing monoisotopic mass for element '{e}'")

    masses = _build_masses_to_search(mass_da, mm, labels, max_labels, allow_isotopes)

    raw_counts_combined = _collect_raw_counts_for_masses(
        masses, elements, mm, abs_tol_da, ppm_tolerance, upper_bounds
    )

    M_dec = Decimal(str(mass_da))
    solutions = _filter_and_build_solutions(
        raw_counts_combined,
        mm,
        M_dec,
        enforce_dbe,
        enforce_even_electron,
        nitrogen_rule,
        charge,
        max_candidates,
    )

    if allow_isotopes and solutions:
        solutions = _expand_isotopologues(
            solutions, float(M_dec), abs_tol_da, labels=labels, max_labels=max_labels
        )

    _sort_solutions(solutions, sort_by)
    return solutions


def solve_formula(
    mass_da: float,
    elements: List[str] = ("C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"),
    mono_masses: Optional[Dict[str, Decimal]] = None,
    abs_tol_da: float = 1e-5,
    ppm_tolerance: Optional[float] = None,
    charge: int = 0,
    enforce_dbe: bool = False,
    enforce_even_electron: bool = False,
    nitrogen_rule: bool = False,
    upper_bounds: Optional[Dict[str, int]] = None,
    allow_isotopes: bool = False,
    labels: Tuple[str, ...] = ("D",),
    max_labels: int = 3,
) -> Optional[Solution]:
    """
    Convenience wrapper that returns the single best-matching formula (or None).

    This calls :func:`enumerate_formulas` with reasonable defaults for candidate
    selection and returns the first solution (sorted by absolute mass error).
    Use :func:`enumerate_formulas` directly when multiple candidates are desired.

    :param mass_da: Target monoisotopic mass (in daltons).
    :type mass_da: float
    :param elements: Iterable of element symbols to consider.
    :type elements: List[str]
    :param mono_masses: Optional dictionary mapping element symbols to
    Decimal monoisotopic masses.
    :type mono_masses: Optional[Dict[str, Decimal]]
    :param abs_tol_da: Absolute mass tolerance in daltons.
    :type abs_tol_da: float
    :param ppm_tolerance: Optional ppm tolerance; if provided, overrides
    ``abs_tol_da`` calculation.
    :type ppm_tolerance: Optional[float]
    :param charge: Molecular charge used for even-electron filtering.
    :type charge: int
    :param enforce_dbe: If True, discard formulas with negative DBE.
    :type enforce_dbe: bool
    :param enforce_even_electron: If True, enforce the even-electron rule.
    :type enforce_even_electron: bool
    :param nitrogen_rule: If True, apply nominal-mass nitrogen rule.
    :type nitrogen_rule: bool
    :param upper_bounds: Optional per-element upper bounds for counts.
    :type upper_bounds: Optional[Dict[str, int]]
    :param allow_isotopes: If True, expand isotopologues around candidate formulas.
    :type allow_isotopes: bool
    :param labels: Tuple of label element symbols to consider for isotopologue expansion.
    :type labels: Tuple[str, ...]
    :param max_labels: Maximum number of label substitutions to consider
    when expanding isotopologues.
    :type max_labels: int

    :return: The best-matching :class:`~.models.Solution` or None if no candidates found.
    :rtype: Optional[Solution]

    Example
    -------

    Simple single-solution call:

    .. code-block:: python

        from synrecon.solver import solve_formula
        sol = solve_formula(
            180.063388104,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
            enforce_dbe=True
        )
        if sol is not None:
            print(sol.formula, sol.mass_calc, sol.abs_error)
        else:
            print("No formula found within tolerance.")
    """
    sols = enumerate_formulas(
        mass_da=mass_da,
        elements=elements,
        mono_masses=mono_masses,
        abs_tol_da=abs_tol_da,
        ppm_tolerance=ppm_tolerance,
        charge=charge,
        enforce_dbe=enforce_dbe,
        enforce_even_electron=enforce_even_electron,
        nitrogen_rule=nitrogen_rule,
        upper_bounds=upper_bounds,
        max_candidates=None,
        sort_by="abs_error",
        allow_isotopes=allow_isotopes,
        labels=labels,
        max_labels=max_labels,
    )
    return sols[0] if sols else None
