import importlib
import math
import unittest
from unittest import mock
from synrecon.chem import hill_formula, compute_dbe

MOD = importlib.import_module("synrecon.chem")


def _load_valence():
    """Find a VALENCE mapping to use for expected DBE calculations.

    Order of attempts:
      1) sibling `elements` module in the same package as MOD
      2) top-level `elements` module
      3) fallback default mapping for common elements
    """
    pkg = getattr(MOD, "__package__", None)
    if pkg:
        try:
            elements = importlib.import_module(pkg + ".elements")
            if hasattr(elements, "VALENCE"):
                return elements.VALENCE
        except Exception:
            pass
    try:
        elements = importlib.import_module("elements")
        if hasattr(elements, "VALENCE"):
            return elements.VALENCE
    except Exception:
        pass
    return {"C": 4, "H": 1, "O": 2, "N": 3, "S": 2, "Cl": 1, "Br": 1}


VALENCE = _load_valence()


class TestHillAndDBE(unittest.TestCase):
    # ---------- Hill formula tests ----------

    def test_hill_formula_empty_and_zero_counts(self):
        self.assertEqual(hill_formula({}), "")
        # defensive: zeros should be omitted and produce empty string
        self.assertEqual(hill_formula({"C": 0, "H": 0}), "")

    def test_hill_formula_carbon_present_ordering(self):
        counts = {"C": 6, "H": 12, "O": 6, "N": 1, "Cl": 1}
        got = hill_formula(counts)
        # C first then H-like group: check start
        self.assertTrue(got.startswith("C6H12"), f"unexpected start: {got!r}")
        # ensure Cl, N, O present
        self.assertIn("Cl", got)
        self.assertIn("N", got)
        self.assertIn("O", got)
        # Check ordering among tail elements after the "C6H12"
        tail_start = len("C6H12")
        pos_cl = got.find("Cl", tail_start)
        pos_n = got.find("N", tail_start)
        pos_o = got.find("O", tail_start)
        self.assertNotEqual(pos_cl, -1)
        self.assertNotEqual(pos_n, -1)
        self.assertNotEqual(pos_o, -1)
        self.assertLess(pos_cl, pos_n, f"expected 'Cl' before 'N' in {got!r}")
        self.assertLess(pos_n, pos_o, f"expected 'N' before 'O' in {got!r}")

    def test_hill_formula_no_carbon_h_like_first(self):
        counts = {"H": 2, "O": 1, "C": 0, "D": 1, "B": 3}
        got = hill_formula(counts)
        # locate first H-like occurrence (H, D or T)
        indices = {sym: got.find(sym) for sym in ("H", "D", "T")}
        # pick smallest non-negative index
        first_h_like_pos = min((i for i in indices.values() if i != -1), default=-1)
        self.assertNotEqual(first_h_like_pos, -1, f"No H-like element found in {got!r}")
        pos_b = got.find("B")
        pos_o = got.find("O")
        self.assertNotEqual(pos_b, -1, f"No 'B' found in {got!r}")
        self.assertNotEqual(pos_o, -1, f"No 'O' found in {got!r}")
        self.assertLess(
            first_h_like_pos, pos_b, f"H-like group should appear before 'B' in {got!r}"
        )
        self.assertLess(
            first_h_like_pos, pos_o, f"H-like group should appear before 'O' in {got!r}"
        )
        # ensure B and O appear in alphabetical order (B before O)
        self.assertLess(pos_b, pos_o, f"'B' should appear before 'O' in {got!r}")

    def test_hill_formula_omit_zero_and_negative_counts(self):
        counts = {"C": 1, "H": 0, "O": -2, "N": 1}
        got = hill_formula(counts)
        self.assertNotIn("H", got)
        self.assertNotIn("O", got)
        self.assertIn("C", got)
        self.assertIn("N", got)

    def test_hill_formula_count_one_omits_digit(self):
        counts = {"C": 1, "H": 1, "O": 1}
        got = hill_formula(counts)
        # single counts should omit the '1'
        self.assertIn("C", got)
        self.assertNotIn("C1", got)
        self.assertIn("H", got)
        self.assertNotIn("H1", got)
        self.assertIn("O", got)
        self.assertNotIn("O1", got)

    # ---------- DBE tests ----------

    @staticmethod
    def _expected_dbe_from_valence(counts, valence_map):
        s = 0.0
        for e, n in counts.items():
            if n <= 0:
                continue
            v = valence_map.get(e, 0)
            s += n * (v - 2)
        dbe = 1.0 + 0.5 * s
        if -1e-9 < dbe < 0:
            dbe = 0.0
        return float(dbe)

    def test_compute_dbe_basic_common_molecules(self):
        cases = {
            "glucose_like": ({"C": 6, "H": 12, "O": 6}, None),
            "water": ({"H": 2, "O": 1}, None),
            "ammonia": ({"N": 1, "H": 3}, None),
            "benzene": ({"C": 6, "H": 6}, None),
        }
        for name, (counts, _) in cases.items():
            with self.subTest(name=name):
                expected = self._expected_dbe_from_valence(counts, VALENCE)
                got = compute_dbe(counts)
                self.assertIsInstance(got, float)
                self.assertTrue(
                    math.isclose(got, expected, rel_tol=1e-12, abs_tol=1e-12),
                    f"DBE mismatch for {name}: expected {expected}, got {got}",
                )

    def test_compute_dbe_ignores_non_positive_counts(self):
        counts = {"C": 2, "H": 4, "X": 0, "Y": -3}
        expected = self._expected_dbe_from_valence({"C": 2, "H": 4}, VALENCE)
        got = compute_dbe(counts)
        self.assertTrue(math.isclose(got, expected, rel_tol=1e-12, abs_tol=1e-12))

    def test_compute_dbe_numeric_tidy_patch(self):
        tiny_negative_v = 2.0 - 2.000000000001  # very small negative offset
        patched_valence = {"X": tiny_negative_v}
        with mock.patch.object(MOD, "VALENCE", patched_valence, create=True):
            counts = {"X": 1}
            got = compute_dbe(counts)
            self.assertEqual(got, 0.0)

    # ---------- fuzz / regression sanity checks ----------

    def test_hill_formula_parametric_examples(self):
        examples = [
            ({"C": 1, "H": 1, "O": 1}, ["C", "H", "O"]),
            ({"H": 3, "D": 1, "T": 2, "Li": 1}, ["H", "D", "T", "Li"]),
        ]
        for counts, expected_contains in examples:
            with self.subTest(counts=counts):
                s = hill_formula(counts)
                for sym in expected_contains:
                    self.assertIn(sym, s)


if __name__ == "__main__":
    unittest.main()
