"""Backward-compatible operation dispatch for spherical equation packets."""

from __future__ import annotations

from typing import Any

from .deformation import deformation_result
from .roundtrip import run_roundtrip


def run_packet(packet: dict[str, Any]) -> tuple[dict[str, Any], object | None]:
    operation = packet.get("mapping_request", {}).get("operation", "equal_s3_static")
    if operation == "equal_s3_static":
        return run_roundtrip(packet), None
    if operation == "one_shell_shape_oscillation":
        return deformation_result(packet)
    raise ValueError(f"Unsupported spherical_constraint operation: {operation}")
