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
    parameters = request["parameters"]
    for key in ("R", "d", "trace_step", "radius_rate", "internal_speed"):
        _require(key in parameters, f"mapping_request.parameters is missing {key}")
    _require(float(parameters["R"]) > 0.0, "R must be positive")
    _require(float(parameters["d"]) > 0.0, "d must be positive")
    _require(float(parameters["trace_step"]) > 0.0, "trace_step must be positive")

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
