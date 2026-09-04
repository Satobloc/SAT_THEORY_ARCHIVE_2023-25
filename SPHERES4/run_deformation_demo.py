"""Run the v0.2 one-shell deformation cycle and export its data products."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.contracts import load_equation_packet  # noqa: E402
from hsh_spheres.deformation import concatenate_cycle_points, deformation_result  # noqa: E402


def main() -> None:
    packet = load_equation_packet(ROOT / "examples" / "one_shell_deformation_packet.json")
    result, cycle = deformation_result(packet)
    output_dir = ROOT / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    result_path = output_dir / "one_shell_deformation_result.json"
    history_path = output_dir / "one_shell_deformation_history.csv"
    curves_path = output_dir / "one_shell_deformation_curves.npz"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    rows = result["observables"]["frame_history"]
    with history_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    points, offsets = concatenate_cycle_points(cycle.frames)
    np.savez_compressed(
        curves_path,
        points=points,
        offsets=offsets,
        phases=np.array([frame.phase for frame in cycle.frames]),
        epsilons=np.array([frame.epsilon for frame in cycle.frames]),
    )

    print(f"mapping: {result['mapping_id']}")
    print(f"status: {result['status']}")
    print(f"frames: {len(cycle.frames)}")
    print(f"circumference range: {result['observables']['circumference_min']:.12f} .. {result['observables']['circumference_max']:.12f}")
    print(f"mean-curvature range: {result['observables']['curvature_mean_min']:.12f} .. {result['observables']['curvature_mean_max']:.12f}")
    print(f"minimum rank margin: {result['observables']['minimum_jacobian_singular_value']:.6e}")
    print(f"bifurcation detected: {result['observables']['bifurcation_detected']}")
    print(f"constraint residual: {result['residuals']['constraint_max_absolute']:.3e}")
    print(f"continuation return error: {result['residuals']['continuation_seed_return_error']:.3e}")
    print(f"result: {result_path}")
    print(f"history: {history_path}")
    print(f"curves: {curves_path}")


if __name__ == "__main__":
    main()
