from pathlib import Path
import subprocess, sys, textwrap

script = r'''#!/usr/bin/env python3
"""
H_UNIVERSES.py

Generate every H-manifold combination using the dimensional compass.

Default basic mode:
- 6 rotational planes, each: none / clockwise / widdershins
- 4 axes, each: none / expansion / contraction
- total: 3^6 * 3^4 = 59,049 states

Optional variable mode:
- adds changing expansion and changing contraction on each axis
- total: 3^6 * 5^4 = 455,625 states

Output:
- saved beside this script by default
- NFC-normalized Unicode
- empty bracket-side layers contain one nonbreaking space (U+00A0)
- descriptions consolidate like-action properties
"""

from __future__ import annotations

import argparse
import csv
import itertools
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

NBSP = "\u00A0"


@dataclass(frozen=True)
class State:
    key: str
    glyph: str


ROTATION_STATES = {
    "xy": (
        State("none", ""),
        State("cw", "\u036f"),    # Hͯ
        State("ccw", "\u036e"),   # Hͮ
    ),
    "zw": (
        State("none", ""),
        State("cw", "\u0353"),    # H͓
        State("ccw", "\u032c"),   # H̬
    ),
    "xz": (
        State("none", ""),
        State("cw", "ˣ"),
        State("ccw", "ᵛ"),
    ),
    "yw": (
        State("none", ""),
        State("cw", "ₓ"),
        State("ccw", "ᵥ"),
    ),
    "xw": (
        State("none", ""),
        State("cw", "ˣ"),
        State("ccw", "ᵛ"),
    ),
    "yz": (
        State("none", ""),
        State("cw", "ₓ"),
        State("ccw", "ᵥ"),
    ),
}


def axis_states(axis: str, mode: str) -> tuple[State, ...]:
    is_subscript = axis in {"y", "w"}
    plus = "₊" if is_subscript else "⁺"
    minus = "₋" if is_subscript else "⁻"

    states = [
        State("none", ""),
        State("expand", plus),
        State("contract", minus),
    ]

    if mode == "variable":
        states.extend(
            [
                State("changing_expand", "ᵟ" + plus),
                State("changing_contract", "ᵟ" + minus),
            ]
        )

    return tuple(states)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def bracket_layer(left: str, middle: str, right: str) -> str:
    """
    Preserve the bracket layer.

    If a left or right side has no active property, use exactly one NBSP.
    """
    return f"{left or NBSP}[{middle}]{right or NBSP}"


def render_compass(
    rotations: dict[str, State],
    axes: dict[str, State],
) -> str:
    """
    Render:
        outer axis layer [
            inner plane layer [
                central H with planes 1 and 2
            ]
        ]
    """
    # Plane 1 = xy above H; plane 2 = zw below H.
    central = "H" + rotations["xy"].glyph + rotations["zw"].glyph

    # Plane slots 3/4 to the left; 5/6 to the right.
    plane_left = rotations["xz"].glyph + rotations["yw"].glyph
    plane_right = rotations["xw"].glyph + rotations["yz"].glyph
    rotational_layer = bracket_layer(plane_left, central, plane_right)

    # Axis slots x/y to the left; z/w to the right.
    axis_left = axes["x"].glyph + axes["y"].glyph
    axis_right = axes["z"].glyph + axes["w"].glyph
    full_compass = bracket_layer(axis_left, rotational_layer, axis_right)

    return nfc(full_compass)


def describe(
    rotations: dict[str, State],
    axes: dict[str, State],
) -> str:
    """
    Consolidate like-action properties.

    Example:
        contraction: x+y | expansion: z | clockwise rotation: yw+zw
    """
    groups: list[str] = []

    axis_groups = (
        ("contraction", "contract"),
        ("expansion", "expand"),
        ("changing contraction", "changing_contract"),
        ("changing expansion", "changing_expand"),
    )
    for label, key in axis_groups:
        members = [
            axis
            for axis in ("x", "y", "z", "w")
            if axes[axis].key == key
        ]
        if members:
            groups.append(f"{label}: {'+'.join(members)}")

    rotation_groups = (
        ("clockwise rotation", "cw"),
        ("widdershins rotation", "ccw"),
    )
    for label, key in rotation_groups:
        members = [
            plane
            for plane in ("xy", "zw", "xz", "yw", "xw", "yz")
            if rotations[plane].key == key
        ]
        if members:
            groups.append(f"{label}: {'+'.join(members)}")

    return " | ".join(groups) if groups else "baseline H; no active dynamics"


def iter_states(axis_mode: str):
    planes = ("xy", "zw", "xz", "yw", "xw", "yz")
    axis_order = ("x", "y", "z", "w")
    axis_choices = tuple(axis_states(axis, axis_mode) for axis in axis_order)

    index = 0
    for rotation_choice in itertools.product(
        *(ROTATION_STATES[plane] for plane in planes)
    ):
        rotations = dict(zip(planes, rotation_choice))

        for axis_choice in itertools.product(*axis_choices):
            axes = dict(zip(axis_order, axis_choice))
            index += 1
            yield index, render_compass(rotations, axes), describe(rotations, axes)


def write_txt(
    path: Path,
    rows: Iterable[tuple[int, str, str]],
) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for index, compass, description in rows:
            handle.write(f"{index:>6}\t{compass}\t{description}\n")
            count = index
    return count


def write_csv(
    path: Path,
    rows: Iterable[tuple[int, str, str]],
) -> int:
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("index", "compass", "description"))
        for index, compass, description in rows:
            writer.writerow((index, compass, description))
            count = index
    return count


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Generate every H-manifold rotation and axis-dynamics state."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=script_dir / "h_manifold_states.txt",
        help="Output path. Default: h_manifold_states.txt beside this script.",
    )
    parser.add_argument(
        "--format",
        choices=("txt", "csv"),
        default="txt",
        help="Output format. Default: txt",
    )
    parser.add_argument(
        "--axis-mode",
        choices=("basic", "variable"),
        default="basic",
        help=(
            "basic = none/expansion/contraction (59,049 states); "
            "variable adds changing expansion/contraction (455,625 states)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent

    # Any relative custom output path is also resolved beside the script.
    if not args.output.is_absolute():
        args.output = script_dir / args.output

    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows = iter_states(args.axis_mode)
    if args.format == "csv":
        count = write_csv(args.output, rows)
    else:
        count = write_txt(args.output, rows)

    print(f"Wrote {count:,} states to:")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
'''

path = Path("/mnt/data/H_UNIVERSES.py")
path.write_text(script, encoding="utf-8")

# Verify syntax and run it in an isolated temp folder beside itself.
subprocess.run(
    [sys.executable, str(path), "-o", "H_UNIVERSES_test.txt"],
    check=True,
    capture_output=True,
    text=True,
)

test_output = Path("/mnt/data/H_UNIVERSES_test.txt")
line_count = sum(1 for _ in test_output.open("r", encoding="utf-8"))
first_lines = "".join(test_output.open("r", encoding="utf-8").readlines()[:5])

print(f"Script: {path}")
print(f"Validated output lines: {line_count}")
print(first_lines)
