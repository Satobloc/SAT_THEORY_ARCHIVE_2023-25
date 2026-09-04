from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.collapse import analytic_collapse_state, collapse_result, run_collapse_sweep
from hsh_spheres.contracts import load_equation_packet


class CollapseTests(unittest.TestCase):
    def test_analytic_singular_values_match_base_case(self) -> None:
        state = analytic_collapse_state(1.0, 1.0, near_critical_relative_gap=1e-3)
        self.assertEqual(state.classification, "regular_closed_carrier")
        self.assertAlmostEqual(state.radius, math.sqrt(2.0 / 3.0), places=14)
        expected = sorted((2.0 * math.sqrt(2.0), math.sqrt(2.0), math.sqrt(2.0)), reverse=True)
        np.testing.assert_allclose(state.singular_values, expected, rtol=1e-14, atol=1e-14)

    def test_state_classification_across_event(self) -> None:
        critical = math.sqrt(3.0)
        near = analytic_collapse_state(1.0, critical * (1.0 - 1e-6), near_critical_relative_gap=1e-3)
        at = analytic_collapse_state(1.0, critical, near_critical_relative_gap=1e-3)
        above = analytic_collapse_state(1.0, critical * (1.0 + 1e-6), near_critical_relative_gap=1e-3)
        self.assertEqual(near.classification, "near_critical_closed_carrier")
        self.assertEqual(at.classification, "rank_loss_point")
        self.assertEqual(above.classification, "no_real_carrier")
        self.assertEqual(at.singular_values[-1], 0.0)

    def test_adaptive_trace_reaches_small_carrier(self) -> None:
        sweep = run_collapse_sweep(
            radius=1.0,
            start_separation=1.0,
            trace_step=0.04,
            linear_frame_count=3,
            linear_end_fraction=0.9,
            critical_gap_exponents=[4, 6],
            near_critical_relative_gap=1e-3,
            above_critical_fraction=1e-6,
        )
        near_frames = [frame for frame in sweep.frames if frame.analytic.classification == "near_critical_closed_carrier"]
        self.assertTrue(near_frames)
        self.assertTrue(all(frame.trace is not None for frame in near_frames))
        self.assertTrue(all(frame.trace.minimum_step_used < 0.04 for frame in near_frames if frame.trace is not None))
        self.assertLess(sweep.event_location_error, 1e-12)

    def test_full_collapse_packet(self) -> None:
        packet = load_equation_packet(ROOT / "examples" / "equal_s3_collapse_packet.json")
        result, sweep = collapse_result(packet)
        tolerances = packet["tolerances"]
        self.assertEqual(result["status"], "exact_identity_with_numerical_verification")
        self.assertLess(result["residuals"]["radius_relative_max"], tolerances["radius_relative"])
        self.assertLess(result["residuals"]["circumference_relative_max"], tolerances["circumference_relative"])
        self.assertLess(result["residuals"]["curvature_relative_max"], tolerances["curvature_relative"])
        self.assertLess(result["residuals"]["response_relative_max"], tolerances["response_relative"])
        self.assertLess(result["residuals"]["singular_value_relative_max"], tolerances["singular_value_relative"])
        self.assertLess(result["residuals"]["constraint_max_absolute"], tolerances["constraint_absolute"])
        self.assertLess(sweep.event_location_error, tolerances["event_location_absolute"])
        self.assertEqual(
            set(result["diagnostics"]["classifications_present"]),
            {"regular_closed_carrier", "near_critical_closed_carrier", "rank_loss_point", "no_real_carrier"},
        )
        self.assertIn("conditioning_limit", result["diagnostics"]["numerical_statuses_present"])
        self.assertEqual(result["provenance"]["silent_repairs"], [])


if __name__ == "__main__":
    unittest.main()
