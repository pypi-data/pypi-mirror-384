from __future__ import annotations
from decimal import Decimal
from typing import Dict

# --------------------------------------------
# Atomic-number map (periodic table) 1..118
# --------------------------------------------
Z_TO_SYMBOL = [
    None,
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",  # 1..10
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",  # 11..20
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",  # 21..30
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",  # 31..40
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",  # 41..50
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",  # 51..60
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",  # 61..70
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",  # 71..80
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Th",
    "U",
]


ATOMIC_NO: Dict[str, int] = {sym: z for z, sym in enumerate(Z_TO_SYMBOL) if sym}

# -------------------------------------------
# Monoisotopic masses (exact masses, Decimal)
# Coverage: practical MS elements + D/T
# -------------------------------------------
MONO_MASS: Dict[str, Decimal] = {
    # ... (kept identical to original) ...
    "H": Decimal("1.00782503223"),
    "D": Decimal("2.01410177812"),
    "T": Decimal("3.01604927790"),
    "He": Decimal("4.00260325413"),
    "Li": Decimal("7.0160034366"),
    "Be": Decimal("9.012183065"),
    "B": Decimal("11.00930536"),
    "C": Decimal("12.000000000"),
    "N": Decimal("14.00307400443"),
    "O": Decimal("15.99491461957"),
    "F": Decimal("18.99840316273"),
    "Ne": Decimal("19.9924401762"),
    "Na": Decimal("22.9897692820"),
    "Mg": Decimal("23.985041697"),
    "Al": Decimal("26.98153853"),
    "Si": Decimal("27.97692653465"),
    "P": Decimal("30.97376199842"),
    "S": Decimal("31.9720711744"),
    "Cl": Decimal("34.968852682"),
    "Ar": Decimal("39.9623831237"),
    "K": Decimal("38.9637064864"),
    "Ca": Decimal("39.962590863"),
    "Sc": Decimal("44.955907"),
    "Ti": Decimal("47.94794198"),
    "V": Decimal("50.943957"),
    "Cr": Decimal("51.94050623"),
    "Mn": Decimal("54.93804391"),
    "Fe": Decimal("55.93493633"),
    "Co": Decimal("58.93319429"),
    "Ni": Decimal("57.93534241"),
    "Cu": Decimal("62.92959772"),
    "Zn": Decimal("63.92914201"),
    "Ga": Decimal("68.9255735"),
    "Ge": Decimal("73.921177761"),
    "As": Decimal("74.92159457"),
    "Se": Decimal("79.9165218"),
    "Br": Decimal("78.9183376"),
    "Kr": Decimal("83.9114977282"),
    "Rb": Decimal("84.9117897379"),
    "Sr": Decimal("87.9056125"),
    "Y": Decimal("88.9058403"),
    "Zr": Decimal("89.9046977"),
    "Nb": Decimal("92.9063730"),
    "Mo": Decimal("97.90540482"),
    "Tc": Decimal("97.907216"),
    "Ru": Decimal("101.9043441"),
    "Rh": Decimal("102.905498"),
    "Pd": Decimal("105.9034804"),
    "Ag": Decimal("106.9050916"),
    "Cd": Decimal("113.90336509"),
    "In": Decimal("112.90406184"),
    "Sn": Decimal("119.90220163"),
    "Sb": Decimal("120.9038120"),
    "Te": Decimal("129.906222748"),
    "I": Decimal("126.9044719"),
    "Xe": Decimal("131.9041535"),
    "Cs": Decimal("132.9054519610"),
    "Ba": Decimal("137.9052472"),
    "La": Decimal("138.9063563"),
    "Ce": Decimal("139.9054431"),
    "Pr": Decimal("140.9076576"),
    "Nd": Decimal("141.9077290"),
    "Pm": Decimal("144.912749"),
    "Sm": Decimal("151.9197397"),
    "Eu": Decimal("152.9212303"),
    "Gd": Decimal("157.9241039"),
    "Tb": Decimal("158.9253547"),
    "Dy": Decimal("163.9291819"),
    "Ho": Decimal("164.9303288"),
    "Er": Decimal("165.9302995"),
    "Tm": Decimal("168.9342179"),
    "Yb": Decimal("173.9388664"),
    "Lu": Decimal("174.9407718"),
    "Hf": Decimal("175.9414018"),
    "Ta": Decimal("180.9479958"),
    "W": Decimal("183.95093092"),
    "Re": Decimal("184.9529550"),
    "Os": Decimal("191.9614807"),
    "Ir": Decimal("192.9629260"),
    "Pt": Decimal("194.9647917"),
    "Au": Decimal("196.96656879"),
    "Hg": Decimal("199.96832659"),
    "Tl": Decimal("202.9723446"),
    "Pb": Decimal("203.9730440"),
    "Bi": Decimal("208.9803991"),
    "Po": Decimal("208.9824308"),
    "At": Decimal("209.9871479"),
    "Rn": Decimal("222.0175782"),
    "Th": Decimal("232.0380558"),
    "U": Decimal("238.05078826"),
}


def ensure_mono_mass(symbol: str) -> Decimal:
    """
    Return monoisotopic mass for element symbol or raise a clear error.

    :param symbol: Element symbol to lookup (e.g., 'C', 'H').
    :type symbol: str
    :returns: Monoisotopic mass as Decimal.
    :rtype: Decimal
    :raises KeyError: If the symbol is not present in MONO_MASS.
    """
    try:
        return MONO_MASS[symbol]
    except KeyError as e:
        msg = (
            f"Monoisotopic mass for element '{symbol}' is not in table. "
            "If you need it, extend MONO_MASS with the most-abundant"
            + " isotope's exact mass."
        )
        raise KeyError(msg) from e


# ----------------------------------------------------
# Typical valences for DBE heuristics in organic space
# ----------------------------------------------------
VALENCE: Dict[str, int] = {
    "H": 1,
    "D": 1,
    "T": 1,
    "F": 1,
    "Cl": 1,
    "Br": 1,
    "I": 1,
    "C": 4,
    "Si": 4,
    "Ge": 4,
    "Sn": 4,
    "Pb": 4,
    "N": 3,
    "P": 3,
    "As": 3,
    "Sb": 3,
    "O": 2,
    "S": 2,
    "Se": 2,
    "Te": 2,
}

ORGANIC_DEFAULT = ("C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I")

__all__ = [
    "Z_TO_SYMBOL",
    "ATOMIC_NO",
    "MONO_MASS",
    "VALENCE",
    "ORGANIC_DEFAULT",
    "ensure_mono_mass",
]
