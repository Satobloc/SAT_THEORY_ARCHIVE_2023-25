from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.geometry import analytic_equal_s3_carrier, equal_s3_system, trace_closed_carrier


class GeometryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.radius = 1.0
        self.separation = 1.0
        self.rho, self.circumference = analytic_equal_s3_carrier(self.radius, self.separation)
        self.system = equal_s3_system(self.radius, self.separation)
        self.start = np.array([0.0, 0.0, self.rho, 0.0])

    def test_analytic_carrier(self) -> None:
        self.assertAlmostEqual(self.rho, math.sqrt(2.0 / 3.0), places=14)
        self.assertLess(np.max(np.abs(self.system.values(self.start))), 1e-12)
        self.assertEqual(self.system.rank(self.start), 3)

    def test_tangent_is_in_jacobian_nullspace(self) -> None:
        tangent = self.system.tangent(self.start)
        self.assertAlmostEqual(float(np.linalg.norm(tangent)), 1.0, places=12)
        self.assertLess(float(np.linalg.norm(self.system.jacobian(self.start) @ tangent)), 1e-12)

    def test_numeric_closed_trace(self) -> None:
        trace = trace_closed_carrier(self.system, self.start, step_size=0.03)
        self.assertLess(trace.max_constraint_residual, 1e-10)
        self.assertLess(abs(trace.circumference - self.circumference) / self.circumference, 0.003)
        radii = np.linalg.norm(trace.points[:-1, 2:4], axis=1)
        self.assertLess(float(np.max(np.abs(radii - self.rho))), 1e-9)

    def test_velocity_decomposition(self) -> None:
        radius_rate = 0.1
        internal_speed = 0.25
        rates = [{"radius_rate": radius_rate} for _ in self.system.shells]
        velocity = self.system.velocity_decomposition(self.start, rates, internal_speed=internal_speed)
        expected_forced_speed = self.radius * radius_rate / self.rho
        self.assertAlmostEqual(float(velocity.surface_forced[2]), expected_forced_speed, places=11)
        self.assertAlmostEqual(float(np.linalg.norm(velocity.internal_tangent)), internal_speed, places=12)
        self.assertLess(float(np.linalg.norm(self.system.jacobian(self.start) @ velocity.internal_tangent)), 1e-12)
        self.assertLess(
            float(np.linalg.norm(self.system.jacobian(self.start) @ velocity.surface_forced + velocity.parameter_derivatives)),
            1e-11,
        )

    def test_translation_and_rotation_invariance(self) -> None:
        rng = np.random.default_rng(42)
        q, _ = np.linalg.qr(rng.normal(size=(4, 4)))
        translation = np.array([0.4, -1.2, 0.7, 2.0])
        transformed_system = self.system.transformed(q, translation)
        transformed_start = q @ self.start + translation
        self.assertLess(np.max(np.abs(transformed_system.values(transformed_start))), 1e-11)
        self.assertEqual(transformed_system.rank(transformed_start), 3)
        tangent = transformed_system.tangent(transformed_start)
        self.assertLess(float(np.linalg.norm(transformed_system.jacobian(transformed_start) @ tangent)), 1e-11)

    def test_bifurcation_indicator_tends_to_zero(self) -> None:
        regular_smallest = self.system.singular_values(self.start)[-1]
        near_d = math.sqrt(3.0) * self.radius * (1.0 - 1e-8)
        near_rho, _ = analytic_equal_s3_carrier(self.radius, near_d)
        near_system = equal_s3_system(self.radius, near_d)
        near_start = np.array([0.0, 0.0, near_rho, 0.0])
        near_smallest = near_system.singular_values(near_start)[-1]
        self.assertLess(near_smallest / regular_smallest, 0.001)


if __name__ == "__main__":
    unittest.main()
