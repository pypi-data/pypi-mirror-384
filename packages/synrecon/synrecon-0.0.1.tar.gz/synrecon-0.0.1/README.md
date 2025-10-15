# SynRecon

Reconstruct molecular formulas from exact (monoisotopic) mass.

Given a neutral **exact (monoisotopic) mass**, **SynRecon** searches for a **non-negative integer composition** over a chosen element set that matches the mass within a configurable tolerance (default `1e-5` Da). Enumeration is performed using integer scaling with a fast DFS enumeration and an optional ILP backend. Scope: **basic single best formula**; optional chemistry filters (DBE ≥ 0, even-electron rule, nitrogen rule) can be enabled to tighten results.

**Highlights**
- Integer-weight DFS enumeration for raw candidate formulas.
- Optional chemical filters: DBE, even-electron rule, nitrogen rule.
- Optional simple isotopologue expansion (e.g. D for H).
- Small, dependency-light core; optional ILP backend for constrained searches.

---

## Install

```bash
pip install synrecon
```
## Quick examples

### Python API (recommended)

```python
from synrecon.solver import solve_formula, enumerate_formulas

# single best solution (or None)
sol = solve_formula(
    180.063388104,
    elements=["C", "H", "O"],
    abs_tol_da=1e-5,
    enforce_dbe=True,
)

if sol is None:
    print("No solution found within tolerance.")
else:
    print("Best formula:", sol.formula)
    print("Calculated mass:", sol.mass_calc)
    print("Absolute error (Da):", sol.abs_error)
    print("DBE:", sol.dbe)

# enumerate several candidates (more verbose)
candidates = enumerate_formulas(
    180.063388104,
    elements=["C", "H", "O"],
    abs_tol_da=1e-5,
    enforce_dbe=True,
    max_candidates=20,
    sort_by="abs_error",
)

print("\nTop candidates:")
for s in candidates[:10]:
    print(f"{s.formula:12s} mass={s.mass_calc:.6f} err={s.abs_error:.6e} dbe={s.dbe}")
```
### CLI

```bash
synrecon solve --mass 180.063388104 \
              --elements "C H O" \
              --tol 1e-5 \
              --dbe \
              --allow-isotopes \
              --labels "D T"
```


## Contributing
- [Tieu-Long Phan](https://tieulongphan.github.io/)

## Publication

[**SynRecon**:]()


## License

This project is licensed under MIT License - see the [License](LICENSE) file for details.

## Acknowledgments

This project has received funding from the European Unions Horizon Europe Doctoral Network programme under the Marie-Skłodowska-Curie grant agreement No 101072930 ([TACsy](https://tacsy.eu/) -- Training Alliance for Computational)