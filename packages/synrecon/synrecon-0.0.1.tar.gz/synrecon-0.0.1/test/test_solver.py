import unittest
import json

from synrecon.chem import hill_formula, compute_dbe
from synrecon.elements import MONO_MASS
from synrecon.solver import enumerate_formulas, solve_formula


class TestSolver(unittest.TestCase):
    def test_hill_formula_and_dbe(self):
        counts = {"C": 6, "H": 6}
        self.assertEqual(hill_formula(counts), "C6H6")
        self.assertAlmostEqual(compute_dbe(counts), 4.0, places=6)

    def test_enumerate_contains_glucose(self):
        counts = {"C": 6, "H": 12, "O": 6}
        mass = sum(float(MONO_MASS[e]) * n for e, n in counts.items())
        sols = enumerate_formulas(
            mass_da=mass,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
            enforce_dbe=True,
        )
        formulas = [s.formula for s in sols]
        self.assertIn("C6H12O6", formulas)

    def test_solve_formula_best(self):
        counts = {"C": 6, "H": 12, "O": 6}
        mass = sum(float(MONO_MASS[e]) * n for e, n in counts.items())
        sol = solve_formula(
            mass_da=mass,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
            enforce_dbe=True,
        )
        self.assertIsNotNone(sol)
        self.assertEqual(sol.formula, "C6H12O6")

    def test_isotopologue_expansion_deuterium(self):
        counts = {"C": 6, "H": 12, "O": 6}
        base_mass = sum(float(MONO_MASS[e]) * n for e, n in counts.items())
        # Replace 1 H with D -> mass increases by D-H
        delta = float(MONO_MASS["D"] - MONO_MASS["H"])
        target = base_mass + delta

        # enumerate directly at the target mass with isotopologue expansion on
        sols2 = enumerate_formulas(
            mass_da=target,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
            enforce_dbe=True,
            allow_isotopes=True,
            labels=("D",),
            max_labels=1,
        )
        formulas2 = [s.formula for s in sols2]
        # Expect at least one with one D
        self.assertTrue(any("D" in f for f in formulas2), msg=str(formulas2))

    def test_no_candidates_for_small_mass(self):
        sols = enumerate_formulas(
            mass_da=0.3,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
        )
        self.assertEqual(len(sols), 0)

    def test_json_serializable_output(self):
        counts = {"C": 6, "H": 12, "O": 6}
        mass = sum(float(MONO_MASS[e]) * n for e, n in counts.items())
        sols = enumerate_formulas(
            mass_da=mass,
            elements=["C", "H", "O"],
            abs_tol_da=1e-5,
            enforce_dbe=True,
        )
        payload = [
            {
                "formula": s.formula,
                "counts": s.counts,
                "mass_calc": s.mass_calc,
                "abs_error": s.abs_error,
                "dbe": s.dbe,
            }
            for s in sols
        ]
        json.dumps(payload)  # should not raise


if __name__ == "__main__":
    unittest.main()
