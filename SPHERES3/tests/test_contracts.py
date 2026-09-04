from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsh_spheres.contracts import ContractError, load_equation_packet, validate_equation_packet


class ContractTests(unittest.TestCase):
    def test_example_packet_is_valid(self) -> None:
        packet = load_equation_packet(ROOT / "examples" / "equal_s3_packet.json")
        self.assertEqual(packet["equation_id"], "STD-GEO-S3X3-R4-0001")

    def test_missing_authority_fails(self) -> None:
        packet = json.loads((ROOT / "examples" / "equal_s3_packet.json").read_text(encoding="utf-8"))
        del packet["authority"]
        with self.assertRaises(ContractError):
            validate_equation_packet(packet)


if __name__ == "__main__":
    unittest.main()
