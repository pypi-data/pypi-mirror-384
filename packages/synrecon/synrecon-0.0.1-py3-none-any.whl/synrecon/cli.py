# cli.py
from __future__ import annotations
import json
import sys
import re
from typing import List, Optional, Tuple

import click

from .solver import enumerate_formulas, solve_formula
from .elements import ORGANIC_DEFAULT

_DEFAULT_ELEMENTS_STR = " ".join(ORGANIC_DEFAULT)


def _parse_elements(value: Optional[str]) -> List[str]:
    """Parse element list from a space- or comma-separated string."""
    if not value:
        return list(ORGANIC_DEFAULT)
    parts = re.split(r"[,\s]+", value.strip())
    elems = [p for p in parts if p]
    return elems if elems else list(ORGANIC_DEFAULT)


def _parse_labels(value: Optional[str]) -> Tuple[str, ...]:
    """Parse isotopic label tokens like 'D' or 'D T' into a tuple."""
    if not value:
        return ("D",)
    parts = re.split(r"[,\s]+", value.strip())
    labels = tuple([p for p in parts if p])
    return labels if labels else ("D",)


@click.group()
def cli():
    """Exact-mass → molecular-formula utilities (with optional isotopologues)."""


@cli.command("solve")
@click.option(
    "--mass",
    "mass_da",
    type=float,
    required=True,
    help="Neutral monoisotopic mass (Da).",
)
@click.option(
    "--elements",
    "-e",
    "elements_str",
    type=str,
    default=_DEFAULT_ELEMENTS_STR,
    help=(
        "Allowed elements as a single string: space- or comma-separated. "
        'Example: --elements "C H O" or --elements "C,H,O".'
    ),
)
@click.option(
    "--tol",
    "abs_tol_da",
    type=float,
    default=1e-5,
    show_default=True,
    help="Absolute tolerance (Da).",
)
@click.option(
    "--ppm",
    "ppm",
    type=float,
    default=None,
    help="PPM tolerance (overrides absolute tol).",
)
@click.option(
    "--charge",
    type=int,
    default=0,
    show_default=True,
    help="Net charge for even-electron parity.",
)
@click.option(
    "--dbe/--no-dbe",
    "enforce_dbe",
    default=False,
    show_default=True,
    help="Enforce DBE ≥ 0.",
)
@click.option(
    "--even/--no-even",
    "enforce_even",
    default=False,
    show_default=True,
    help="Enforce even-electron parity.",
)
@click.option(
    "--nrule/--no-nrule",
    "nitrogen_rule",
    default=False,
    show_default=True,
    help="Apply nitrogen rule based on nominal-mass parity.",
)
@click.option(
    "--allow-isotopes/--no-allow-isotopes",
    default=False,
    show_default=True,
    help="Expand H-containing hits into isotopologues (H→D/T) post-enumeration.",
)
@click.option(
    "--labels",
    type=str,
    default="D",
    show_default=True,
    help="Isotope labels to consider when --allow-isotopes is on (e.g. 'D' or 'D T').",
)
@click.option(
    "--max-labels",
    type=int,
    default=3,
    show_default=True,
    help="Max number of H atoms replaced across all labels.",
)
def cmd_solve(
    mass_da,
    elements_str,
    abs_tol_da,
    ppm,
    charge,
    enforce_dbe,
    enforce_even,
    nitrogen_rule,
    allow_isotopes,
    labels,
    max_labels,
):
    """Return the single best candidate within tolerance."""
    elements = _parse_elements(elements_str)
    label_tuple = _parse_labels(labels)

    sol = solve_formula(
        mass_da=mass_da,
        elements=elements,
        abs_tol_da=abs_tol_da,
        ppm_tolerance=ppm,
        charge=charge,
        enforce_dbe=enforce_dbe,
        enforce_even_electron=enforce_even,
        nitrogen_rule=nitrogen_rule,
        allow_isotopes=allow_isotopes,
        labels=label_tuple,
        max_labels=max_labels,
    )
    if sol is None:
        click.echo("No feasible formula within tolerance.", err=True)
        sys.exit(2)

    click.echo(
        f"{sol.formula}\tmass={sol.mass_calc:.9f}\t"
        f"err={sol.abs_error:.9g}\tDBE={sol.dbe:.3f}"
    )


@cli.command("enumerate")
@click.option(
    "--mass",
    "mass_da",
    type=float,
    required=True,
    help="Neutral monoisotopic mass (Da).",
)
@click.option(
    "--elements",
    "-e",
    "elements_str",
    type=str,
    default=_DEFAULT_ELEMENTS_STR,
    help=(
        "Allowed elements as a single string: space- or comma-separated. "
        'Example: --elements "C H O" or --elements "C,H,O".'
    ),
)
@click.option(
    "--tol",
    "abs_tol_da",
    type=float,
    default=1e-5,
    show_default=True,
    help="Absolute tolerance (Da).",
)
@click.option(
    "--ppm",
    "ppm",
    type=float,
    default=None,
    help="PPM tolerance (overrides absolute tol).",
)
@click.option(
    "--charge",
    type=int,
    default=0,
    show_default=True,
    help="Net charge for even-electron parity.",
)
@click.option(
    "--dbe/--no-dbe",
    "enforce_dbe",
    default=False,
    show_default=True,
    help="Enforce DBE ≥ 0.",
)
@click.option(
    "--even/--no-even",
    "enforce_even",
    default=False,
    show_default=True,
    help="Enforce even-electron parity.",
)
@click.option(
    "--nrule/--no-nrule",
    "nitrogen_rule",
    default=False,
    show_default=True,
    help="Apply nitrogen rule based on nominal-mass parity.",
)
@click.option(
    "--max",
    "max_candidates",
    type=int,
    default=None,
    help="Stop after this many candidates.",
)
@click.option(
    "--sort",
    "sort_by",
    type=click.Choice(["abs_error", "mass", "formula", "dbe"], case_sensitive=False),
    default="abs_error",
    show_default=True,
)
@click.option(
    "--json/--no-json",
    "as_json",
    default=False,
    show_default=True,
    help="Print JSON array instead of text.",
)
@click.option(
    "--allow-isotopes/--no-allow-isotopes",
    default=False,
    show_default=True,
    help="Expand H-containing hits into isotopologues (H→D/T) post-enumeration.",
)
@click.option(
    "--labels",
    type=str,
    default="D",
    show_default=True,
    help="Isotope labels to consider when --allow-isotopes is on (e.g., 'D' or 'D T').",
)
@click.option(
    "--max-labels",
    type=int,
    default=3,
    show_default=True,
    help="Max number of H atoms replaced across all labels.",
)
def cmd_enumerate(
    mass_da,
    elements_str,
    abs_tol_da,
    ppm,
    charge,
    enforce_dbe,
    enforce_even,
    nitrogen_rule,
    max_candidates,
    sort_by,
    as_json,
    allow_isotopes,
    labels,
    max_labels,
):
    """Enumerate ALL feasible formulas within tolerance (optionally add isotopologues)."""
    elements = _parse_elements(elements_str)
    label_tuple = _parse_labels(labels)

    sols = enumerate_formulas(
        mass_da=mass_da,
        elements=elements,
        abs_tol_da=abs_tol_da,
        ppm_tolerance=ppm,
        charge=charge,
        enforce_dbe=enforce_dbe,
        enforce_even_electron=enforce_even,
        nitrogen_rule=nitrogen_rule,
        max_candidates=max_candidates,
        sort_by=sort_by,
        allow_isotopes=allow_isotopes,
        labels=label_tuple,
        max_labels=max_labels,
    )
    if not sols:
        click.echo("No feasible formulas within tolerance.", err=True)
        sys.exit(2)

    if as_json:
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
        click.echo(json.dumps(payload, indent=2))
    else:
        for i, s in enumerate(sols, 1):
            click.echo(
                f"[{i:>3}] {s.formula:>12}  mass={s.mass_calc:.9f}  "
                f"err={s.abs_error:.9g}  DBE={s.dbe:.3f}"
            )


if __name__ == "__main__":
    cli()
