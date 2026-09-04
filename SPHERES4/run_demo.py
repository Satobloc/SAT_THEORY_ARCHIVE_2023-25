"""Run the included exact geometry round trip without installing the package."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.contracts import load_equation_packet  # noqa: E402
from hsh_spheres.roundtrip import run_roundtrip  # noqa: E402


def main() -> None:
    packet = load_equation_packet(ROOT / "examples" / "equal_s3_packet.json")
    result = run_roundtrip(packet)
    output = ROOT / "build" / "equal_s3_mapping_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"mapping: {result['mapping_id']}")
    print(f"status: {result['status']}")
    print(f"analytic radius: {result['observables']['carrier_radius_exact']:.12f}")
    print(f"numeric radius: {result['observables']['carrier_radius_numeric']:.12f}")
    print(f"circumference residual: {result['residuals']['carrier_circumference_relative']:.3e}")
    print(f"constraint residual: {result['residuals']['constraint_max_absolute']:.3e}")
    print(f"result: {output}")


if __name__ == "__main__":
    main()
