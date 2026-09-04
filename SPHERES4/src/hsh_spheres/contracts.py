"""Small dependency-free runtime validation for backend contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when an equation packet violates the backend contract."""


REQUIRED_PACKET_FIELDS = {
    "schema_version",
    "equation_id",
    "title",
    "authority",
    "equations",
    "variables",
    "domain",
    "assumptions",
    "symmetries",
    "constraints",
    "known_solution",
    "mapping_request",
    "tolerances",
}

MAPPING_STATUSES = {
    "exact_identity",
    "exact_identity_with_numerical_verification",
    "coordinate_rewrite",
    "controlled_approximation",
    "calibrated_representation",
    "candidate_extension",
    "failed_mapping",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def validate_equation_packet(packet: dict[str, Any]) -> dict[str, Any]:
    """Validate the subset of the JSON contract required by v0.1."""

    missing = REQUIRED_PACKET_FIELDS.difference(packet)
    _require(not missing, f"Equation packet is missing fields: {sorted(missing)}")
    _require(packet["schema_version"] == "0.1.0", "Unsupported schema_version")
    _require(bool(packet["equation_id"]), "equation_id must be non-empty")
    _require(
        packet["authority"].get("status") == "authoritative_standard_input",
        "authority.status must be authoritative_standard_input",
    )
    _require(bool(packet["authority"].get("source")), "authority.source is required")
    _require(isinstance(packet["equations"], list) and packet["equations"], "equations must be non-empty")
    _require(isinstance(packet["variables"], list), "variables must be a list")

    for variable in packet["variables"]:
        for key in ("symbol", "role", "unit", "dimensions"):
            _require(key in variable, f"Variable is missing {key}: {variable}")
        dims = variable["dimensions"]
        _require(all(k in dims for k in ("M", "L", "T")), f"Variable dimensions need M, L, T: {variable}")

    request = packet["mapping_request"]
    _require(request.get("backend") == "spherical_constraint", "Unsupported mapping backend")
    _require(isinstance(request.get("parameters"), dict), "mapping_request.parameters must be an object")
    operation = request.get("operation", "equal_s3_static")
    _require(
        operation in {"equal_s3_static", "one_shell_shape_oscillation", "equal_s3_separation_collapse"},
        f"Unsupported spherical_constraint operation: {operation}",
    )
    parameters = request["parameters"]
    for key in ("R", "d", "trace_step", "radius_rate", "internal_speed"):
        _require(key in parameters, f"mapping_request.parameters is missing {key}")
    _require(float(parameters["R"]) > 0.0, "R must be positive")
    _require(float(parameters["d"]) > 0.0, "d must be positive")
    _require(float(parameters["trace_step"]) > 0.0, "trace_step must be positive")

    if operation == "one_shell_shape_oscillation":
        for key in ("deformation_amplitude", "frame_count", "bifurcation_tolerance"):
            _require(key in parameters, f"deformation parameters are missing {key}")
        _require(float(parameters["deformation_amplitude"]) >= 0.0, "deformation_amplitude must be non-negative")
        _require(int(parameters["frame_count"]) >= 3, "frame_count must be at least three")
        _require(float(parameters["bifurcation_tolerance"]) > 0.0, "bifurcation_tolerance must be positive")

    if operation == "equal_s3_separation_collapse":
        for key in (
            "linear_frame_count",
            "linear_end_fraction",
            "critical_gap_exponents",
            "near_critical_relative_gap",
            "above_critical_fraction",
            "bifurcation_tolerance",
        ):
            _require(key in parameters, f"collapse parameters are missing {key}")
        _require(int(parameters["linear_frame_count"]) >= 2, "linear_frame_count must be at least two")
        _require(0.0 < float(parameters["linear_end_fraction"]) < 1.0, "linear_end_fraction must lie in (0,1)")
        exponents = parameters["critical_gap_exponents"]
        _require(isinstance(exponents, list) and exponents, "critical_gap_exponents must be a non-empty list")
        _require(all(int(value) > 0 for value in exponents), "critical gap exponents must be positive")
        _require(0.0 < float(parameters["near_critical_relative_gap"]) < 1.0, "invalid near-critical gap")
        _require(float(parameters["above_critical_fraction"]) > 0.0, "above_critical_fraction must be positive")

    return packet


def validate_mapping_result(result: dict[str, Any]) -> dict[str, Any]:
    _require(result.get("schema_version") == "0.1.0", "Unsupported result schema_version")
    _require(result.get("status") in MAPPING_STATUSES, "Invalid mapping status")
    for key in (
        "mapping_id",
        "equation_id",
        "backend",
        "object_map",
        "operator_map",
        "constraint_realization",
        "solver",
        "readout_map",
        "observables",
        "residuals",
        "diagnostics",
    ):
        _require(key in result, f"Mapping result is missing {key}")
    return result


def load_equation_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    return validate_equation_packet(packet)
