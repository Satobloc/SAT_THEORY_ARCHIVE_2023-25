#!/usr/bin/env python3
"""
H_UNIVERSES_WINDOWS.py

Standalone Windows-friendly generator.

It writes h_manifold_states.txt directly into the CURRENT WORKING DIRECTORY.
There are no hard-coded external paths.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import unicodedata
from dataclasses import dataclass

NBSP = "\u00A0"


@dataclass(frozen=True)
class State:
    key: str
    glyph: str


ROTATION_STATES = {
    "xy": (
        State("none", ""),
        State("cw", "\u036f"),
        State("ccw", "\u036e"),
    ),
    "zw": (
        State("none", ""),
        State("cw", "\u0353"),
        State("ccw", "\u032c"),
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


def axis_states(axis: str, mode: str):
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
    return f"{left or NBSP}[{middle}]{right or NBSP}"


def render_compass(rotations, axes) -> str:
    central = "H" + rotations["xy"].glyph + rotations["zw"].glyph

    plane_left = rotations["xz"].glyph + rotations["yw"].glyph
    plane_right = rotations["xw"].glyph + rotations["yz"].glyph
    rotational_layer = bracket_layer(plane_left, central, plane_right)

    axis_left = axes["x"].glyph + axes["y"].glyph
    axis_right = axes["z"].glyph + axes["w"].glyph
    return nfc(bracket_layer(axis_left, rotational_layer, axis_right))


def describe(rotations, axes) -> str:
    groups = []

    for label, key in (
        ("contraction", "contract"),
        ("expansion", "expand"),
        ("changing contraction", "changing_contract"),
        ("changing expansion", "changing_expand"),
    ):
        members = [
            axis
            for axis in ("x", "y", "z", "w")
            if axes[axis].key == key
        ]
        if members:
            groups.append(f"{label}: {'+'.join(members)}")

    for label, key in (
        ("clockwise rotation", "cw"),
        ("widdershins rotation", "ccw"),
    ):
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
    axes_order = ("x", "y", "z", "w")
    axis_choices = tuple(axis_states(axis, axis_mode) for axis in axes_order)

    index = 0
    for rotation_choice in itertools.product(
        *(ROTATION_STATES[plane] for plane in planes)
    ):
        rotations = dict(zip(planes, rotation_choice))

        for axis_choice in itertools.product(*axis_choices):
            axes = dict(zip(axes_order, axis_choice))
            index += 1
            yield index, render_compass(rotations, axes), describe(rotations, axes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--axis-mode",
        choices=("basic", "variable"),
        default="basic",
    )
    parser.add_argument(
        "--format",
        choices=("txt", "csv"),
        default="txt",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Optional filename only. Saved in the current working directory.",
    )
    args = parser.parse_args()

    if args.output:
        output_name = args.output
    elif args.format == "csv":
        output_name = "h_manifold_states.csv"
    else:
        output_name = "h_manifold_states.txt"

    rows = iter_states(args.axis_mode)

    if args.format == "csv":
        with open(output_name, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(("index", "compass", "description"))
            count = 0
            for index, compass, description in rows:
                writer.writerow((index, compass, description))
                count = index
    else:
        with open(output_name, "w", encoding="utf-8", newline="\n") as handle:
            count = 0
            for index, compass, description in rows:
                handle.write(f"{index:>6}\t{compass}\t{description}\n")
                count = index

    print(f"Wrote {count:,} states to {output_name}")


if __name__ == "__main__":
    main()
