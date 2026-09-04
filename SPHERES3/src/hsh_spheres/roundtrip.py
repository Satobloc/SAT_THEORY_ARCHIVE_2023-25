"""Standard-equation packet to H(s)H geometric round trip."""

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np

from .contracts import validate_equation_packet, validate_mapping_result
from .geometry import analytic_equal_s3_carrier, equal_s3_system, trace_closed_carrier


def _relative_error(calculated: float, expected: float) -> float:
    return abs(calculated - expected) / abs(expected) if expected != 0.0 else abs(calculated)


def run_roundtrip(packet: dict[str, Any]) -> dict[str, Any]:
    packet = validate_equation_packet(packet)
    params = packet["mapping_request"]["parameters"]
    radius = float(params["R"])
    separation = float(params["d"])
    trace_step = float(params["trace_step"])
    radius_rate = float(params["radius_rate"])
    internal_speed = float(params["internal_speed"])

    rho_exact, circumference_exact = analytic_equal_s3_carrier(radius, separation)
    system = equal_s3_system(radius, separation)
    start = np.array([0.0, 0.0, rho_exact, 0.0])
    trace = trace_closed_carrier(system, start, step_size=trace_step)

    points = trace.points[:-1]
    radii = np.linalg.norm(points[:, 2:4], axis=1)
    rho_numeric = float(np.mean(radii))
    radius_spread = float(np.max(np.abs(radii - rho_exact)))

    rates = [{"radius_rate": radius_rate} for _ in system.shells]
    velocity = system.velocity_decomposition(start, rates, internal_speed=internal_speed)
    forced_speed_exact = radius * radius_rate / rho_exact
    forced_speed_numeric = float(velocity.surface_forced[2])
    tangent_constraint_residual = float(np.linalg.norm(system.jacobian(start) @ velocity.internal_tangent))
    velocity_constraint_residual = float(
        np.linalg.norm(system.jacobian(start) @ velocity.surface_forced + velocity.parameter_derivatives)
    )

    near_critical_d = sqrt(3.0) * radius * (1.0 - 1e-8)
    near_rho, _ = analytic_equal_s3_carrier(radius, near_critical_d)
    near_system = equal_s3_system(radius, near_critical_d)
    near_start = np.array([0.0, 0.0, near_rho, 0.0])
    regular_singular_values = system.singular_values(start)
    near_singular_values = near_system.singular_values(near_start)

    result = {
        "schema_version": "0.1.0",
        "mapping_id": f"MAP-{packet['equation_id']}-SPHERICAL-0001",
        "equation_id": packet["equation_id"],
        "backend": "spherical_constraint",
        "status": "exact_identity_with_numerical_verification",
        "object_map": {
            "standard_shell": "QuadraticShell",
            "common_intersection": "one-dimensional carrier",
            "carrier_topology": "S^1",
            "ambient_space": "R^4",
            "ontology_claim": "none; computational representation only"
        },
        "operator_map": {
            "intersection": "simultaneous constraint solution F_1=F_2=F_3=0",
            "carrier_tangent": "normalized one-dimensional nullspace of J",
            "surface_forced_velocity": "-pinv(J) partial_lambda(F)",
            "internal_velocity": "u t",
            "superhelical_nesting": "not invoked",
            "braid_nesting": "not invoked"
        },
        "constraint_realization": {
            "equation": "F_a(x)=(x-c_a)^T A_a (x-c_a)-R_a^2=0",
            "constraint_count": 3,
            "ambient_dimension": 4,
            "regular_rank": system.rank(start),
            "regular_nullity": 4 - system.rank(start)
        },
        "solver": {
            "method": "pseudo-arclength-style predictor-corrector continuation",
            "corrector": "nonlinear least squares with tangent hyperplane gauge",
            "trace_step": trace_step,
            "steps": trace.steps
        },
        "readout_map": {
            "carrier_radius": "mean Euclidean radius in the plane orthogonal to the center triangle",
            "carrier_circumference": "closed traced polyline length",
            "velocity": "v_total=v_surface+v_internal"
        },
        "observables": {
            "carrier_radius_exact": rho_exact,
            "carrier_radius_numeric": rho_numeric,
            "carrier_circumference_exact": circumference_exact,
            "carrier_circumference_numeric": trace.circumference,
            "surface_forced_speed_exact": forced_speed_exact,
            "surface_forced_speed_numeric": forced_speed_numeric,
            "internal_speed": float(np.linalg.norm(velocity.internal_tangent)),
            "total_velocity": velocity.total.tolist()
        },
        "residuals": {
            "carrier_radius_relative": _relative_error(rho_numeric, rho_exact),
            "carrier_circumference_relative": _relative_error(trace.circumference, circumference_exact),
            "surface_forced_speed_relative": _relative_error(forced_speed_numeric, forced_speed_exact),
            "radius_pointwise_max_absolute": radius_spread,
            "constraint_max_absolute": trace.max_constraint_residual,
            "internal_tangent_constraint_norm": tangent_constraint_residual,
            "surface_velocity_constraint_norm": velocity_constraint_residual
        },
        "diagnostics": {
            "regular_jacobian_singular_values": regular_singular_values.tolist(),
            "near_bifurcation_separation": near_critical_d,
            "near_bifurcation_carrier_radius": near_rho,
            "near_bifurcation_jacobian_singular_values": near_singular_values.tolist(),
            "smallest_singular_value_ratio": float(near_singular_values[-1] / regular_singular_values[-1]),
            "bifurcation_condition": "smallest singular value tends to zero as d tends to sqrt(3)R"
        },
        "provenance": {
            "input_authority": packet["authority"],
            "calibrations": [],
            "candidate_physics": [],
            "silent_repairs": []
        }
    }
    return validate_mapping_result(result)
