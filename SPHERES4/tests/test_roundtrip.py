from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.contracts import load_equation_packet, validate_mapping_result
from hsh_spheres.roundtrip import run_roundtrip


class RoundTripTests(unittest.TestCase):
    def test_full_round_trip(self) -> None:
        packet = load_equation_packet(ROOT / "examples" / "equal_s3_packet.json")
        result = validate_mapping_result(run_roundtrip(packet))
        tolerances = packet["tolerances"]
        self.assertEqual(result["status"], "exact_identity_with_numerical_verification")
        self.assertLess(result["residuals"]["constraint_max_absolute"], tolerances["constraint_absolute"])
        self.assertLess(result["residuals"]["carrier_radius_relative"], tolerances["radius_relative"])
        self.assertLess(result["residuals"]["carrier_circumference_relative"], tolerances["circumference_relative"])
        self.assertLess(result["residuals"]["surface_forced_speed_relative"], tolerances["velocity_relative"])
        self.assertEqual(result["provenance"]["silent_repairs"], [])


if __name__ == "__main__":
    unittest.main()
