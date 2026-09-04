"""One-shell deformation cycle for the spherical-constraint backend."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, exp, pi, sin
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from .contracts import validate_equation_packet, validate_mapping_result
from .geometry import ConstraintSystem, QuadraticShell, TraceResult, analytic_equal_s3_carrier, equal_s3_system, trace_closed_carrier


Vector = NDArray[np.float64]
Matrix = NDArray[np.float64]


@dataclass(frozen=True)
class CurveMetrics:
    circumference: float
    curvature_mean: float
    curvature_min: float
    curvature_max: float


@dataclass(frozen=True)
class DeformationFrame:
    phase: float
    epsilon: float
    shape_determinant: float
    trace: TraceResult
    metrics: CurveMetrics
    seed: Vector
    surface_forced: Vector
    internal_tangent: Vector
    total_velocity: Vector
    moving_constraint_residual: float
    minimum_jacobian_singular_value: float
    bifurcation_flag: bool


@dataclass(frozen=True)
class DeformationCycle:
    frames: tuple[DeformationFrame, ...]
    seed_cycle_error: float
    maximum_constraint_residual: float
    minimum_jacobian_singular_value: float


def oscillating_shape(phase: float, amplitude: float) -> tuple[Matrix, Matrix, float]:
    """Return A(phi), dA/dphi, and epsilon for a determinant-one deformation."""

    epsilon = float(amplitude) * sin(float(phase))
    epsilon_rate = float(amplitude) * cos(float(phase))
    a2 = exp(-2.0 * epsilon)
    a3 = exp(2.0 * epsilon)
    shape = np.diag([1.0, 1.0, a2, a3])
    shape_rate = np.diag([0.0, 0.0, -2.0 * epsilon_rate * a2, 2.0 * epsilon_rate * a3])
    return shape, shape_rate, epsilon


def one_shell_deformed_system(
    radius: float,
    separation: float,
    phase: float,
    amplitude: float,
) -> tuple[ConstraintSystem, tuple[dict[str, object], ...], float]:
    base = equal_s3_system(radius, separation)
    shape, shape_rate, epsilon = oscillating_shape(phase, amplitude)
    shells = list(base.shells)
    shells[0] = QuadraticShell(shells[0].center, shape, radius, label="S3_1_deformed")
    rates: tuple[dict[str, object], ...] = (
        {"shape_rate": shape_rate},
        {},
        {},
    )
    return ConstraintSystem(shells), rates, epsilon


def discrete_curve_metrics(points: Matrix) -> CurveMetrics:
    """Calculate closed-polyline length and a discrete curvature estimate in R^D."""

    points = np.asarray(points, dtype=float)
    if points.shape[0] < 5:
        raise ValueError("At least four unique closed-curve points are required")
    unique = points[:-1] if np.linalg.norm(points[0] - points[-1]) < 1e-10 else points
    previous = np.roll(unique, 1, axis=0)
    following = np.roll(unique, -1, axis=0)
    backward_segments = unique - previous
    forward_segments = following - unique
    ds_back = np.linalg.norm(backward_segments, axis=1)
    ds_forward = np.linalg.norm(forward_segments, axis=1)
    if np.any(ds_back <= 0.0) or np.any(ds_forward <= 0.0):
        raise ValueError("Curve contains repeated adjacent points")
    tangent_back = backward_segments / ds_back[:, None]
    tangent_forward = forward_segments / ds_forward[:, None]
    local_ds = 0.5 * (ds_back + ds_forward)
    curvature = np.linalg.norm(tangent_forward - tangent_back, axis=1) / local_ds
    circumference = float(np.sum(ds_forward))
    return CurveMetrics(
        circumference=circumference,
        curvature_mean=float(np.mean(curvature)),
        curvature_min=float(np.min(curvature)),
        curvature_max=float(np.max(curvature)),
    )


def trace_deformation_cycle(
    *,
    radius: float,
    separation: float,
    amplitude: float,
    frame_count: int,
    trace_step: float,
    internal_speed: float,
    bifurcation_tolerance: float,
) -> DeformationCycle:
    rho, _ = analytic_equal_s3_carrier(radius, separation)
    phases = np.linspace(0.0, 2.0 * pi, int(frame_count), endpoint=True)
    initial_seed = np.array([0.0, 0.0, rho, 0.0])
    seed = initial_seed.copy()
    tangent_reference: Vector | None = None
    frames: list[DeformationFrame] = []

    for index, phase in enumerate(phases):
        system, rates, epsilon = one_shell_deformed_system(radius, separation, float(phase), amplitude)
        if index > 0:
            if tangent_reference is None:
                raise RuntimeError("Missing tangent reference")
            seed = system.correct_to_carrier(seed, tangent_reference)
        tangent_reference = system.tangent(seed, reference=tangent_reference)
        trace = trace_closed_carrier(system, seed, step_size=trace_step)
        metrics = discrete_curve_metrics(trace.points)
        velocity = system.velocity_decomposition(
            seed,
            rates,
            internal_speed=internal_speed,
            tangent_reference=tangent_reference,
        )
        moving_residual = float(
            np.linalg.norm(system.jacobian(seed) @ velocity.surface_forced + velocity.parameter_derivatives)
        )
        singular_minimum = min(float(system.singular_values(point)[-1]) for point in trace.points[:-1])
        frames.append(
            DeformationFrame(
                phase=float(phase),
                epsilon=epsilon,
                shape_determinant=float(np.linalg.det(system.shells[0].shape)),
                trace=trace,
                metrics=metrics,
                seed=seed.copy(),
                surface_forced=velocity.surface_forced.copy(),
                internal_tangent=velocity.internal_tangent.copy(),
                total_velocity=velocity.total.copy(),
                moving_constraint_residual=moving_residual,
                minimum_jacobian_singular_value=singular_minimum,
                bifurcation_flag=singular_minimum <= bifurcation_tolerance,
            )
        )

    return DeformationCycle(
        frames=tuple(frames),
        seed_cycle_error=float(np.linalg.norm(frames[-1].seed - initial_seed)),
        maximum_constraint_residual=max(frame.trace.max_constraint_residual for frame in frames),
        minimum_jacobian_singular_value=min(frame.minimum_jacobian_singular_value for frame in frames),
    )


def deformation_result(packet: dict[str, Any]) -> tuple[dict[str, Any], DeformationCycle]:
    packet = validate_equation_packet(packet)
    params = packet["mapping_request"]["parameters"]
    cycle = trace_deformation_cycle(
        radius=float(params["R"]),
        separation=float(params["d"]),
        amplitude=float(params["deformation_amplitude"]),
        frame_count=int(params["frame_count"]),
        trace_step=float(params["trace_step"]),
        internal_speed=float(params["internal_speed"]),
        bifurcation_tolerance=float(params["bifurcation_tolerance"]),
    )
    frame_rows = [
        {
            "frame": index,
            "phase": frame.phase,
            "epsilon": frame.epsilon,
            "shape_determinant": frame.shape_determinant,
            "circumference": frame.metrics.circumference,
            "curvature_mean": frame.metrics.curvature_mean,
            "curvature_min": frame.metrics.curvature_min,
            "curvature_max": frame.metrics.curvature_max,
            "surface_forced_speed_per_phase": float(np.linalg.norm(frame.surface_forced)),
            "internal_speed_per_phase": float(np.linalg.norm(frame.internal_tangent)),
            "moving_constraint_residual": frame.moving_constraint_residual,
            "constraint_max_absolute": frame.trace.max_constraint_residual,
            "minimum_jacobian_singular_value": frame.minimum_jacobian_singular_value,
            "bifurcation_flag": frame.bifurcation_flag,
            "point_count": int(frame.trace.points.shape[0]),
        }
        for index, frame in enumerate(cycle.frames)
    ]
    first = cycle.frames[0]
    last = cycle.frames[-1]
    circumference_cycle_error = abs(last.metrics.circumference - first.metrics.circumference)
    curvature_cycle_error = abs(last.metrics.curvature_mean - first.metrics.curvature_mean)
    determinant_error = max(abs(frame.shape_determinant - 1.0) for frame in cycle.frames)
    result = {
        "schema_version": "0.1.0",
        "mapping_id": f"MAP-{packet['equation_id']}-SPHERICAL-DEFORM-0001",
        "equation_id": packet["equation_id"],
        "backend": "spherical_constraint",
        "status": "coordinate_rewrite",
        "object_map": {
            "deforming_standard_shell": "time-parameterized QuadraticShell",
            "fixed_standard_shells": "two QuadraticShell instances",
            "common_intersection": "evolving closed one-dimensional carrier",
            "ambient_space": "R^4",
            "ontology_claim": "none; computational representation only"
        },
        "operator_map": {
            "shape_deformation": "A_1(phi)=diag(1,1,exp(-2 epsilon),exp(2 epsilon))",
            "shape_rate": "analytic dA_1/dphi",
            "carrier_tangent": "one-dimensional nullspace of J",
            "surface_forced_velocity": "-pinv(J) partial_phi(F)",
            "internal_velocity": "u t",
            "superhelical_nesting": "not invoked",
            "braid_nesting": "not invoked"
        },
        "constraint_realization": {
            "constraint_count": 3,
            "ambient_dimension": 4,
            "phase_interval": [0.0, 2.0 * pi],
            "frame_count": len(cycle.frames),
            "shape_determinant_target": 1.0
        },
        "solver": {
            "method": "frame continuation plus closed-carrier predictor-corrector tracing",
            "trace_step": float(params["trace_step"]),
            "seed_transport": "previous-frame seed corrected into current constraints"
        },
        "readout_map": {
            "history": "per-frame carrier circumference, discrete curvature, velocity decomposition, and rank margin",
            "curve_coordinates": "exported separately as concatenated R^4 point arrays",
            "phase_warning": "velocity values are per unit deformation phase, not per unit physical time"
        },
        "observables": {
            "deformation_amplitude": float(params["deformation_amplitude"]),
            "circumference_min": min(frame.metrics.circumference for frame in cycle.frames),
            "circumference_max": max(frame.metrics.circumference for frame in cycle.frames),
            "curvature_mean_min": min(frame.metrics.curvature_mean for frame in cycle.frames),
            "curvature_mean_max": max(frame.metrics.curvature_mean for frame in cycle.frames),
            "surface_forced_speed_max_per_phase": max(float(np.linalg.norm(frame.surface_forced)) for frame in cycle.frames),
            "minimum_jacobian_singular_value": cycle.minimum_jacobian_singular_value,
            "bifurcation_detected": any(frame.bifurcation_flag for frame in cycle.frames),
            "frame_history": frame_rows
        },
        "residuals": {
            "constraint_max_absolute": cycle.maximum_constraint_residual,
            "seed_cycle_closure_absolute": cycle.seed_cycle_error,
            "circumference_cycle_closure_absolute": circumference_cycle_error,
            "curvature_cycle_closure_absolute": curvature_cycle_error,
            "shape_determinant_max_absolute": determinant_error,
            "moving_constraint_max_absolute": max(frame.moving_constraint_residual for frame in cycle.frames)
        },
        "diagnostics": {
            "bifurcation_indicator": "minimum singular value of J over each carrier",
            "bifurcation_tolerance": float(params["bifurcation_tolerance"]),
            "bifurcation_frames": [index for index, frame in enumerate(cycle.frames) if frame.bifurcation_flag],
            "endpoint_geometry": "identical by construction at phi=0 and phi=2*pi"
        },
        "provenance": {
            "input_authority": packet["authority"],
            "calibrations": [],
            "candidate_physics": [],
            "silent_repairs": []
        }
    }
    return validate_mapping_result(result), cycle


def concatenate_cycle_points(frames: Sequence[DeformationFrame]) -> tuple[Matrix, NDArray[np.int64]]:
    lengths = np.array([frame.trace.points.shape[0] for frame in frames], dtype=np.int64)
    offsets = np.concatenate((np.array([0], dtype=np.int64), np.cumsum(lengths)))
    points = np.vstack([frame.trace.points for frame in frames])
    return points, offsets
