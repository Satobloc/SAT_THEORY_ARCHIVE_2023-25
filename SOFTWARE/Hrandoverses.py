#!/usr/bin/env python3
"""
ROLL_RANDOM_H_UNIVERSES.py

Generate a readable sample of random single-H and paired-HH universes.

Each active dynamic receives a normalized rate:
- axis expansion/contraction rates use h*
- rotational rates use omega*
- coupling strengths g are dimensionless

The script writes RANDOM_H_UNIVERSES.txt into the CURRENT WORKING DIRECTORY
unless another filename is supplied with -o.

Examples:
    python ROLL_RANDOM_H_UNIVERSES.py
    python ROLL_RANDOM_H_UNIVERSES.py -n 50 --seed 20260708
    python ROLL_RANDOM_H_UNIVERSES.py -n 100 --hh-probability 0.70
"""

from __future__ import annotations

import argparse
import random
import unicodedata
from dataclasses import dataclass
from typing import Iterable

NBSP = "\u00A0"

AXES = ("x", "y", "z", "w")
PLANES = ("xy", "zw", "xz", "yw", "xw", "yz")

ROTATION_GLYPHS = {
    "xy": {"cw": "\u036f", "ccw": "\u036e"},
    "zw": {"cw": "\u0353", "ccw": "\u032c"},
    "xz": {"cw": "ˣ", "ccw": "ᵛ"},
    "yw": {"cw": "ₓ", "ccw": "ᵥ"},
    "xw": {"cw": "ˣ", "ccw": "ᵛ"},
    "yz": {"cw": "ₓ", "ccw": "ᵥ"},
}


@dataclass(frozen=True)
class Dynamic:
    shell: str
    kind: str          # "axis" or "rotation"
    target: str        # x/y/z/w or xy/zw/...
    state: str         # expand/contract/cw/ccw
    rate: float        # signed normalized rate

    @property
    def short_id(self) -> str:
        prefix = f"{self.shell}." if self.shell else ""
        return f"{prefix}{self.target}:{self.state}"

    @property
    def compact_rate(self) -> str:
        unit = "h*" if self.kind == "axis" else "ω*"
        return f"{self.rate:+.3f}{unit}"


@dataclass(frozen=True)
class Coupling:
    members: tuple[Dynamic, ...]
    strength: float

    def render(self, index: int) -> str:
        member_text = " ↔ ".join(member.short_id for member in self.members)
        return f"C{index}{{{member_text}}}[g={self.strength:+.3f}]"


@dataclass
class HState:
    shell: str
    axes: dict[str, str]       # none/expand/contract
    planes: dict[str, str]     # none/cw/ccw
    dynamics: list[Dynamic]


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def bracket_layer(left: str, middle: str, right: str) -> str:
    return f"[{left}{middle}{right}]"


def render_compass(state: HState) -> str:
    axis_glyph = {
        "x": {"none": NBSP, "expand": "⁺", "contract": "⁻"},
        "y": {"none": NBSP, "expand": "₊", "contract": "₋"},
        "z": {"none": NBSP, "expand": "⁺", "contract": "⁻"},
        "w": {"none": NBSP, "expand": "₊", "contract": "₋"},
    }

    def plane_glyph(plane: str) -> str:
        state_name = state.planes[plane]
        return NBSP if state_name == "none" else ROTATION_GLYPHS[plane][state_name]

    central = "H"
    if state.planes["xy"] != "none":
        central += ROTATION_GLYPHS["xy"][state.planes["xy"]]
    if state.planes["zw"] != "none":
        central += ROTATION_GLYPHS["zw"][state.planes["zw"]]

    central_layer = f"[{central}]"

    plane_left = plane_glyph("xz") + plane_glyph("yw")
    plane_right = plane_glyph("xw") + plane_glyph("yz")
    rotational_layer = bracket_layer(plane_left, central_layer, plane_right)

    axis_left = axis_glyph["x"][state.axes["x"]] + axis_glyph["y"][state.axes["y"]]
    axis_right = axis_glyph["z"][state.axes["z"]] + axis_glyph["w"][state.axes["w"]]
    return nfc(bracket_layer(axis_left, rotational_layer, axis_right))


def random_magnitude(rng: random.Random, minimum: float, maximum: float) -> float:
    return rng.uniform(minimum, maximum)


def make_random_h(
    rng: random.Random,
    shell: str,
    axis_active_probability: float,
    rotation_active_probability: float,
    axis_rate_min: float,
    axis_rate_max: float,
    rotation_rate_min: float,
    rotation_rate_max: float,
) -> HState:
    axes: dict[str, str] = {}
    planes: dict[str, str] = {}
    dynamics: list[Dynamic] = []

    for axis in AXES:
        if rng.random() < axis_active_probability:
            state = rng.choice(("expand", "contract"))
            magnitude = random_magnitude(rng, axis_rate_min, axis_rate_max)
            signed_rate = magnitude if state == "expand" else -magnitude
            dynamics.append(Dynamic(shell, "axis", axis, state, signed_rate))
            axes[axis] = state
        else:
            axes[axis] = "none"

    for plane in PLANES:
        if rng.random() < rotation_active_probability:
            state = rng.choice(("cw", "ccw"))
            magnitude = random_magnitude(rng, rotation_rate_min, rotation_rate_max)
            # Clockwise positive, widdershins negative by script convention.
            signed_rate = magnitude if state == "cw" else -magnitude
            dynamics.append(Dynamic(shell, "rotation", plane, state, signed_rate))
            planes[plane] = state
        else:
            planes[plane] = "none"

    # Avoid an entirely inert shell.
    if not dynamics:
        axis = rng.choice(AXES)
        state = rng.choice(("expand", "contract"))
        magnitude = random_magnitude(rng, axis_rate_min, axis_rate_max)
        signed_rate = magnitude if state == "expand" else -magnitude
        axes[axis] = state
        dynamics.append(Dynamic(shell, "axis", axis, state, signed_rate))

    return HState(shell=shell, axes=axes, planes=planes, dynamics=dynamics)


def grouped_description(state: HState) -> str:
    groups: list[str] = []

    specifications = (
        ("contraction", "axis", "contract", AXES),
        ("expansion", "axis", "expand", AXES),
        ("clockwise rotation", "rotation", "cw", PLANES),
        ("widdershins rotation", "rotation", "ccw", PLANES),
    )

    for label, kind, state_name, order in specifications:
        by_target = {
            dynamic.target: dynamic
            for dynamic in state.dynamics
            if dynamic.kind == kind and dynamic.state == state_name
        }
        members = [
            f"{target}@{by_target[target].compact_rate}"
            for target in order
            if target in by_target
        ]
        if members:
            groups.append(f"{label}: {' + '.join(members)}")

    return " | ".join(groups)


def choose_coupling_members(
    rng: random.Random,
    dynamics: list[Dynamic],
    group_size: int,
    prefer_cross_shell: bool,
) -> tuple[Dynamic, ...]:
    if prefer_cross_shell:
        by_shell: dict[str, list[Dynamic]] = {}
        for dynamic in dynamics:
            by_shell.setdefault(dynamic.shell, []).append(dynamic)

        populated_shells = [shell for shell, items in by_shell.items() if items]
        if len(populated_shells) >= 2:
            first_shell, second_shell = rng.sample(populated_shells, 2)
            chosen = [
                rng.choice(by_shell[first_shell]),
                rng.choice(by_shell[second_shell]),
            ]
            remaining = [dynamic for dynamic in dynamics if dynamic not in chosen]
            if group_size > 2:
                chosen.extend(rng.sample(remaining, min(group_size - 2, len(remaining))))
            return tuple(chosen)

    return tuple(rng.sample(dynamics, group_size))


def make_couplings(
    rng: random.Random,
    dynamics: list[Dynamic],
    is_hh: bool,
    max_couplings: int,
    max_group_size: int,
) -> list[Coupling]:
    if len(dynamics) < 2 or max_couplings < 1:
        return []

    upper = min(max_couplings, max(1, len(dynamics) // 2))
    coupling_count = rng.randint(1, upper)
    couplings: list[Coupling] = []
    seen: set[tuple[str, ...]] = set()

    attempts = 0
    while len(couplings) < coupling_count and attempts < coupling_count * 20:
        attempts += 1
        group_size = rng.randint(2, min(max_group_size, len(dynamics)))
        members = choose_coupling_members(
            rng,
            dynamics,
            group_size,
            prefer_cross_shell=is_hh and len(couplings) == 0,
        )
        signature = tuple(sorted(member.short_id for member in members))
        if signature in seen:
            continue

        seen.add(signature)
        strength = rng.uniform(-1.0, 1.0)
        couplings.append(Coupling(members=members, strength=strength))

    return couplings


def render_universe(
    index: int,
    universe_type: str,
    states: list[HState],
    couplings: list[Coupling],
) -> str:
    lines = [f"{index:09d}\t{universe_type}"]

    for state in states:
        label = state.shell if state.shell else "H"
        lines.append(
            f"\t{label}: {render_compass(state)}\t\t\t{grouped_description(state)}"
        )

    if universe_type == "HH":
        lines.append("\tpairing: A ↔ B")

    coupling_text = (
        "; ".join(coupling.render(i) for i, coupling in enumerate(couplings, 1))
        if couplings
        else "none"
    )
    lines.append(f"\tcouplings: {coupling_text}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Roll random H and HH universes with rates and couplings."
    )
    parser.add_argument("-n", "--count", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--hh-probability", type=float, default=0.50)
    parser.add_argument("--axis-active-probability", type=float, default=0.65)
    parser.add_argument("--rotation-active-probability", type=float, default=0.60)
    parser.add_argument("--axis-rate-min", type=float, default=0.05)
    parser.add_argument("--axis-rate-max", type=float, default=2.00)
    parser.add_argument("--rotation-rate-min", type=float, default=0.05)
    parser.add_argument("--rotation-rate-max", type=float, default=2.00)
    parser.add_argument("--max-couplings", type=int, default=4)
    parser.add_argument("--max-coupling-size", type=int, default=4)
    parser.add_argument("-o", "--output", default="RANDOM_H_UNIVERSES.txt")
    return parser.parse_args()


def validate_probability(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise SystemExit(f"{name} must be between 0 and 1.")


def main() -> None:
    args = parse_args()

    if args.count < 1:
        raise SystemExit("--count must be at least 1.")
    validate_probability("--hh-probability", args.hh_probability)
    validate_probability("--axis-active-probability", args.axis_active_probability)
    validate_probability("--rotation-active-probability", args.rotation_active_probability)
    if args.axis_rate_min <= 0 or args.axis_rate_max < args.axis_rate_min:
        raise SystemExit("Axis rate range is invalid.")
    if args.rotation_rate_min <= 0 or args.rotation_rate_max < args.rotation_rate_min:
        raise SystemExit("Rotation rate range is invalid.")
    if args.max_coupling_size < 2:
        raise SystemExit("--max-coupling-size must be at least 2.")

    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**63)
    rng = random.Random(seed)

    records: list[str] = []
    for index in range(1, args.count + 1):
        is_hh = rng.random() < args.hh_probability
        if is_hh:
            states = [
                make_random_h(
                    rng, "A",
                    args.axis_active_probability,
                    args.rotation_active_probability,
                    args.axis_rate_min,
                    args.axis_rate_max,
                    args.rotation_rate_min,
                    args.rotation_rate_max,
                ),
                make_random_h(
                    rng, "B",
                    args.axis_active_probability,
                    args.rotation_active_probability,
                    args.axis_rate_min,
                    args.axis_rate_max,
                    args.rotation_rate_min,
                    args.rotation_rate_max,
                ),
            ]
            universe_type = "HH"
        else:
            states = [
                make_random_h(
                    rng, "",
                    args.axis_active_probability,
                    args.rotation_active_probability,
                    args.axis_rate_min,
                    args.axis_rate_max,
                    args.rotation_rate_min,
                    args.rotation_rate_max,
                )
            ]
            universe_type = "H"

        all_dynamics = [dynamic for state in states for dynamic in state.dynamics]
        couplings = make_couplings(
            rng,
            all_dynamics,
            is_hh=is_hh,
            max_couplings=args.max_couplings,
            max_group_size=args.max_coupling_size,
        )
        records.append(render_universe(index, universe_type, states, couplings))

    header = (
        "RANDOM H / HH UNIVERSES\n"
        f"seed: {seed}\n"
        f"count: {args.count}\n"
        "axis rates: signed normalized h*\n"
        "rotation rates: cw positive, widdershins negative, normalized ω*\n"
        "coupling strengths: dimensionless g in [-1, +1]\n"
        "\n"
    )

    with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(header)
        handle.write("\n\n".join(records))
        handle.write("\n")

    print(f"Wrote {args.count} random universes to {args.output}")
    print(f"seed: {seed}")


if __name__ == "__main__":
    main()
