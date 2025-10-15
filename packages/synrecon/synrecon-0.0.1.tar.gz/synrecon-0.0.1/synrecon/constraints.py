from __future__ import annotations
import math
from decimal import Decimal
from typing import Dict, List
from .elements import MONO_MASS, ATOMIC_NO


def even_electron_ok(counts: Dict[str, int], charge: int) -> bool:
    """
    Parity proxy check: verifies that total nuclear charge parity minus the molecular
    charge is even (a quick even-electron-electronicity proxy).

    :param counts: Mapping from element symbol to integer counts.
    :type counts: Dict[str, int]
    :param charge: Total molecular charge (integer).
    :type charge: int
    :returns: True if (sum(Z_i * n_i) - charge) is even, False otherwise.
    :rtype: bool
    """
    s = sum(ATOMIC_NO.get(e, 0) * counts.get(e, 0) for e in counts)
    return ((s - charge) % 2) == 0


def nitrogen_rule_ok(n_count: int, nominal_mass: int) -> bool:
    """
    Apply the simple 'nitrogen rule' used for many neutral organic molecules:
    - If the nominal (integer) mass is odd, expect an odd number of nitrogen atoms.
    - If the nominal mass is even, expect an even number of nitrogen atoms.

    :param n_count: Number of nitrogen atoms in the formula.
    :type n_count: int
    :param nominal_mass: Nominal integer mass (e.g., floor of monoisotopic mass).
    :type nominal_mass: int
    :returns: True if nitrogen parity matches the nominal mass parity, else False.
    :rtype: bool
    """
    want_odd = nominal_mass % 2 == 1
    return (n_count % 2 == 1) if want_odd else (n_count % 2 == 0)


def default_upper_bounds(
    mass_da: Decimal, elements: List[str], mono_masses: Dict[str, Decimal]
) -> Dict[str, int]:
    """
    Provide conservative per-element upper bounds for counts based on the target mass.

    Upper bound for each element e is computed as:
        floor(mass_da / mono_masses[e]) + 2
    (with a fallback denominator of 1 if mono_masses[e] <= 0).

    :param mass_da: Target mass in daltons as Decimal.
    :type mass_da: Decimal
    :param elements: Sequence/list of element symbols to compute upper bounds for.
    :type elements: List[str]
    :param mono_masses: Mapping element symbol -> monoisotopic mass (Decimal).
    :type mono_masses: Dict[str, Decimal]
    :returns: Mapping element -> conservative integer upper bound.
    :rtype: Dict[str, int]
    """
    ub: Dict[str, int] = {}
    for e in elements:
        denom = mono_masses[e] if mono_masses[e] > 0 else Decimal("1")
        ub[e] = max(0, int(math.floor(float(mass_da / denom))) + 2)
    return ub


def ensure_mono_mass(symbol: str):
    """
    Return the monoisotopic mass for the given element symbol from the shared table,
    or raise a clear KeyError if the symbol is unknown.

    :param symbol: Element symbol to look up (e.g. 'C', 'H', 'O').
    :type symbol: str
    :returns: Monoisotopic mass value from MONO_MASS (type depends on MONO_MASS).
    :raises KeyError: If the symbol is not present in MONO_MASS.
    """
    try:
        return MONO_MASS[symbol]
    except KeyError as e:
        raise KeyError(
            "Monoisotopic mass for element '%s' is not in table. Extend MONO_MASS."
            % symbol
        ) from e
