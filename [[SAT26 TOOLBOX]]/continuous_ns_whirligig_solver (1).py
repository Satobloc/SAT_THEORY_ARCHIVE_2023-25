#!/usr/bin/env python3
"""
Continuous spectral Navier–Stokes Whirligig solver.

This is the current pre-optimization solver. It freezes the continuous
Whirligig mechanics and replaces only the two body-fixed input curves with
invertible spectral encodings of the two trial velocity fields:

    A(x,y,z) = (sin z, 0, 0)

    B_epsilon(x,y,z) =
        (-sin y / D, sin x / D, 0)

    D = epsilon^2 + 2 - cos x - cos y

The construction uses:

- sparse 3-D real Fourier coefficients;
- a continuous one-dimensional trigonometric-polynomial encoding;
- an invertible tanh latitude map;
- annulus-controlled rolling;
- continuous connector sweep;
- a Bishop / parallel-transport connector frame;
- constant pen rotation;
- first forward ray intersection with the fixed torus wall.

Finite evaluations are used only to numerically solve and render the
continuous construction. They do not define the input curves.

This version does NOT yet optimize the traversal laws for minimum curvature.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SolverConfig:
    # Input grid
    nx: int = 12
    ny: int = 12
    nz: int = 8
    epsilon: float = 0.35

    # Torus and ball
    torus_major_radius: float = 1.60
    torus_minor_radius: float = 0.55
    ball_radius: float = 0.55

    # Spectral-to-sphere latitude map
    latitude_center: float = 0.84
    latitude_amplitude: float = 0.43
    encoding_gain: float = 1.10
    curve_render_samples: int = 4096

    # Continuous mechanics
    pen_angular_rate: float = 17.0
    tau_end: float = 2.0 * np.pi
    n_eval: int = 16_000

    # Original frozen V1 traversal laws
    alpha_linear_rate: float = 9.0
    alpha_modulation_amplitude: float = 0.15
    alpha_modulation_frequency: float = 2.0

    beta_linear_rate: float = -13.0
    beta_modulation_amplitude: float = 0.22
    beta_modulation_frequency: float = 3.0
    beta_phase_offset: float = 0.7


def build_trial_fields(
    cfg: SolverConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.linspace(0.0, 2.0 * np.pi, cfg.nx, endpoint=False)
    y = np.linspace(0.0, 2.0 * np.pi, cfg.ny, endpoint=False)
    z = np.linspace(0.0, 2.0 * np.pi, cfg.nz, endpoint=False)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

    u_a = np.stack(
        [np.sin(Z), np.zeros_like(Z), np.zeros_like(Z)],
        axis=-1,
    )

    denominator = (
        cfg.epsilon**2
        + 2.0
        - np.cos(X)
        - np.cos(Y)
    )
    u_b = np.stack(
        [
            -np.sin(Y) / denominator,
            np.sin(X) / denominator,
            np.zeros_like(denominator),
        ],
        axis=-1,
    )

    return x, y, z, u_a, u_b


def sparse_spectral_encoding(
    field: np.ndarray,
    curve_samples: int,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """
    Encode the full finite-grid vector field through sparse 3-D rFFT data.

    Each retained complex coefficient c_j supplies one harmonic of a
    continuous scalar trigonometric polynomial:

        Re(c_j) -> cosine amplitude
        Im(c_j) -> sine amplitude
    """
    entries: list[tuple[int, int, complex]] = []
    coeff_shape: tuple[int, ...] | None = None

    for component in range(3):
        coeff_array = np.fft.rfftn(
            field[..., component],
            norm="ortho",
        )
        coeff_shape = coeff_array.shape
        flat = coeff_array.reshape(-1)
        retained = np.flatnonzero(np.abs(flat) > tolerance)

        for index in retained:
            entries.append(
                (component, int(index), flat[index])
            )

    if coeff_shape is None or not entries:
        raise ValueError("No spectral coefficients were retained.")

    components = np.array(
        [entry[0] for entry in entries],
        dtype=np.int16,
    )
    indices = np.array(
        [entry[1] for entry in entries],
        dtype=np.int32,
    )
    coeffs = np.array(
        [entry[2] for entry in entries],
        dtype=np.complex128,
    )

    coefficient_norm = float(np.linalg.norm(coeffs))
    if coefficient_norm == 0.0:
        raise ValueError("Cannot normalize a zero coefficient vector.")

    cosine_raw = coeffs.real / coefficient_norm
    sine_raw = coeffs.imag / coefficient_norm

    harmonic_count = len(coeffs)
    if harmonic_count > curve_samples // 2:
        raise ValueError(
            "curve_render_samples is too small for the retained harmonics."
        )

    spectrum = np.zeros(
        curve_samples // 2 + 1,
        dtype=np.complex128,
    )
    spectrum[1 : harmonic_count + 1] = (
        curve_samples / 2.0
    ) * (cosine_raw - 1j * sine_raw)

    raw_series = np.fft.irfft(
        spectrum,
        n=curve_samples,
    )
    series_bound = float(np.max(np.abs(raw_series)))
    if series_bound == 0.0:
        raise ValueError("Cannot normalize a zero trigonometric series.")

    return {
        "components": components,
        "indices": indices,
        "coeffs": coeffs,
        "coeff_shape": coeff_shape,
        "coefficient_norm": coefficient_norm,
        "series_bound": series_bound,
        "cosine": cosine_raw / series_bound,
        "sine": sine_raw / series_bound,
        "curve_samples": curve_samples,
    }


def uniform_series(encoding: dict[str, Any]) -> np.ndarray:
    sample_count = int(encoding["curve_samples"])
    harmonic_count = len(encoding["coeffs"])

    spectrum = np.zeros(
        sample_count // 2 + 1,
        dtype=np.complex128,
    )
    spectrum[1 : harmonic_count + 1] = (
        sample_count / 2.0
    ) * (
        encoding["cosine"]
        - 1j * encoding["sine"]
    )
    return np.fft.irfft(
        spectrum,
        n=sample_count,
    )


def latitude_curve(
    encoding: dict[str, Any],
    hemisphere: str,
    cfg: SolverConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sample_count = int(encoding["curve_samples"])
    theta = (
        2.0
        * np.pi
        * np.arange(sample_count)
        / sample_count
    )

    scalar_series = uniform_series(encoding)
    offset = (
        cfg.latitude_center
        + cfg.latitude_amplitude
        * np.tanh(cfg.encoding_gain * scalar_series)
    )

    if hemisphere == "north":
        colatitude = offset
    elif hemisphere == "south":
        colatitude = np.pi - offset
    else:
        raise ValueError("hemisphere must be 'north' or 'south'.")

    radius = cfg.ball_radius
    points = radius * np.column_stack(
        [
            np.sin(colatitude) * np.cos(theta),
            np.sin(colatitude) * np.sin(theta),
            np.cos(colatitude),
        ]
    )

    return theta, colatitude, points


def recover_field_from_curve(
    colatitude: np.ndarray,
    hemisphere: str,
    encoding: dict[str, Any],
    grid_shape: tuple[int, int, int],
    cfg: SolverConfig,
) -> tuple[np.ndarray, np.ndarray]:
    if hemisphere == "north":
        normalized = (
            colatitude - cfg.latitude_center
        ) / cfg.latitude_amplitude
    elif hemisphere == "south":
        normalized = (
            (np.pi - colatitude)
            - cfg.latitude_center
        ) / cfg.latitude_amplitude
    else:
        raise ValueError("hemisphere must be 'north' or 'south'.")

    normalized = np.clip(
        normalized,
        -1.0 + 1e-14,
        1.0 - 1e-14,
    )
    scalar_series = (
        np.arctanh(normalized)
        / cfg.encoding_gain
    )

    sample_count = int(encoding["curve_samples"])
    harmonic_count = len(encoding["coeffs"])
    spectrum = np.fft.rfft(scalar_series)

    cosine_recovered = (
        2.0
        * spectrum[1 : harmonic_count + 1].real
        / sample_count
    )
    sine_recovered = (
        -2.0
        * spectrum[1 : harmonic_count + 1].imag
        / sample_count
    )

    coeffs_recovered = (
        encoding["coefficient_norm"]
        * encoding["series_bound"]
        * (cosine_recovered + 1j * sine_recovered)
    )

    coefficient_array_size = int(
        np.prod(encoding["coeff_shape"])
    )
    recovered_components: list[np.ndarray] = []

    for component in range(3):
        flat = np.zeros(
            coefficient_array_size,
            dtype=np.complex128,
        )
        component_mask = (
            encoding["components"] == component
        )
        flat[
            encoding["indices"][component_mask]
        ] = coeffs_recovered[component_mask]

        coefficient_array = flat.reshape(
            encoding["coeff_shape"]
        )
        recovered_components.append(
            np.fft.irfftn(
                coefficient_array,
                s=grid_shape,
                axes=(0, 1, 2),
                norm="ortho",
            )
        )

    field = np.stack(
        recovered_components,
        axis=-1,
    )
    return field, coeffs_recovered


def evaluate_trigonometric_series(
    parameter: np.ndarray,
    encoding: dict[str, Any],
    chunk_size: int = 1000,
) -> np.ndarray:
    parameter = np.asarray(parameter, dtype=float)
    harmonic_count = len(encoding["coeffs"])
    harmonics = np.arange(
        1,
        harmonic_count + 1,
        dtype=float,
    )

    output = np.empty_like(parameter)

    for start in range(0, len(parameter), chunk_size):
        stop = min(
            start + chunk_size,
            len(parameter),
        )
        angles = (
            parameter[start:stop, None]
            * harmonics[None, :]
        )
        output[start:stop] = (
            np.cos(angles) @ encoding["cosine"]
            + np.sin(angles) @ encoding["sine"]
        )

    return output


def evaluate_body_curve(
    parameter: np.ndarray,
    encoding: dict[str, Any],
    hemisphere: str,
    cfg: SolverConfig,
) -> np.ndarray:
    scalar_series = evaluate_trigonometric_series(
        parameter,
        encoding,
    )

    offset = (
        cfg.latitude_center
        + cfg.latitude_amplitude
        * np.tanh(cfg.encoding_gain * scalar_series)
    )

    if hemisphere == "north":
        colatitude = offset
    elif hemisphere == "south":
        colatitude = np.pi - offset
    else:
        raise ValueError("hemisphere must be 'north' or 'south'.")

    return cfg.ball_radius * np.column_stack(
        [
            np.sin(colatitude) * np.cos(parameter),
            np.sin(colatitude) * np.sin(parameter),
            np.cos(colatitude),
        ]
    )


def body_contact_frame(
    annulus_parameter: np.ndarray,
) -> np.ndarray:
    radial = np.column_stack(
        [
            np.sin(annulus_parameter),
            np.zeros_like(annulus_parameter),
            np.cos(annulus_parameter),
        ]
    )
    tangent = np.column_stack(
        [
            np.cos(annulus_parameter),
            np.zeros_like(annulus_parameter),
            -np.sin(annulus_parameter),
        ]
    )
    normal = np.tile(
        [0.0, 1.0, 0.0],
        (len(annulus_parameter), 1),
    )

    return np.stack(
        [radial, tangent, normal],
        axis=-1,
    )


def world_track_frame(
    toroidal_angle: np.ndarray,
) -> np.ndarray:
    radial = np.column_stack(
        [
            np.cos(toroidal_angle),
            np.sin(toroidal_angle),
            np.zeros_like(toroidal_angle),
        ]
    )
    tangent = np.column_stack(
        [
            -np.sin(toroidal_angle),
            np.cos(toroidal_angle),
            np.zeros_like(toroidal_angle),
        ]
    )
    normal = np.tile(
        [0.0, 0.0, 1.0],
        (len(toroidal_angle), 1),
    )

    return np.stack(
        [radial, tangent, normal],
        axis=-1,
    )


def minimal_rotation(
    vector_from: np.ndarray,
    vector_to: np.ndarray,
) -> np.ndarray:
    cross = np.cross(vector_from, vector_to)
    sine = np.linalg.norm(cross)
    cosine = np.clip(
        np.dot(vector_from, vector_to),
        -1.0,
        1.0,
    )

    if sine < 1e-12:
        if cosine > 0.0:
            return np.eye(3)

        reference = np.array(
            [1.0, 0.0, 0.0]
        )
        if abs(
            np.dot(reference, vector_from)
        ) > 0.9:
            reference = np.array(
                [0.0, 1.0, 0.0]
            )

        axis = np.cross(
            vector_from,
            reference,
        )
        axis /= np.linalg.norm(axis)
        return (
            -np.eye(3)
            + 2.0 * np.outer(axis, axis)
        )

    axis = cross / sine
    skew = np.array(
        [
            [0.0, -axis[2], axis[1]],
            [axis[2], 0.0, -axis[0]],
            [-axis[1], axis[0], 0.0],
        ]
    )
    angle = np.arctan2(sine, cosine)

    return (
        np.eye(3)
        + np.sin(angle) * skew
        + (1.0 - np.cos(angle)) * (skew @ skew)
    )


def bishop_frame(
    connector_direction: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    first_normal = np.zeros_like(
        connector_direction
    )
    second_normal = np.zeros_like(
        connector_direction
    )

    reference = np.array(
        [0.0, 0.0, 1.0]
    )
    if abs(
        np.dot(
            reference,
            connector_direction[0],
        )
    ) > 0.9:
        reference = np.array(
            [0.0, 1.0, 0.0]
        )

    first_normal[0] = (
        reference
        - np.dot(
            reference,
            connector_direction[0],
        )
        * connector_direction[0]
    )
    first_normal[0] /= np.linalg.norm(
        first_normal[0]
    )

    second_normal[0] = np.cross(
        connector_direction[0],
        first_normal[0],
    )
    second_normal[0] /= np.linalg.norm(
        second_normal[0]
    )

    for index in range(
        1,
        len(connector_direction),
    ):
        rotation = minimal_rotation(
            connector_direction[index - 1],
            connector_direction[index],
        )
        candidate = (
            rotation @ first_normal[index - 1]
        )
        candidate -= (
            np.dot(
                candidate,
                connector_direction[index],
            )
            * connector_direction[index]
        )

        norm = np.linalg.norm(candidate)
        if norm < 1e-12:
            candidate = (
                first_normal[index - 1]
                - np.dot(
                    first_normal[index - 1],
                    connector_direction[index],
                )
                * connector_direction[index]
            )
            norm = np.linalg.norm(candidate)

        first_normal[index] = candidate / norm
        second_normal[index] = np.cross(
            connector_direction[index],
            first_normal[index],
        )
        second_normal[index] /= np.linalg.norm(
            second_normal[index]
        )

    return first_normal, second_normal


def torus_implicit(
    points: np.ndarray,
    cfg: SolverConfig,
) -> np.ndarray:
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    major = cfg.torus_major_radius
    minor = cfg.torus_minor_radius

    return (
        (
            x * x
            + y * y
            + z * z
            + major * major
            - minor * minor
        )
        ** 2
        - 4.0
        * major
        * major
        * (x * x + y * y)
    )


def first_forward_torus_intersection(
    origin: np.ndarray,
    direction: np.ndarray,
    cfg: SolverConfig,
) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Find the first forward ray intersection with the torus wall.

    The ray origin is inside the torus tube, so the first sign change of the
    torus implicit function selects the physically adjacent wall.
    """
    count = len(origin)
    lower = np.zeros(count)
    upper = np.full(
        count,
        2.0 * cfg.torus_minor_radius + 0.25,
    )

    for _ in range(12):
        outside_test = torus_implicit(
            origin + upper[:, None] * direction,
            cfg,
        )
        needs_expansion = outside_test <= 0.0

        if not np.any(needs_expansion):
            break

        upper[needs_expansion] *= 1.7

    bracket_failures = int(
        np.sum(
            torus_implicit(
                origin + upper[:, None] * direction,
                cfg,
            )
            <= 0.0
        )
    )

    for _ in range(52):
        midpoint = 0.5 * (lower + upper)
        midpoint_value = torus_implicit(
            origin + midpoint[:, None] * direction,
            cfg,
        )
        still_inside = midpoint_value <= 0.0

        lower[still_inside] = midpoint[still_inside]
        upper[~still_inside] = midpoint[~still_inside]

    ray_parameter = 0.5 * (lower + upper)
    intersection = (
        origin
        + ray_parameter[:, None] * direction
    )

    return intersection, ray_parameter, bracket_failures


def relative_l2(
    reference: np.ndarray,
    candidate: np.ndarray,
) -> float:
    return float(
        np.linalg.norm(reference - candidate)
        / np.linalg.norm(reference)
    )


def solve(
    cfg: SolverConfig,
) -> dict[str, Any]:
    x, y, z, u_a, u_b = build_trial_fields(cfg)
    grid_shape = (
        cfg.nx,
        cfg.ny,
        cfg.nz,
    )

    encoding_a = sparse_spectral_encoding(
        u_a,
        cfg.curve_render_samples,
    )
    encoding_b = sparse_spectral_encoding(
        u_b,
        cfg.curve_render_samples,
    )

    (
        theta_a,
        colatitude_a,
        curve_a_display,
    ) = latitude_curve(
        encoding_a,
        "north",
        cfg,
    )
    (
        theta_b,
        colatitude_b,
        curve_b_display,
    ) = latitude_curve(
        encoding_b,
        "south",
        cfg,
    )

    u_a_recovered, _ = recover_field_from_curve(
        colatitude_a,
        "north",
        encoding_a,
        grid_shape,
        cfg,
    )
    u_b_recovered, _ = recover_field_from_curve(
        colatitude_b,
        "south",
        encoding_b,
        grid_shape,
        cfg,
    )

    tau = np.linspace(
        0.0,
        cfg.tau_end,
        cfg.n_eval,
    )
    psi = tau

    rolling_ratio = (
        cfg.torus_major_radius
        + cfg.ball_radius
    ) / cfg.ball_radius
    annulus_parameter = (
        -rolling_ratio * psi
    )

    alpha = (
        cfg.alpha_linear_rate * tau
        + cfg.alpha_modulation_amplitude
        * np.sin(
            cfg.alpha_modulation_frequency
            * tau
        )
    )
    beta = (
        cfg.beta_linear_rate * tau
        + cfg.beta_modulation_amplitude
        * np.sin(
            cfg.beta_modulation_frequency
            * tau
        )
        + cfg.beta_phase_offset
    )

    center = np.column_stack(
        [
            cfg.torus_major_radius
            * np.cos(psi),
            cfg.torus_major_radius
            * np.sin(psi),
            np.zeros_like(psi),
        ]
    )
    pin = np.column_stack(
        [
            (
                cfg.torus_major_radius
                + cfg.ball_radius
            )
            * np.cos(psi),
            (
                cfg.torus_major_radius
                + cfg.ball_radius
            )
            * np.sin(psi),
            np.zeros_like(psi),
        ]
    )

    body_frame = body_contact_frame(
        annulus_parameter
    )
    world_frame = world_track_frame(psi)

    orientation = np.einsum(
        "nij,nkj->nik",
        world_frame,
        body_frame,
    )

    active_a_body = evaluate_body_curve(
        alpha,
        encoding_a,
        "north",
        cfg,
    )
    active_b_body = evaluate_body_curve(
        beta,
        encoding_b,
        "south",
        cfg,
    )

    endpoint_a = (
        center
        + np.einsum(
            "nij,nj->ni",
            orientation,
            active_a_body,
        )
    )
    endpoint_b = (
        center
        + np.einsum(
            "nij,nj->ni",
            orientation,
            active_b_body,
        )
    )

    connector = endpoint_b - endpoint_a
    connector_length = np.linalg.norm(
        connector,
        axis=1,
    )
    connector_direction = (
        connector / connector_length[:, None]
    )
    connector_midpoint = (
        0.5 * (endpoint_a + endpoint_b)
    )

    normal_1, normal_2 = bishop_frame(
        connector_direction
    )

    pen_phase = (
        cfg.pen_angular_rate * tau
    )
    pen_direction = (
        np.cos(pen_phase)[:, None] * normal_1
        + np.sin(pen_phase)[:, None] * normal_2
    )
    pen_direction /= np.linalg.norm(
        pen_direction,
        axis=1,
    )[:, None]

    (
        output_curve,
        ray_parameter,
        bracket_failures,
    ) = first_forward_torus_intersection(
        connector_midpoint,
        pen_direction,
        cfg,
    )

    annulus_midpoint = (
        cfg.ball_radius
        * np.column_stack(
            [
                np.sin(annulus_parameter),
                np.zeros_like(annulus_parameter),
                np.cos(annulus_parameter),
            ]
        )
    )
    pin_from_ball = (
        center
        + np.einsum(
            "nij,nj->ni",
            orientation,
            annulus_midpoint,
        )
    )

    pin_residual = np.linalg.norm(
        pin_from_ball - pin,
        axis=1,
    )
    qtq = np.einsum(
        "nji,njk->nik",
        orientation,
        orientation,
    )
    rotation_residual = np.max(
        np.abs(qtq - np.eye(3)),
        axis=(1, 2),
    )
    torus_residual = np.abs(
        torus_implicit(output_curve, cfg)
    )
    frame_residual = np.maximum.reduce(
        [
            np.abs(
                np.sum(
                    connector_direction
                    * normal_1,
                    axis=1,
                )
            ),
            np.abs(
                np.sum(
                    connector_direction
                    * normal_2,
                    axis=1,
                )
            ),
            np.abs(
                np.sum(
                    normal_1 * normal_2,
                    axis=1,
                )
            ),
        ]
    )

    diagnostics = {
        "mechanics_frozen_from_v1": True,
        "minimum_curvature_optimization": False,
        "encoding_object": (
            "sparse Fourier representation followed by a "
            "one-dimensional trigonometric polynomial"
        ),
        "A_retained_complex_coefficients": int(
            len(encoding_a["coeffs"])
        ),
        "B_retained_complex_coefficients": int(
            len(encoding_b["coeffs"])
        ),
        "A_field_relative_reconstruction_error": relative_l2(
            u_a,
            u_a_recovered,
        ),
        "B_field_relative_reconstruction_error": relative_l2(
            u_b,
            u_b_recovered,
        ),
        "A_field_max_abs_reconstruction_error": float(
            np.max(np.abs(u_a - u_a_recovered))
        ),
        "B_field_max_abs_reconstruction_error": float(
            np.max(np.abs(u_b - u_b_recovered))
        ),
        "continuous_solver_evaluations": int(
            cfg.n_eval
        ),
        "max_pin_residual": float(
            pin_residual.max()
        ),
        "max_rotation_residual": float(
            rotation_residual.max()
        ),
        "max_torus_residual": float(
            torus_residual.max()
        ),
        "max_frame_residual": float(
            frame_residual.max()
        ),
        "minimum_connector_length": float(
            connector_length.min()
        ),
        "ray_origins_inside_tube_fraction": float(
            np.mean(
                torus_implicit(
                    connector_midpoint,
                    cfg,
                )
                <= 1e-10
            )
        ),
        "ray_bracket_failures": bracket_failures,
    }

    return {
        "config": cfg,
        "diagnostics": diagnostics,
        "x": x,
        "y": y,
        "z": z,
        "u_a": u_a,
        "u_b": u_b,
        "encoding_a": encoding_a,
        "encoding_b": encoding_b,
        "theta_a": theta_a,
        "theta_b": theta_b,
        "curve_a_display": curve_a_display,
        "curve_b_display": curve_b_display,
        "tau": tau,
        "alpha": alpha,
        "beta": beta,
        "center": center,
        "orientation": orientation,
        "endpoint_a": endpoint_a,
        "endpoint_b": endpoint_b,
        "connector_direction": connector_direction,
        "normal_1": normal_1,
        "normal_2": normal_2,
        "pen_phase": pen_phase,
        "ray_parameter": ray_parameter,
        "output_curve": output_curve,
    }


def save_solution(
    result: dict[str, Any],
    output_directory: Path,
) -> None:
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    cfg: SolverConfig = result["config"]
    encoding_a = result["encoding_a"]
    encoding_b = result["encoding_b"]

    (
        output_directory / "diagnostics.json"
    ).write_text(
        json.dumps(
            {
                "config": asdict(cfg),
                "diagnostics": result["diagnostics"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    np.savez_compressed(
        output_directory / "solution.npz",
        x=result["x"],
        y=result["y"],
        z=result["z"],
        uA=result["u_a"],
        uB=result["u_b"],
        thetaA=result["theta_a"],
        thetaB=result["theta_b"],
        A_display=result["curve_a_display"],
        B_display=result["curve_b_display"],
        tau=result["tau"],
        alpha=result["alpha"],
        beta=result["beta"],
        C=result["center"],
        Q=result["orientation"],
        a=result["endpoint_a"],
        b=result["endpoint_b"],
        d=result["connector_direction"],
        n1=result["normal_1"],
        n2=result["normal_2"],
        phi=result["pen_phase"],
        mu=result["ray_parameter"],
        Gamma=result["output_curve"],
        A_components=encoding_a["components"],
        A_indices=encoding_a["indices"],
        A_coeffs=encoding_a["coeffs"],
        A_encoding_cosine=encoding_a["cosine"],
        A_encoding_sine=encoding_a["sine"],
        B_components=encoding_b["components"],
        B_indices=encoding_b["indices"],
        B_coeffs=encoding_b["coeffs"],
        B_encoding_cosine=encoding_b["cosine"],
        B_encoding_sine=encoding_b["sine"],
    )


def save_flattened_torus_curve(
    result: dict[str, Any],
    output_directory: Path,
) -> None:
    cfg: SolverConfig = result["config"]
    gamma = result["output_curve"]

    x = gamma[:, 0]
    y = gamma[:, 1]
    z = gamma[:, 2]

    major_angle = np.unwrap(
        np.arctan2(y, x)
    )
    cylindrical_radius = np.sqrt(
        x * x + y * y
    )
    minor_angle = np.arctan2(
        z,
        cylindrical_radius
        - cfg.torus_major_radius,
    )

    major_arclength = (
        cfg.torus_major_radius
        * major_angle
    )
    minor_arclength = (
        cfg.torus_minor_radius
        * minor_angle
    )

    np.savetxt(
        output_directory
        / "flattened_torus_curve.csv",
        np.column_stack(
            [
                major_angle,
                minor_angle,
                major_arclength,
                minor_arclength,
            ]
        ),
        delimiter=",",
        header=(
            "u_angle,v_angle,"
            "U_major_arclength,"
            "V_minor_arclength"
        ),
        comments="",
    )


def save_diagnostic_figure(
    result: dict[str, Any],
    output_directory: Path,
) -> None:
    import matplotlib.pyplot as plt

    cfg: SolverConfig = result["config"]
    curve_a = result["curve_a_display"]
    curve_b = result["curve_b_display"]
    gamma = result["output_curve"]
    tau = result["tau"]

    torus_residual = np.abs(
        torus_implicit(gamma, cfg)
    )

    u = np.linspace(0.0, 2.0 * np.pi, 64)
    v = np.linspace(0.0, 2.0 * np.pi, 22)
    U, V = np.meshgrid(u, v)
    x_torus = (
        cfg.torus_major_radius
        + cfg.torus_minor_radius * np.cos(V)
    ) * np.cos(U)
    y_torus = (
        cfg.torus_major_radius
        + cfg.torus_minor_radius * np.cos(V)
    ) * np.sin(U)
    z_torus = (
        cfg.torus_minor_radius * np.sin(V)
    )

    figure = plt.figure(
        figsize=(13.0, 5.4)
    )
    axis_1 = figure.add_subplot(
        131,
        projection="3d",
    )
    axis_2 = figure.add_subplot(
        132,
        projection="3d",
    )
    axis_3 = figure.add_subplot(133)

    axis_1.plot(
        curve_a[::2, 0],
        curve_a[::2, 1],
        curve_a[::2, 2],
        linewidth=0.55,
        label="A",
    )
    axis_1.plot(
        curve_b[::2, 0],
        curve_b[::2, 1],
        curve_b[::2, 2],
        linewidth=0.55,
        label="B",
    )
    axis_1.set_title(
        "Invertible spectral input curves"
    )
    axis_1.legend(fontsize=8)
    axis_1.set_box_aspect((1, 1, 1))
    axis_1.view_init(24, 38)

    axis_2.plot_wireframe(
        x_torus,
        y_torus,
        z_torus,
        linewidth=0.22,
        alpha=0.10,
    )
    axis_2.plot(
        gamma[::3, 0],
        gamma[::3, 1],
        gamma[::3, 2],
        linewidth=0.65,
    )
    axis_2.set_title(
        "Continuous torus output"
    )
    axis_2.set_box_aspect(
        (1, 1, 0.55)
    )
    axis_2.view_init(27, 36)

    axis_3.plot(
        tau[::10],
        torus_residual[::10],
    )
    axis_3.set_yscale("log")
    axis_3.set_xlabel(r"$\tau$")
    axis_3.set_title(
        "Torus contact residual"
    )

    figure.tight_layout()
    figure.savefig(
        output_directory
        / "continuous_ns_diagnostics.png",
        dpi=150,
    )
    plt.close(figure)


def save_flattened_curve_figure(
    result: dict[str, Any],
    output_directory: Path,
) -> None:
    import matplotlib.pyplot as plt

    cfg: SolverConfig = result["config"]
    gamma = result["output_curve"]

    x = gamma[:, 0]
    y = gamma[:, 1]
    z = gamma[:, 2]

    major_angle = np.unwrap(
        np.arctan2(y, x)
    )
    cylindrical_radius = np.sqrt(
        x * x + y * y
    )
    minor_angle = np.arctan2(
        z,
        cylindrical_radius
        - cfg.torus_major_radius,
    )

    major_arclength = (
        cfg.torus_major_radius
        * major_angle
    )
    minor_arclength = (
        cfg.torus_minor_radius
        * minor_angle
    )

    figure = plt.figure(
        figsize=(9.0, 5.5)
    )
    axis = figure.add_subplot(111)
    axis.plot(
        major_arclength,
        minor_arclength,
        linewidth=0.8,
    )
    axis.set_xlabel(
        "Major-circle coordinate U = R·u"
    )
    axis.set_ylabel(
        "Minor-circle coordinate V = r·v"
    )
    axis.set_title(
        "Composite curve on flattened torus"
    )
    figure.tight_layout()
    figure.savefig(
        output_directory
        / "flattened_torus_composite_curve.png",
        dpi=160,
    )
    plt.close(figure)


def save_animation(
    result: dict[str, Any],
    output_directory: Path,
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.animation import (
        FuncAnimation,
        PillowWriter,
    )

    cfg: SolverConfig = result["config"]
    tau = result["tau"]
    center = result["center"]
    orientation = result["orientation"]
    endpoint_a = result["endpoint_a"]
    endpoint_b = result["endpoint_b"]
    output_curve = result["output_curve"]
    curve_a = result["curve_a_display"][::2]
    curve_b = result["curve_b_display"][::2]

    connector_midpoint = (
        0.5 * (endpoint_a + endpoint_b)
    )
    psi = tau
    pin = np.column_stack(
        [
            (
                cfg.torus_major_radius
                + cfg.ball_radius
            )
            * np.cos(psi),
            (
                cfg.torus_major_radius
                + cfg.ball_radius
            )
            * np.sin(psi),
            np.zeros_like(psi),
        ]
    )

    annulus_parameter = np.linspace(
        0.0,
        2.0 * np.pi,
        320,
    )
    annulus_midline = (
        cfg.ball_radius
        * np.column_stack(
            [
                np.sin(annulus_parameter),
                np.zeros_like(
                    annulus_parameter
                ),
                np.cos(annulus_parameter),
            ]
        )
    )
    annulus_width = (
        0.62
        * np.sin(
            (
                annulus_parameter
                - np.pi
            )
            / 2.0
        )
        ** 2
    )

    def rotate_body_z(
        points: np.ndarray,
        angle: np.ndarray,
    ) -> np.ndarray:
        cosine = np.cos(angle)
        sine = np.sin(angle)
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        return np.column_stack(
            [
                cosine * x - sine * y,
                sine * x + cosine * y,
                z,
            ]
        )

    annulus_upper = rotate_body_z(
        annulus_midline,
        annulus_width,
    )
    annulus_lower = rotate_body_z(
        annulus_midline,
        -annulus_width,
    )

    u = np.linspace(
        0.0,
        2.0 * np.pi,
        36,
    )
    v = np.linspace(
        0.0,
        2.0 * np.pi,
        14,
    )
    U, V = np.meshgrid(u, v)
    x_torus = (
        cfg.torus_major_radius
        + cfg.torus_minor_radius * np.cos(V)
    ) * np.cos(U)
    y_torus = (
        cfg.torus_major_radius
        + cfg.torus_minor_radius * np.cos(V)
    ) * np.sin(U)
    z_torus = (
        cfg.torus_minor_radius * np.sin(V)
    )

    sphere_u = np.linspace(
        0.0,
        2.0 * np.pi,
        18,
    )
    sphere_v = np.linspace(
        0.0,
        np.pi,
        9,
    )
    sphere_U, sphere_V = np.meshgrid(
        sphere_u,
        sphere_v,
    )
    sphere_body = np.stack(
        [
            cfg.ball_radius
            * np.cos(sphere_U)
            * np.sin(sphere_V),
            cfg.ball_radius
            * np.sin(sphere_U)
            * np.sin(sphere_V),
            cfg.ball_radius
            * np.cos(sphere_V),
        ],
        axis=-1,
    )

    figure = plt.figure(
        figsize=(11.0, 6.0)
    )
    axis_full = figure.add_subplot(
        121,
        projection="3d",
    )
    axis_close = figure.add_subplot(
        122,
        projection="3d",
    )

    for axis in (
        axis_full,
        axis_close,
    ):
        axis.plot_wireframe(
            x_torus,
            y_torus,
            z_torus,
            linewidth=0.22,
            alpha=0.09,
        )

    outer = np.linspace(
        0.0,
        2.0 * np.pi,
        320,
    )
    axis_full.plot(
        (
            cfg.torus_major_radius
            + cfg.ball_radius
        )
        * np.cos(outer),
        (
            cfg.torus_major_radius
            + cfg.ball_radius
        )
        * np.sin(outer),
        np.zeros_like(outer),
        linestyle="--",
        linewidth=1.0,
        label="pin track",
    )

    sphere_artists: list[Any] = [
        None,
        None,
    ]

    curve_a_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=0.70,
        label="spectral A",
    )
    curve_b_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=0.70,
        label="spectral B",
    )
    annulus_upper_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=2.2,
        label="annulus",
    )
    annulus_lower_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=2.2,
    )
    connector_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=1.8,
        label="connector",
    )
    pen_ray_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=1.5,
        label="pen ray",
    )
    trace_full, = axis_full.plot(
        [],
        [],
        [],
        linewidth=1.0,
        label="torus trace",
    )
    pin_full, = axis_full.plot(
        [],
        [],
        [],
        marker="o",
        linestyle="None",
    )
    draw_full, = axis_full.plot(
        [],
        [],
        [],
        marker="o",
        linestyle="None",
    )

    curve_a_close, = axis_close.plot(
        [],
        [],
        [],
        linewidth=0.9,
    )
    curve_b_close, = axis_close.plot(
        [],
        [],
        [],
        linewidth=0.9,
    )
    annulus_upper_close, = axis_close.plot(
        [],
        [],
        [],
        linewidth=2.7,
    )
    annulus_lower_close, = axis_close.plot(
        [],
        [],
        [],
        linewidth=2.7,
    )
    connector_close, = axis_close.plot(
        [],
        [],
        [],
        linewidth=2.4,
    )
    pen_ray_close, = axis_close.plot(
        [],
        [],
        [],
        linewidth=1.9,
    )
    pin_close, = axis_close.plot(
        [],
        [],
        [],
        marker="o",
        linestyle="None",
    )
    draw_close, = axis_close.plot(
        [],
        [],
        [],
        marker="o",
        linestyle="None",
    )

    axis_full.set_title(
        "Continuous spectral Navier–Stokes Whirligig"
    )
    axis_full.legend(
        loc="upper left",
        fontsize=8,
    )
    axis_full.set_xlim(-2.35, 2.35)
    axis_full.set_ylim(-2.35, 2.35)
    axis_full.set_zlim(-1.2, 1.2)
    axis_full.set_box_aspect(
        (1, 1, 0.55)
    )
    axis_full.view_init(27, 35)

    axis_close.set_title(
        "Connector sweep and true torus contact"
    )
    axis_close.set_box_aspect(
        (1, 1, 1)
    )
    axis_close.view_init(18, 42)

    def set_line(
        line: Any,
        points: np.ndarray,
    ) -> None:
        line.set_data(
            points[:, 0],
            points[:, 1],
        )
        line.set_3d_properties(
            points[:, 2]
        )

    frame_indices = np.linspace(
        0,
        len(tau) - 1,
        64,
    ).astype(int)

    def update(frame: int) -> tuple[Any, ...]:
        index = frame_indices[frame]
        current_orientation = (
            orientation[index]
        )
        current_center = center[index]

        curve_a_world = (
            current_center
            + curve_a
            @ current_orientation.T
        )
        curve_b_world = (
            current_center
            + curve_b
            @ current_orientation.T
        )
        annulus_upper_world = (
            current_center
            + annulus_upper
            @ current_orientation.T
        )
        annulus_lower_world = (
            current_center
            + annulus_lower
            @ current_orientation.T
        )

        for line, points in (
            (
                curve_a_full,
                curve_a_world,
            ),
            (
                curve_b_full,
                curve_b_world,
            ),
            (
                annulus_upper_full,
                annulus_upper_world,
            ),
            (
                annulus_lower_full,
                annulus_lower_world,
            ),
            (
                curve_a_close,
                curve_a_world,
            ),
            (
                curve_b_close,
                curve_b_world,
            ),
            (
                annulus_upper_close,
                annulus_upper_world,
            ),
            (
                annulus_lower_close,
                annulus_lower_world,
            ),
        ):
            set_line(line, points)

        active_a = endpoint_a[index]
        active_b = endpoint_b[index]
        midpoint = connector_midpoint[index]
        draw_point = output_curve[index]
        current_pin = pin[index]

        for line in (
            connector_full,
            connector_close,
        ):
            line.set_data(
                [active_a[0], active_b[0]],
                [active_a[1], active_b[1]],
            )
            line.set_3d_properties(
                [active_a[2], active_b[2]]
            )

        for line in (
            pen_ray_full,
            pen_ray_close,
        ):
            line.set_data(
                [midpoint[0], draw_point[0]],
                [midpoint[1], draw_point[1]],
            )
            line.set_3d_properties(
                [midpoint[2], draw_point[2]]
            )

        history = np.linspace(
            0,
            index,
            min(3500, index + 1),
        ).astype(int)
        set_line(
            trace_full,
            output_curve[history],
        )

        for point_artist in (
            pin_full,
            pin_close,
        ):
            point_artist.set_data(
                [current_pin[0]],
                [current_pin[1]],
            )
            point_artist.set_3d_properties(
                [current_pin[2]]
            )

        for point_artist in (
            draw_full,
            draw_close,
        ):
            point_artist.set_data(
                [draw_point[0]],
                [draw_point[1]],
            )
            point_artist.set_3d_properties(
                [draw_point[2]]
            )

        for slot, axis in enumerate(
            (axis_full, axis_close)
        ):
            if sphere_artists[slot] is not None:
                sphere_artists[slot].remove()

            sphere_world = (
                sphere_body
                @ current_orientation.T
                + current_center
            )
            sphere_artists[slot] = (
                axis.plot_wireframe(
                    sphere_world[..., 0],
                    sphere_world[..., 1],
                    sphere_world[..., 2],
                    linewidth=0.22,
                    alpha=0.18,
                )
            )

        axis_close.set_xlim(
            current_center[0] - 0.82,
            current_center[0] + 0.82,
        )
        axis_close.set_ylim(
            current_center[1] - 0.82,
            current_center[1] + 0.82,
        )
        axis_close.set_zlim(-0.82, 0.82)

        axis_full.view_init(
            27,
            35 + 0.16 * frame,
        )
        axis_close.view_init(
            18,
            42 + 0.40 * frame,
        )

        return (
            curve_a_full,
            curve_b_full,
            annulus_upper_full,
            annulus_lower_full,
            connector_full,
            pen_ray_full,
            trace_full,
            pin_full,
            draw_full,
            curve_a_close,
            curve_b_close,
            annulus_upper_close,
            annulus_lower_close,
            connector_close,
            pen_ray_close,
            pin_close,
            draw_close,
        )

    animation = FuncAnimation(
        figure,
        update,
        frames=len(frame_indices),
        interval=90,
        blit=False,
    )
    animation.save(
        output_directory
        / "continuous_ns_whirligig.gif",
        writer=PillowWriter(fps=10),
        dpi=68,
    )
    plt.close(figure)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the current continuous spectral "
            "Navier–Stokes Whirligig solver."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "continuous_ns_whirligig_output"
        ),
    )
    parser.add_argument(
        "--n-eval",
        type=int,
        default=16_000,
        help=(
            "Numerical evaluation count for the "
            "continuous solver."
        ),
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Skip GIF generation.",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    # Keep Matplotlib cache out of read-only home directories.
    os.environ.setdefault(
        "MPLCONFIGDIR",
        "/tmp",
    )

    config = SolverConfig(
        n_eval=arguments.n_eval,
    )
    result = solve(config)

    save_solution(
        result,
        arguments.output_dir,
    )
    save_flattened_torus_curve(
        result,
        arguments.output_dir,
    )
    save_diagnostic_figure(
        result,
        arguments.output_dir,
    )
    save_flattened_curve_figure(
        result,
        arguments.output_dir,
    )

    if not arguments.no_animation:
        save_animation(
            result,
            arguments.output_dir,
        )

    print(
        json.dumps(
            result["diagnostics"],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
