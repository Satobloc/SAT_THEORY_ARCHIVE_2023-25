from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.contracts import load_equation_packet
from hsh_spheres.deformation import (
    deformation_result,
    discrete_curve_metrics,
    one_shell_deformed_system,
    oscillating_shape,
    trace_deformation_cycle,
)
from hsh_spheres.geometry import analytic_equal_s3_carrier, trace_closed_carrier


class DeformationTests(unittest.TestCase):
    def test_shape_is_positive_and_volume_preserving(self) -> None:
        for phase in np.linspace(0.0, 2.0 * math.pi, 13):
            shape, _, _ = oscillating_shape(float(phase), 0.35)
            self.assertGreater(float(np.min(np.linalg.eigvalsh(shape))), 0.0)
            self.assertAlmostEqual(float(np.linalg.det(shape)), 1.0, places=12)

    def test_shape_rate_matches_finite_difference(self) -> None:
        phase = 0.73
        h = 1e-7
        shape_plus, _, _ = oscillating_shape(phase + h, 0.35)
        shape_minus, _, _ = oscillating_shape(phase - h, 0.35)
        _, analytic_rate, _ = oscillating_shape(phase, 0.35)
        numeric_rate = (shape_plus - shape_minus) / (2.0 * h)
        self.assertLess(float(np.max(np.abs(numeric_rate - analytic_rate))), 1e-8)

    def test_zero_phase_recovers_equal_s3_circle(self) -> None:
        rho, circumference = analytic_equal_s3_carrier(1.0, 1.0)
        system, _, epsilon = one_shell_deformed_system(1.0, 1.0, 0.0, 0.35)
        start = np.array([0.0, 0.0, rho, 0.0])
        trace = trace_closed_carrier(system, start, step_size=0.03)
        metrics = discrete_curve_metrics(trace.points)
        self.assertAlmostEqual(epsilon, 0.0, places=14)
        self.assertLess(abs(metrics.circumference - circumference) / circumference, 0.003)
        self.assertLess(abs(metrics.curvature_mean - 1.0 / rho), 0.002)

    def test_moving_constraint_velocity(self) -> None:
        rho, _ = analytic_equal_s3_carrier(1.0, 1.0)
        system, rates, _ = one_shell_deformed_system(1.0, 1.0, 0.4, 0.35)
        base_seed = np.array([0.0, 0.0, rho, 0.0])
        seed = system.correct_to_carrier(base_seed, np.array([0.0, 0.0, 0.0, 1.0]))
        velocity = system.velocity_decomposition(seed, rates, internal_speed=0.25)
        residual = np.linalg.norm(system.jacobian(seed) @ velocity.surface_forced + velocity.parameter_derivatives)
        self.assertLess(float(residual), 1e-10)

    def test_short_cycle_closes_and_remains_regular(self) -> None:
        cycle = trace_deformation_cycle(
            radius=1.0,
            separation=1.0,
            amplitude=0.25,
            frame_count=9,
            trace_step=0.045,
            internal_speed=0.1,
            bifurcation_tolerance=1e-5,
        )
        self.assertLess(cycle.seed_cycle_error, 1e-8)
        self.assertLess(cycle.maximum_constraint_residual, 1e-9)
        self.assertGreater(cycle.minimum_jacobian_singular_value, 1e-5)
        self.assertFalse(any(frame.bifurcation_flag for frame in cycle.frames))
        self.assertAlmostEqual(cycle.frames[0].metrics.circumference, cycle.frames[-1].metrics.circumference, places=9)

    def test_full_deformation_packet(self) -> None:
        packet = load_equation_packet(ROOT / "examples" / "one_shell_deformation_packet.json")
        result, cycle = deformation_result(packet)
        tolerances = packet["tolerances"]
        self.assertEqual(result["status"], "coordinate_rewrite")
        self.assertEqual(len(cycle.frames), packet["mapping_request"]["parameters"]["frame_count"])
        self.assertLess(result["residuals"]["constraint_max_absolute"], tolerances["constraint_absolute"])
        self.assertLess(result["residuals"]["seed_cycle_closure_absolute"], tolerances["cycle_closure_absolute"])
        self.assertLess(result["residuals"]["moving_constraint_max_absolute"], tolerances["moving_constraint_absolute"])
        self.assertLess(result["residuals"]["shape_determinant_max_absolute"], tolerances["shape_determinant_absolute"])
        self.assertFalse(result["observables"]["bifurcation_detected"])
        self.assertEqual(result["provenance"]["silent_repairs"], [])


if __name__ == "__main__":
    unittest.main()
