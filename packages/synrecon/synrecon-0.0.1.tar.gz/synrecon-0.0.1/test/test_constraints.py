from __future__ import annotations

import unittest
from decimal import Decimal
from typing import Dict, List

from synrecon.constraints import (
    even_electron_ok,
    nitrogen_rule_ok,
    default_upper_bounds,
    ensure_mono_mass,
    MONO_MASS,
    ATOMIC_NO,
)


class TestConstraintsHelpers(unittest.TestCase):
    # ---------- even_electron_ok tests ----------
    @unittest.skipUnless(
        "H" in ATOMIC_NO and "C" in ATOMIC_NO, "ATOMIC_NO missing expected elements"
    )
    def test_even_electron_simple_true_false(self):
        # H atomic number = 1 -> parity: H=2 -> even, H=1 -> odd
        self.assertTrue(even_electron_ok({"H": 2}, charge=0))
        self.assertFalse(even_electron_ok({"H": 1}, charge=0))
        # Carbon Z=6 -> one carbon neutral is even
        self.assertTrue(even_electron_ok({"C": 1}, charge=0))

    @unittest.skipUnless("H" in ATOMIC_NO, "ATOMIC_NO missing H")
    def test_even_electron_with_charge(self):
        # H=2 with +1 charge: (2 - 1) is odd -> False
        self.assertFalse(even_electron_ok({"H": 2}, charge=1))
        # H=1 with -1 charge: (1 - (-1)) = 2 -> even -> True
        self.assertTrue(even_electron_ok({"H": 1}, charge=-1))

    # ---------- nitrogen_rule_ok tests ----------
    def test_nitrogen_rule_odd_even(self):
        # nominal mass odd -> expect odd N count
        self.assertTrue(nitrogen_rule_ok(n_count=1, nominal_mass=15))
        self.assertFalse(nitrogen_rule_ok(n_count=2, nominal_mass=15))
        # nominal mass even -> expect even N count
        self.assertTrue(nitrogen_rule_ok(n_count=2, nominal_mass=14))
        self.assertFalse(nitrogen_rule_ok(n_count=1, nominal_mass=14))

    # ---------- default_upper_bounds tests ----------
    def test_default_upper_bounds_basic(self):
        # Use explicit Decimal masses to match function signature
        mass_da = Decimal("180.0")
        mono_masses: Dict[str, Decimal] = {
            "C": Decimal("12.0"),  # typical carbon monoisotopic mass (approx)
            "H": Decimal("1.0"),
            "X": Decimal("0"),  # force fallback to denom = 1
        }
        elements: List[str] = ["C", "H", "X"]
        ub = default_upper_bounds(mass_da, elements, mono_masses)

        # Expected calculations:
        # C: floor(180.0 / 12.0) = floor(15.0) = 15 -> +2 => 17
        # H: floor(180.0 / 1.0) = 180 -> +2 => 182
        # X: mono_masses["X"] <= 0 so denom becomes 1 -> floor(180.0/1)=180->+2=> 182
        expected = {"C": 17, "H": 182, "X": 182}
        self.assertEqual(ub, expected)

    def test_default_upper_bounds_nonpositive_masses(self):

        mass_da = Decimal("50.0")
        mono_masses: Dict[str, Decimal] = {"A": Decimal("-5.0")}
        elements = ["A"]
        ub = default_upper_bounds(mass_da, elements, mono_masses)
        # floor(50/1) + 2 = 50 + 2 = 52
        self.assertEqual(ub["A"], 52)

    # ---------- ensure_mono_mass tests ----------
    @unittest.skipUnless(bool(MONO_MASS), "MONO_MASS table is empty or missing")
    def test_ensure_mono_mass_present_and_missing(self):
        # pick a known key from MONO_MASS (prefer 'C' if present)
        key = "C" if "C" in MONO_MASS else next(iter(MONO_MASS))
        val = ensure_mono_mass(key)
        # ensure return type is numeric-like (Decimal or float)
        self.assertTrue(
            hasattr(val, "as_tuple") or isinstance(val, (int, float, Decimal))
        )

        # unknown symbol should raise KeyError
        with self.assertRaises(KeyError):
            ensure_mono_mass("Unobtanium123")


if __name__ == "__main__":
    unittest.main()
