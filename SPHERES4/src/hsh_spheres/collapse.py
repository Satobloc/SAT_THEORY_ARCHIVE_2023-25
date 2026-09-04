"""Exact symmetric carrier-collapse benchmark for three equal S^3 shells."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq

from .contracts import validate_equation_packet, validate_mapping_result
from .deformation import CurveMetrics, discrete_curve_metrics
from .geometry import ConstraintSystem, TraceResult, analytic_equal_s3_carrier, equal_s3_system, trace_closed_carrier


Vector = NDArray[np.float64]
Matrix = NDArray[np.float64]


@dataclass(frozen=True)
class AnalyticCollapseState:
    separation: float
    critical_separation: float
    classification: str
    radius: float | None
    circumference: float | None
    curvature: float | None
    radius_derivative: float | None
    singular_values: tuple[float, float, float]


@dataclass(frozen=True)
class CollapseFrame:
    analytic: AnalyticCollapseState
    trace: TraceResult | None
    metrics: CurveMetrics | None
    radius_numeric: float | None
    radius_derivative_numeric: float | None
    singular_values_numeric: tuple[float, float, float]
    points: Matrix | None
    numerical_status: str
    numerical_note: str | None = None


@dataclass(frozen=True)
class CollapseSweep:
    frames: tuple[CollapseFrame, ...]
    critical_separation_exact: float
    critical_separation_numeric: float
    event_location_error: float


def analytic_collapse_state(
    radius: float,
    separation: float,
    *,
    near_critical_relative_gap: float,
    equality_tolerance: float = 1e-14,
) -> AnalyticCollapseState:
    critical = sqrt(3.0) * radius
    discriminant = radius**2 - separation**2 / 3.0
    relative_gap = (critical - separation) / critical
    planar = sqrt(2.0) * separation

    if abs(separation - critical) <= equality_tolerance * max(1.0, critical):
        return AnalyticCollapseState(
            separation=separation,
            critical_separation=critical,
            classification="rank_loss_point",
            radius=0.0,
            circumference=0.0,
            curvature=None,
            radius_derivative=None,
            singular_values=(planar, planar, 0.0),
        )
    if discriminant < 0.0:
        return AnalyticCollapseState(
            separation=separation,
            critical_separation=critical,
            classification="no_real_carrier",
            radius=None,
            circumference=None,
            curvature=None,
            radius_derivative=None,
            singular_values=(planar, planar, 0.0),
        )

    rho = sqrt(discriminant)
    common = 2.0 * sqrt(3.0) * rho
    classification = (
        "near_critical_closed_carrier"
        if relative_gap <= near_critical_relative_gap
        else "regular_closed_carrier"
    )
    return AnalyticCollapseState(
        separation=separation,
        critical_separation=critical,
        classification=classification,
        radius=rho,
        circumference=2.0 * pi * rho,
        curvature=1.0 / rho,
        radius_derivative=-separation / (3.0 * rho),
        singular_values=tuple(sorted((common, planar, planar), reverse=True)),
    )


def equal_center_separation_rates() -> tuple[dict[str, object], ...]:
    """Center derivatives dc_a/dd for the centered equilateral construction."""

    return (
        {"center_velocity": np.array([0.0, 1.0 / sqrt(3.0), 0.0, 0.0])},
        {"center_velocity": np.array([-0.5, -0.5 / sqrt(3.0), 0.0, 0.0])},
        {"center_velocity": np.array([0.5, -0.5 / sqrt(3.0), 0.0, 0.0])},
    )


def collapse_separations(
    *,
    radius: float,
    start: float,
    linear_frame_count: int,
    linear_end_fraction: float,
    critical_gap_exponents: Sequence[int],
    above_critical_fraction: float,
) -> tuple[float, ...]:
    critical = sqrt(3.0) * radius
    if not (0.0 < start < critical):
        raise ValueError("start separation must lie below the critical separation")
    linear = np.linspace(start, critical * linear_end_fraction, int(linear_frame_count))
    near = [critical * (1.0 - 10.0 ** (-int(exponent))) for exponent in critical_gap_exponents]
    values = list(linear) + near + [critical, critical * (1.0 + above_critical_fraction)]
    return tuple(sorted(set(float(value) for value in values)))


def run_collapse_sweep(
    *,
    radius: float,
    start_separation: float,
    trace_step: float,
    linear_frame_count: int,
    linear_end_fraction: float,
    critical_gap_exponents: Sequence[int],
    near_critical_relative_gap: float,
    above_critical_fraction: float,
) -> CollapseSweep:
    critical = sqrt(3.0) * radius
    separations = collapse_separations(
        radius=radius,
        start=start_separation,
        linear_frame_count=linear_frame_count,
        linear_end_fraction=linear_end_fraction,
        critical_gap_exponents=critical_gap_exponents,
        above_critical_fraction=above_critical_fraction,
    )
    base_rho, _ = analytic_equal_s3_carrier(radius, start_separation)
    base_system = equal_s3_system(radius, start_separation)
    base_start = np.array([0.0, 0.0, base_rho, 0.0])
    singular_reference = float(base_system.singular_values(base_start)[-1])
    rates = equal_center_separation_rates()
    frames: list[CollapseFrame] = []

    for separation in separations:
        analytic = analytic_collapse_state(
            radius,
            separation,
            near_critical_relative_gap=near_critical_relative_gap,
        )
        if analytic.classification in {"regular_closed_carrier", "near_critical_closed_carrier"}:
            if analytic.radius is None:
                raise RuntimeError("Regular state is missing its radius")
            system = equal_s3_system(radius, separation)
            start = np.array([0.0, 0.0, analytic.radius, 0.0])
            numeric_singular = tuple(float(value) for value in system.singular_values(start))
            try:
                trace = trace_closed_carrier(
                    system,
                    start,
                    step_size=trace_step,
                    adaptive=True,
                    singular_reference=singular_reference,
                    minimum_step=trace_step * 1e-8,
                )
                metrics = discrete_curve_metrics(trace.points)
                points = trace.points[:-1]
                numeric_radius = float(np.mean(np.linalg.norm(points[:, 2:4], axis=1)))
                velocity = system.velocity_decomposition(start, rates, internal_speed=0.0)
                numeric_derivative = float(velocity.surface_forced[2])
                frames.append(
                    CollapseFrame(
                        analytic=analytic,
                        trace=trace,
                        metrics=metrics,
                        radius_numeric=numeric_radius,
                        radius_derivative_numeric=numeric_derivative,
                        singular_values_numeric=numeric_singular,
                        points=trace.points,
                        numerical_status="traced_and_certified",
                    )
                )
            except RuntimeError as error:
                frames.append(
                    CollapseFrame(
                        analytic=analytic,
                        trace=None,
                        metrics=None,
                        radius_numeric=None,
                        radius_derivative_numeric=None,
                        singular_values_numeric=numeric_singular,
                        points=None,
                        numerical_status="conditioning_limit",
                        numerical_note=str(error),
                    )
                )
        elif analytic.classification == "rank_loss_point":
            system = equal_s3_system(radius, separation)
            point = np.zeros(4)
            singular = tuple(float(value) for value in system.singular_values(point))
            frames.append(
                CollapseFrame(
                    analytic, None, None, 0.0, None, singular, point[None, :], "rank_loss_evaluated"
                )
            )
        else:
            frames.append(
                CollapseFrame(
                    analytic, None, None, None, None, analytic.singular_values, None, "no_real_carrier"
                )
            )

    discriminant = lambda value: radius**2 - value**2 / 3.0
    numeric_critical = float(brentq(discriminant, start_separation, critical * (1.0 + above_critical_fraction)))
    return CollapseSweep(
        frames=tuple(frames),
        critical_separation_exact=critical,
        critical_separation_numeric=numeric_critical,
        event_location_error=abs(numeric_critical - critical),
    )


def _relative_error(calculated: float | None, expected: float | None) -> float | None:
    if calculated is None or expected is None:
        return None
    return abs(calculated - expected) / abs(expected) if expected != 0.0 else abs(calculated)


def collapse_result(packet: dict[str, Any]) -> tuple[dict[str, Any], CollapseSweep]:
    packet = validate_equation_packet(packet)
    params = packet["mapping_request"]["parameters"]
    sweep = run_collapse_sweep(
        radius=float(params["R"]),
        start_separation=float(params["d"]),
        trace_step=float(params["trace_step"]),
        linear_frame_count=int(params["linear_frame_count"]),
        linear_end_fraction=float(params["linear_end_fraction"]),
        critical_gap_exponents=[int(value) for value in params["critical_gap_exponents"]],
        near_critical_relative_gap=float(params["near_critical_relative_gap"]),
        above_critical_fraction=float(params["above_critical_fraction"]),
    )
    rows = []
    for index, frame in enumerate(sweep.frames):
        analytic = frame.analytic
        rows.append(
            {
                "frame": index,
                "separation": analytic.separation,
                "relative_gap_to_critical": (analytic.critical_separation - analytic.separation) / analytic.critical_separation,
                "classification": analytic.classification,
                "numerical_status": frame.numerical_status,
                "numerical_note": frame.numerical_note,
                "radius_exact": analytic.radius,
                "radius_numeric": frame.radius_numeric,
                "radius_relative_error": _relative_error(frame.radius_numeric, analytic.radius),
                "circumference_exact": analytic.circumference,
                "circumference_numeric": None if frame.metrics is None else frame.metrics.circumference,
                "circumference_relative_error": _relative_error(
                    None if frame.metrics is None else frame.metrics.circumference,
                    analytic.circumference,
                ),
                "curvature_exact": analytic.curvature,
                "curvature_numeric": None if frame.metrics is None else frame.metrics.curvature_mean,
                "curvature_relative_error": _relative_error(
                    None if frame.metrics is None else frame.metrics.curvature_mean,
                    analytic.curvature,
                ),
                "radius_derivative_exact": analytic.radius_derivative,
                "radius_derivative_numeric": frame.radius_derivative_numeric,
                "radius_derivative_relative_error": _relative_error(
                    frame.radius_derivative_numeric,
                    analytic.radius_derivative,
                ),
                "singular_values_exact": list(analytic.singular_values),
                "singular_values_numeric": list(frame.singular_values_numeric),
                "smallest_singular_value": frame.singular_values_numeric[-1],
                "constraint_max_absolute": None if frame.trace is None else frame.trace.max_constraint_residual,
                "closure_return_error": None if frame.trace is None else frame.trace.closure_error,
                "trace_steps": None if frame.trace is None else frame.trace.steps,
                "minimum_step_used": None if frame.trace is None else frame.trace.minimum_step_used,
            }
        )

    regular_rows = [row for row in rows if row["numerical_status"] == "traced_and_certified"]
    result = {
        "schema_version": "0.1.0",
        "mapping_id": f"MAP-{packet['equation_id']}-SPHERICAL-COLLAPSE-0001",
        "equation_id": packet["equation_id"],
        "backend": "spherical_constraint",
        "status": "exact_identity_with_numerical_verification",
        "object_map": {
            "three_standard_shells": "three equal QuadraticShell instances",
            "regular_intersection": "closed S^1 carrier",
            "critical_intersection": "rank-loss point",
            "supercritical_intersection": "empty real carrier",
            "ontology_claim": "none; geometric event benchmark only"
        },
        "operator_map": {
            "continuation_parameter": "equilateral center separation d",
            "adaptive_step": "base step scaled by local/reference smallest singular value",
            "closure": "departure plus local Poincare return plus tangent recovery",
            "event_indicator": "smallest singular value of J",
            "superhelical_nesting": "not invoked",
            "braid_nesting": "not invoked"
        },
        "constraint_realization": {
            "ambient_dimension": 4,
            "constraint_count": 3,
            "critical_separation_exact": sweep.critical_separation_exact,
            "critical_rank": 2
        },
        "solver": {
            "regular_carrier": "adaptive predictor-corrector continuation",
            "event_location": "bracketed Brent scalar root of the authoritative discriminant",
            "history_frame_count": len(sweep.frames)
        },
        "readout_map": {
            "event_history": "analytic and numerical radius, circumference, curvature, response, and singular values",
            "event_classification": "regular, near-critical, rank-loss, or no-real-carrier"
        },
        "observables": {
            "critical_separation_exact": sweep.critical_separation_exact,
            "critical_separation_numeric": sweep.critical_separation_numeric,
            "event_location_absolute_error": sweep.event_location_error,
            "history": rows
        },
        "residuals": {
            "radius_relative_max": max(row["radius_relative_error"] for row in regular_rows),
            "circumference_relative_max": max(row["circumference_relative_error"] for row in regular_rows),
            "curvature_relative_max": max(row["curvature_relative_error"] for row in regular_rows),
            "response_relative_max": max(row["radius_derivative_relative_error"] for row in regular_rows),
            "singular_value_relative_max": max(
                max(
                    abs(numeric - exact) / abs(exact) if exact != 0.0 else abs(numeric)
                    for numeric, exact in zip(row["singular_values_numeric"], row["singular_values_exact"], strict=True)
                )
                for row in regular_rows
            ),
            "constraint_max_absolute": max(row["constraint_max_absolute"] for row in regular_rows),
            "closure_return_max_absolute": max(row["closure_return_error"] for row in regular_rows)
        },
        "diagnostics": {
            "critical_behavior": {
                "radius": "tends to zero",
                "circumference": "tends to zero",
                "curvature": "diverges",
                "radius_derivative": "diverges negative",
                "common_singular_value": "tends to zero"
            },
            "classifications_present": sorted(set(row["classification"] for row in rows)),
            "numerical_statuses_present": sorted(set(row["numerical_status"] for row in rows)),
            "conditioning_limit_frames": [
                row["frame"] for row in rows if row["numerical_status"] == "conditioning_limit"
            ],
            "physical_event_inference": "none"
        },
        "provenance": {
            "input_authority": packet["authority"],
            "calibrations": [],
            "candidate_physics": [],
            "silent_repairs": []
        }
    }
    return validate_mapping_result(result), sweep


def concatenate_collapse_points(frames: Sequence[CollapseFrame]) -> tuple[Matrix, NDArray[np.int64], Vector]:
    traced = [frame for frame in frames if frame.points is not None]
    lengths = np.array([frame.points.shape[0] for frame in traced], dtype=np.int64)
    offsets = np.concatenate((np.array([0], dtype=np.int64), np.cumsum(lengths)))
    points = np.vstack([frame.points for frame in traced])
    separations = np.array([frame.analytic.separation for frame in traced], dtype=float)
    return points, offsets, separations
