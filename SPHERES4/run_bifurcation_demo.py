"""Run the v0.3 exact carrier-collapse event benchmark."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.collapse import collapse_result, concatenate_collapse_points  # noqa: E402
from hsh_spheres.contracts import load_equation_packet  # noqa: E402


def _csv_value(value: object) -> object:
    if isinstance(value, list):
        return json.dumps(value)
    return value


def main() -> None:
    packet = load_equation_packet(ROOT / "examples" / "equal_s3_collapse_packet.json")
    result, sweep = collapse_result(packet)
    output_dir = ROOT / "build"
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "equal_s3_collapse_result.json"
    history_path = output_dir / "equal_s3_collapse_history.csv"
    curves_path = output_dir / "equal_s3_collapse_curves.npz"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    rows = result["observables"]["history"]
    with history_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows([{key: _csv_value(value) for key, value in row.items()} for row in rows])

    points, offsets, separations = concatenate_collapse_points(sweep.frames)
    np.savez_compressed(curves_path, points=points, offsets=offsets, separations=separations)

    print(f"mapping: {result['mapping_id']}")
    print(f"status: {result['status']}")
    print(f"frames: {len(sweep.frames)}")
    print(f"critical separation exact: {sweep.critical_separation_exact:.15f}")
    print(f"critical separation numeric: {sweep.critical_separation_numeric:.15f}")
    print(f"event location error: {sweep.event_location_error:.3e}")
    print(f"radius residual max: {result['residuals']['radius_relative_max']:.3e}")
    print(f"curvature residual max: {result['residuals']['curvature_relative_max']:.3e}")
    print(f"constraint residual max: {result['residuals']['constraint_max_absolute']:.3e}")
    print(f"classifications: {', '.join(result['diagnostics']['classifications_present'])}")
    print(f"result: {result_path}")
    print(f"history: {history_path}")
    print(f"curves: {curves_path}")


if __name__ == "__main__":
    main()
