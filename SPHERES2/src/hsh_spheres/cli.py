"""Command-line runner for one equation packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import load_equation_packet
from .runner import run_packet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an H(s)H spherical-constraint equation round trip")
    parser.add_argument("packet", type=Path, help="Path to an equation packet JSON file")
    parser.add_argument("--output", type=Path, required=True, help="Path for the mapping result JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    packet = load_equation_packet(args.packet)
    result, _ = run_packet(packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"mapping: {result['mapping_id']}")
    print(f"status: {result['status']}")
    print(f"radius residual: {result['residuals']['carrier_radius_relative']:.3e}")
    print(f"circumference residual: {result['residuals']['carrier_circumference_relative']:.3e}")
    print(f"constraint residual: {result['residuals']['constraint_max_absolute']:.3e}")


if __name__ == "__main__":
    main()
