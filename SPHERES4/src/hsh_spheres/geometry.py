"""Quadratic shell constraints and one-dimensional carrier tracing."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Iterable, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares


Vector = NDArray[np.float64]
Matrix = NDArray[np.float64]


@dataclass(frozen=True)
class QuadraticShell:
    """A shell F(x)=(x-c)^T A (x-c)-R^2=0."""

    center: Vector
    shape: Matrix
    radius: float
    label: str = "shell"

    def __post_init__(self) -> None:
        center = np.asarray(self.center, dtype=float)
        shape = np.asarray(self.shape, dtype=float)
        if center.ndim != 1:
            raise ValueError("center must be one-dimensional")
        if shape.shape != (center.size, center.size):
            raise ValueError("shape must be square and match center dimension")
        if not np.allclose(shape, shape.T, atol=1e-12):
            raise ValueError("shape must be symmetric")
        if np.min(np.linalg.eigvalsh(shape)) <= 0.0:
            raise ValueError("shape must be positive definite")
        if self.radius <= 0.0:
            raise ValueError("radius must be positive")
        object.__setattr__(self, "center", center)
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "radius", float(self.radius))

    @property
    def dimension(self) -> int:
        return int(self.center.size)

    def value(self, x: Vector) -> float:
        delta = np.asarray(x, dtype=float) - self.center
        return float(delta @ self.shape @ delta - self.radius**2)

    def gradient(self, x: Vector) -> Vector:
        delta = np.asarray(x, dtype=float) - self.center
        return 2.0 * self.shape @ delta

    def parameter_derivative(
        self,
        x: Vector,
        *,
        center_velocity: Vector | None = None,
        shape_rate: Matrix | None = None,
        radius_rate: float = 0.0,
    ) -> float:
        """Partial derivative of F at fixed x under shell-parameter motion."""

        delta = np.asarray(x, dtype=float) - self.center
        c_dot = np.zeros(self.dimension) if center_velocity is None else np.asarray(center_velocity, dtype=float)
        a_dot = np.zeros_like(self.shape) if shape_rate is None else np.asarray(shape_rate, dtype=float)
        return float(delta @ a_dot @ delta - 2.0 * c_dot @ self.shape @ delta - 2.0 * self.radius * radius_rate)

    def transformed(self, rotation: Matrix, translation: Vector) -> "QuadraticShell":
        rotation = np.asarray(rotation, dtype=float)
        translation = np.asarray(translation, dtype=float)
        return QuadraticShell(
            center=rotation @ self.center + translation,
            shape=rotation @ self.shape @ rotation.T,
            radius=self.radius,
            label=self.label,
        )


@dataclass(frozen=True)
class VelocityDecomposition:
    surface_forced: Vector
    internal_tangent: Vector
    total: Vector
    tangent: Vector
    parameter_derivatives: Vector


@dataclass(frozen=True)
class TraceResult:
    points: Matrix
    circumference: float
    max_constraint_residual: float
    steps: int
    closure_error: float
    closure_method: str = "local_poincare_return"
    tangent_alignment: float = 1.0
    maximum_departure: float = 0.0
    minimum_step_used: float = 0.0
    maximum_step_used: float = 0.0


class ConstraintSystem:
    def __init__(self, shells: Sequence[QuadraticShell]):
        if not shells:
            raise ValueError("At least one shell is required")
        dimension = shells[0].dimension
        if any(shell.dimension != dimension for shell in shells):
            raise ValueError("All shells must share an ambient dimension")
        self.shells = tuple(shells)
        self.dimension = dimension

    def values(self, x: Vector) -> Vector:
        return np.array([shell.value(x) for shell in self.shells], dtype=float)

    def jacobian(self, x: Vector) -> Matrix:
        return np.vstack([shell.gradient(x) for shell in self.shells])

    def singular_values(self, x: Vector) -> Vector:
        return np.linalg.svd(self.jacobian(x), compute_uv=False)

    def rank(self, x: Vector, tolerance: float = 1e-10) -> int:
        return int(np.linalg.matrix_rank(self.jacobian(x), tol=tolerance))

    def tangent(self, x: Vector, *, reference: Vector | None = None) -> Vector:
        jacobian = self.jacobian(x)
        _, singular_values, vh = np.linalg.svd(jacobian, full_matrices=True)
        rank = int(np.sum(singular_values > 1e-10))
        nullity = self.dimension - rank
        if nullity != 1:
            raise ValueError(f"Expected one-dimensional nullspace, found nullity={nullity}")
        tangent = vh[-1].astype(float)
        tangent /= np.linalg.norm(tangent)
        if reference is not None and float(tangent @ reference) < 0.0:
            tangent = -tangent
        return tangent

    def velocity_decomposition(
        self,
        x: Vector,
        shell_rates: Sequence[dict[str, object]],
        *,
        internal_speed: float = 0.0,
        tangent_reference: Vector | None = None,
    ) -> VelocityDecomposition:
        if len(shell_rates) != len(self.shells):
            raise ValueError("One rate dictionary is required per shell")
        partials = np.array(
            [shell.parameter_derivative(x, **rates) for shell, rates in zip(self.shells, shell_rates, strict=True)],
            dtype=float,
        )
        jacobian = self.jacobian(x)
        surface = -np.linalg.pinv(jacobian) @ partials
        tangent = self.tangent(x, reference=tangent_reference)
        internal = float(internal_speed) * tangent
        return VelocityDecomposition(
            surface_forced=surface,
            internal_tangent=internal,
            total=surface + internal,
            tangent=tangent,
            parameter_derivatives=partials,
        )

    def correct_to_carrier(self, predictor: Vector, normal: Vector, *, tolerance: float = 1e-12) -> Vector:
        predictor = np.asarray(predictor, dtype=float)
        normal = np.asarray(normal, dtype=float)

        def augmented_residual(x: Vector) -> Vector:
            return np.concatenate((self.values(x), [float((x - predictor) @ normal)]))

        result = least_squares(
            augmented_residual,
            predictor,
            xtol=tolerance,
            ftol=tolerance,
            gtol=tolerance,
            max_nfev=200,
        )
        if not result.success or np.max(np.abs(self.values(result.x))) > 1e-9:
            raise RuntimeError(f"Carrier correction failed: {result.message}")
        return result.x.astype(float)

    def transformed(self, rotation: Matrix, translation: Vector) -> "ConstraintSystem":
        return ConstraintSystem([shell.transformed(rotation, translation) for shell in self.shells])


def analytic_equal_s3_carrier(radius: float, separation: float) -> tuple[float, float]:
    if radius <= 0.0 or separation <= 0.0:
        raise ValueError("radius and separation must be positive")
    squared = radius**2 - separation**2 / 3.0
    if squared <= 0.0:
        raise ValueError("No regular S^1 carrier: require d < sqrt(3) R")
    rho = sqrt(squared)
    return rho, 2.0 * pi * rho


def equal_s3_system(radius: float, separation: float) -> ConstraintSystem:
    """Three equal S^3 shells centered on an equilateral triangle in x0-x1."""

    circumradius = separation / sqrt(3.0)
    centers = (
        np.array([0.0, circumradius, 0.0, 0.0]),
        np.array([-separation / 2.0, -circumradius / 2.0, 0.0, 0.0]),
        np.array([separation / 2.0, -circumradius / 2.0, 0.0, 0.0]),
    )
    identity = np.eye(4)
    return ConstraintSystem(
        [QuadraticShell(center, identity, radius, label=f"S3_{index + 1}") for index, center in enumerate(centers)]
    )


def trace_closed_carrier(
    system: ConstraintSystem,
    start: Vector,
    *,
    step_size: float,
    max_steps: int = 5000,
    min_steps: int = 20,
    closure_factor: float = 1.25,
    adaptive: bool = False,
    singular_reference: float | None = None,
    minimum_step: float | None = None,
) -> TraceResult:
    """Trace a regular closed carrier with a local Poincare-return test.

    A return is accepted only after the trace has left a neighborhood of its
    starting point, crossed the start's transverse section in the return
    direction, re-entered the local neighborhood, and recovered the starting
    tangent orientation. Optional singular-value scaling reduces the predictor
    step near rank loss.
    """

    start = np.asarray(start, dtype=float)
    if np.max(np.abs(system.values(start))) > 1e-8:
        raise ValueError("start must lie on the carrier")
    points = [start.copy()]
    tangent = system.tangent(start)
    initial_tangent = tangent.copy()
    initial_singular = float(system.singular_values(start)[-1])
    singular_scale = initial_singular if singular_reference is None else float(singular_reference)
    if singular_scale <= 0.0:
        raise ValueError("singular_reference must be positive")
    min_step = max(step_size * 1e-6, 1e-12) if minimum_step is None else float(minimum_step)
    if min_step <= 0.0 or min_step > step_size:
        raise ValueError("minimum_step must be positive and no larger than step_size")
    circumference = 0.0
    residual = float(np.max(np.abs(system.values(start))))
    maximum_departure = 0.0
    departed = False
    departure_threshold: float | None = None
    seen_negative_section = False
    section_previous = 0.0
    step_minimum_used = step_size
    step_maximum_used = 0.0

    for step in range(1, max_steps + 1):
        current = points[-1]
        tangent = system.tangent(current, reference=tangent)
        local_step = step_size
        if adaptive:
            local_singular = float(system.singular_values(current)[-1])
            local_step = step_size * min(1.0, local_singular / singular_scale)
            local_step = max(min_step, local_step)
        step_minimum_used = min(step_minimum_used, local_step)
        step_maximum_used = max(step_maximum_used, local_step)
        if departure_threshold is None:
            departure_threshold = 4.0 * local_step
        predictor = current + local_step * tangent
        corrected = system.correct_to_carrier(predictor, tangent)
        segment = float(np.linalg.norm(corrected - current))
        if segment <= 1e-14:
            raise RuntimeError("Continuation stalled")
        distance_to_start = float(np.linalg.norm(corrected - start))
        maximum_departure = max(maximum_departure, distance_to_start)
        if distance_to_start > departure_threshold:
            departed = True

        section_current = float((corrected - start) @ initial_tangent)
        if section_current < 0.0:
            seen_negative_section = True

        is_return_crossing = section_previous < 0.0 <= section_current
        if step >= min_steps and departed and seen_negative_section and is_return_crossing:
            denominator = section_current - section_previous
            fraction = -section_previous / denominator if denominator != 0.0 else 1.0
            fraction = float(np.clip(fraction, 0.0, 1.0))
            crossing_predictor = current + fraction * (corrected - current)
            crossing = system.correct_to_carrier(crossing_predictor, initial_tangent)
            crossing_distance = float(np.linalg.norm(crossing - start))
            crossing_tangent = system.tangent(crossing, reference=tangent)
            alignment = float(crossing_tangent @ initial_tangent)
            if crossing_distance < closure_factor * max(local_step, min_step) and alignment > 0.95:
                circumference += float(np.linalg.norm(crossing - current))
                circumference += crossing_distance
                residual = max(residual, float(np.max(np.abs(system.values(crossing)))))
                points.append(start.copy())
                return TraceResult(
                    points=np.vstack(points),
                    circumference=circumference,
                    max_constraint_residual=residual,
                    steps=step,
                    closure_error=crossing_distance,
                    tangent_alignment=alignment,
                    maximum_departure=maximum_departure,
                    minimum_step_used=step_minimum_used,
                    maximum_step_used=step_maximum_used,
                )

        points.append(corrected)
        circumference += segment
        residual = max(residual, float(np.max(np.abs(system.values(corrected)))))
        section_previous = section_current

    raise RuntimeError("Carrier did not close within max_steps")


def max_constraint_residual(system: ConstraintSystem, points: Iterable[Vector]) -> float:
    return max(float(np.max(np.abs(system.values(point)))) for point in points)
