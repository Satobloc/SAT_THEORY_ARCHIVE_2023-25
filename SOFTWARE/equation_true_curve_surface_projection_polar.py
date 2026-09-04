
#!/usr/bin/env python3
"""
equation_true_curve_surface_projection_polar.py

ACTION PLAN IMPLEMENTATION:
equation -> actual output curve -> arclength curve -> intrinsic sphere/torus projection -> render/export.

Default test equation:
    (x**2 + y**2 - 1)**3 - x**2*y**3 = 0

Core rules:
    - Sphere and torus are clean carriers only.
    - Equation data lives in curves and exported data tables.
    - Surface meshes are not deformed and not data-colored.
    - Exact on-surface curves are data.
    - Display-offset curves are render-only and excluded from reconstruction.
    - Projection modes are compared:
        arclength_y
        arclength_curvature
        arclength_gradient
        arclength_radius
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import json
import math
import zipfile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sympy as sp


# -----------------------------
# CONFIG
# -----------------------------

@dataclass
class Config:
    equation: str = "(x**2 + y**2 - 1)**3 - x**2*y**3 = 0"
    outdir: str = "equation_true_curve_surface_projection_polar_output"

    x_range: Tuple[float, float] = (-1.6, 1.6)
    y_range: Tuple[float, float] = (-1.4, 1.8)

    grid_nx: int = 1100
    grid_ny: int = 1100
    min_branch_points: int = 40
    resample_points_per_branch: int = 3600

    sphere_radius: float = 0.5
    torus_major_radius: float = 1.0
    torus_minor_radius: float = 0.5

    winding_count: int = 2
    sphere_theta_base: float = math.pi / 2.0
    sphere_theta_amplitude: float = 1.18
    sphere_polar_margin: float = 0.10
    exact_line_width: float = 0.75
    display_line_width: float = 2.65

    surface_u: int = 240
    surface_v: int = 160

    display_offset_sphere: float = 0.035
    display_offset_torus: float = 0.045

    dpi: int = 210
    residual_tolerance_warning: float = 5e-3
    reconstruction_tolerance: float = 1e-10


# -----------------------------
# STAGE 1: INPUT + RESIDUAL
# -----------------------------

def parse_equation(eq_string: str):
    x, y = sp.symbols("x y")
    locals_ = {
        "x": x, "y": y,
        "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "exp": sp.exp, "log": sp.log, "sqrt": sp.sqrt,
        "pi": sp.pi, "Abs": sp.Abs,
    }
    if "=" in eq_string:
        left, right = eq_string.split("=", 1)
        F = sp.sympify(left, locals=locals_) - sp.sympify(right, locals=locals_)
    else:
        F = sp.sympify(eq_string, locals=locals_)
    F = sp.simplify(F)
    f_np = sp.lambdify((x, y), F, "numpy")
    dFx = sp.diff(F, x)
    dFy = sp.diff(F, y)
    dFx_np = sp.lambdify((x, y), dFx, "numpy")
    dFy_np = sp.lambdify((x, y), dFy, "numpy")
    return x, y, F, f_np, dFx_np, dFy_np


# -----------------------------
# STAGE 2: SOURCE CURVE EXTRACTION
# -----------------------------

def evaluate_grid(cfg: Config, f_np):
    xs = np.linspace(cfg.x_range[0], cfg.x_range[1], cfg.grid_nx)
    ys = np.linspace(cfg.y_range[0], cfg.y_range[1], cfg.grid_ny)
    X, Y = np.meshgrid(xs, ys, indexing="xy")
    with np.errstate(all="ignore"):
        Z = np.asarray(f_np(X, Y), dtype=float)
    Z = np.nan_to_num(Z, nan=np.inf, posinf=np.inf, neginf=-np.inf)
    return xs, ys, X, Y, Z

def extract_zero_contours(X, Y, Z, min_branch_points: int):
    fig, ax = plt.subplots()
    cs = ax.contour(X, Y, Z, levels=[0.0])
    branches = []
    for seg in cs.allsegs[0]:
        if seg is None or len(seg) < min_branch_points:
            continue
        branches.append(np.asarray(seg, dtype=float))
    plt.close(fig)

    unique = []
    seen = set()
    for seg in branches:
        key = (round(float(seg[0,0]), 8), round(float(seg[0,1]), 8), len(seg))
        if key not in seen:
            seen.add(key)
            unique.append(seg)
    return unique


# -----------------------------
# STAGE 3: ARCLENGTH PARAMETERIZATION
# -----------------------------

def polyline_arclength(points: np.ndarray):
    if len(points) < 2:
        return np.array([0.0])
    diffs = np.diff(points, axis=0)
    seglen = np.sqrt((diffs**2).sum(axis=1))
    return np.concatenate([[0.0], np.cumsum(seglen)])

def resample_by_arclength(points: np.ndarray, n_samples: int):
    s = polyline_arclength(points)
    total = float(s[-1])
    if total <= 1e-15:
        raise ValueError("Degenerate zero-arclength branch")
    target = np.linspace(0.0, total, n_samples)
    x = np.interp(target, s, points[:, 0])
    y = np.interp(target, s, points[:, 1])
    s_norm = target / total
    return np.column_stack([x, y]), s_norm, total


# -----------------------------
# STAGE 4: CURVE CHANNELS
# -----------------------------

def eval_np_func(func, x, y):
    with np.errstate(all="ignore"):
        val = np.asarray(func(x, y), dtype=float)
    if val.shape == ():
        val = np.full_like(x, float(val))
    return np.nan_to_num(val, nan=0.0, posinf=0.0, neginf=0.0)

def curve_curvature(x: np.ndarray, y: np.ndarray, s_norm: np.ndarray):
    # Derivatives with respect to normalized arclength parameter.
    eps = 1e-12
    dx = np.gradient(x, s_norm + eps)
    dy = np.gradient(y, s_norm + eps)
    ddx = np.gradient(dx, s_norm + eps)
    ddy = np.gradient(dy, s_norm + eps)
    denom = (dx*dx + dy*dy)**1.5
    kappa = np.abs(dx*ddy - dy*ddx) / np.maximum(denom, 1e-12)
    return np.nan_to_num(kappa, nan=0.0, posinf=0.0, neginf=0.0)

def normalize_channel(q: np.ndarray):
    q = np.asarray(q, dtype=float)
    finite = np.isfinite(q)
    if not np.any(finite):
        return np.zeros_like(q), True
    mn = float(np.min(q[finite]))
    mx = float(np.max(q[finite]))
    if abs(mx - mn) < 1e-14:
        return np.full_like(q, 0.5), True
    return (q - mn) / (mx - mn), False

def compute_channels(branch_xy: np.ndarray, s_norm: np.ndarray, f_np, dFx_np, dFy_np):
    x = branch_xy[:, 0]
    y = branch_xy[:, 1]
    F = eval_np_func(f_np, x, y)
    dFx = eval_np_func(dFx_np, x, y)
    dFy = eval_np_func(dFy_np, x, y)
    grad_norm = np.sqrt(dFx*dFx + dFy*dFy)
    curvature = curve_curvature(x, y, s_norm)
    radius = np.sqrt(x*x + y*y)
    channels = {
        "x": x,
        "y": y,
        "F": F,
        "curvature": curvature,
        "gradient": grad_norm,
        "radius": radius,
    }
    normalized = {}
    degenerate = {}
    for name in ["y", "curvature", "gradient", "radius"]:
        normalized[name], degenerate[name] = normalize_channel(channels[name])
    return channels, normalized, degenerate


# -----------------------------
# STAGE 5/6: INTRINSIC PROJECTIONS + EMBEDDING
# -----------------------------

PROJECTION_MODES = {
    "arclength_y": "y",
    "arclength_curvature": "curvature",
    "arclength_gradient": "gradient",
    "arclength_radius": "radius",
}

def sphere_embed(r, phi, theta):
    return np.column_stack([
        r*np.sin(theta)*np.cos(phi),
        r*np.sin(theta)*np.sin(phi),
        r*np.cos(theta)
    ])

def torus_embed(R, r, u, v):
    return np.column_stack([
        (R+r*np.cos(v))*np.cos(u),
        (R+r*np.cos(v))*np.sin(u),
        r*np.sin(v)
    ])

def intrinsic_projection(cfg: Config, s_norm: np.ndarray, q_norm: np.ndarray, mode_name: str, branch_id: int = 0):
    """
    Polar hemisphere sphere projection.

    The source curve is treated as a polar trace on one hemisphere:
        phi(s) = azimuth from arclength
        theta(Q) = polar radius from the pole toward the equator

    branch_id alternates hemispheres:
        even branch_id -> north hemisphere
        odd branch_id  -> south hemisphere

    This leaves the opposite hemisphere available for a second branch/projection.
    """
    phi = 2*np.pi*cfg.winding_count*s_norm

    # Polar radius on one hemisphere. Q=0 near pole, Q=1 near equator.
    theta_north = cfg.sphere_polar_margin + q_norm*((np.pi/2.0) - cfg.sphere_polar_margin)

    if branch_id % 2 == 0:
        hemisphere = "north"
        theta = theta_north
    else:
        hemisphere = "south"
        theta = np.pi - theta_north

    u = 2*np.pi*cfg.winding_count*s_norm
    v = 2*np.pi*q_norm

    sphere_xyz = sphere_embed(cfg.sphere_radius, phi, theta)
    torus_xyz = torus_embed(cfg.torus_major_radius, cfg.torus_minor_radius, u, v)

    return {
        "mode": mode_name,
        "Q": q_norm,
        "sphere_hemisphere": hemisphere,
        "sphere_phi": phi,
        "sphere_theta": theta,
        "sphere_xyz": sphere_xyz,
        "torus_u": u,
        "torus_v": v,
        "torus_xyz": torus_xyz,
    }

def sphere_surface_error(cfg: Config, pts: np.ndarray):
    return float(np.max(np.abs(np.linalg.norm(pts, axis=1) - cfg.sphere_radius)))

def torus_surface_error(cfg: Config, pts: np.ndarray):
    rho = np.sqrt(pts[:,0]**2 + pts[:,1]**2)
    residual = (rho - cfg.torus_major_radius)**2 + pts[:,2]**2 - cfg.torus_minor_radius**2
    return float(np.max(np.abs(residual)))


# -----------------------------
# STAGE 7: DISPLAY LAYER
# -----------------------------

def sphere_display_offset(cfg: Config, pts: np.ndarray):
    normals = pts / np.linalg.norm(pts, axis=1, keepdims=True)
    return pts + cfg.display_offset_sphere*normals

def torus_display_offset(cfg: Config, pts: np.ndarray):
    rho = np.sqrt(pts[:,0]**2 + pts[:,1]**2)
    center = np.column_stack([
        cfg.torus_major_radius*pts[:,0]/np.maximum(rho, 1e-12),
        cfg.torus_major_radius*pts[:,1]/np.maximum(rho, 1e-12),
        np.zeros(len(pts))
    ])
    normals = pts - center
    normals = normals / np.linalg.norm(normals, axis=1, keepdims=True)
    return pts + cfg.display_offset_torus*normals


# -----------------------------
# RENDERING HELPERS
# -----------------------------

def sphere_mesh(cfg: Config):
    u = np.linspace(0, 2*np.pi, cfg.surface_u)
    v = np.linspace(0, np.pi, cfg.surface_v)
    U, V = np.meshgrid(u, v, indexing="ij")
    return (
        cfg.sphere_radius*np.sin(V)*np.cos(U),
        cfg.sphere_radius*np.sin(V)*np.sin(U),
        cfg.sphere_radius*np.cos(V)
    )

def torus_mesh(cfg: Config):
    u = np.linspace(0, 2*np.pi, cfg.surface_u)
    v = np.linspace(0, 2*np.pi, cfg.surface_v)
    U, V = np.meshgrid(u, v, indexing="ij")
    return (
        (cfg.torus_major_radius+cfg.torus_minor_radius*np.cos(V))*np.cos(U),
        (cfg.torus_major_radius+cfg.torus_minor_radius*np.cos(V))*np.sin(U),
        cfg.torus_minor_radius*np.sin(V)
    )

def set_axes_equal(ax, points, pad=0.08):
    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    centers = (mins+maxs)/2
    radius = np.max(maxs-mins)/2 * (1+pad)
    ax.set_xlim(centers[0]-radius, centers[0]+radius)
    ax.set_ylim(centers[1]-radius, centers[1]+radius)
    ax.set_zlim(centers[2]-radius, centers[2]+radius)

def plot_source_xy(out: Path, cfg: Config, X, Y, Z, raw_branches, resampled_branches):
    fig, ax = plt.subplots(figsize=(11, 10))
    finite = Z[np.isfinite(Z)]
    lim = np.percentile(np.abs(finite), 96) if finite.size else 1.0
    ax.contourf(X, Y, np.clip(Z, -lim, lim), levels=100)
    ax.contour(X, Y, Z, levels=[0], colors="black", linewidths=1.2)
    for i, b in enumerate(resampled_branches):
        ax.plot(b[:,0], b[:,1], linewidth=2.0, label=f"resampled branch {i}")
    ax.set_xlim(cfg.x_range)
    ax.set_ylim(cfg.y_range)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("STAGE 10: Source XY output curve")
    ax.grid(alpha=0.25)
    if len(resampled_branches) <= 8:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "01_source_xy_output_curve.png", dpi=cfg.dpi)
    plt.close(fig)

def plot_single_mode(out: Path, cfg: Config, mode: str, projections_by_branch: List[dict]):
    Xs,Ys,Zs = sphere_mesh(cfg)
    Xt,Yt,Zt = torus_mesh(cfg)

    fig = plt.figure(figsize=(22, 11), facecolor="white")

    ax = fig.add_subplot(121, projection="3d")
    ax.set_proj_type("ortho")
    ax.plot_surface(Xs,Ys,Zs,color="#d9e7ff",alpha=0.82,linewidth=0,shade=True)
    ax.plot_wireframe(Xs[::14,::14], Ys[::14,::14], Zs[::14,::14], linewidth=0.25, alpha=0.22)
    allpts = [np.column_stack([Xs.ravel(), Ys.ravel(), Zs.ravel()])]
    for p in projections_by_branch:
        exact = p["sphere_xyz"]
        display = sphere_display_offset(cfg, exact)
        ax.plot(exact[:,0], exact[:,1], exact[:,2], color="black", linewidth=cfg.exact_line_width, alpha=0.9)
        ax.plot(display[:,0], display[:,1], display[:,2], color="red", linewidth=cfg.display_line_width, alpha=0.95)
        allpts.append(display)
    set_axes_equal(ax, np.vstack(allpts), pad=0.12)
    ax.view_init(elev=25, azim=-45)
    ax.set_axis_off()
    ax.set_title(f"Sphere projection — {mode}\nblack exact curve; red display-only offset", fontsize=15)

    ax = fig.add_subplot(122, projection="3d")
    ax.set_proj_type("ortho")
    ax.plot_surface(Xt,Yt,Zt,color="#e5e5e5",alpha=0.88,linewidth=0,shade=True)
    ax.plot_wireframe(Xt[::14,::14], Yt[::14,::14], Zt[::14,::14], linewidth=0.25, alpha=0.22)
    allpts = [np.column_stack([Xt.ravel(), Yt.ravel(), Zt.ravel()])]
    for p in projections_by_branch:
        exact = p["torus_xyz"]
        display = torus_display_offset(cfg, exact)
        ax.plot(exact[:,0], exact[:,1], exact[:,2], color="black", linewidth=cfg.exact_line_width, alpha=0.9)
        ax.plot(display[:,0], display[:,1], display[:,2], color="blue", linewidth=cfg.display_line_width, alpha=0.95)
        allpts.append(display)
    set_axes_equal(ax, np.vstack(allpts), pad=0.12)
    ax.view_init(elev=26, azim=-40)
    ax.set_axis_off()
    ax.set_title(f"Torus projection — {mode}\nblack exact curve; blue display-only offset", fontsize=15)

    fig.tight_layout()
    fig.savefig(out / f"02_projection_{mode}.png", dpi=cfg.dpi)
    plt.close(fig)

def plot_intrinsic_charts(out: Path, cfg: Config, mode: str, projections_by_branch: List[dict]):
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    for p in projections_by_branch:
        axes[0].plot(p["sphere_phi"], p["sphere_theta"], linewidth=2.0)
        axes[1].plot(p["torus_u"], p["torus_v"], linewidth=2.0)
    axes[0].set_title(f"Sphere intrinsic chart — {mode}")
    axes[0].set_xlabel("phi")
    axes[0].set_ylabel("theta")
    axes[0].grid(alpha=0.25)
    axes[1].set_title(f"Torus intrinsic chart — {mode}")
    axes[1].set_xlabel("u")
    axes[1].set_ylabel("v")
    axes[1].grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out / f"03_intrinsic_charts_{mode}.png", dpi=cfg.dpi)
    plt.close(fig)

def plot_mode_comparison(out: Path, cfg: Config, projections_by_mode: Dict[str, List[dict]]):
    Xs,Ys,Zs = sphere_mesh(cfg)
    Xt,Yt,Zt = torus_mesh(cfg)
    modes = list(projections_by_mode.keys())

    fig = plt.figure(figsize=(24, 6*len(modes)), facecolor="white")
    row = 0
    for mode in modes:
        row += 1
        ax = fig.add_subplot(len(modes), 2, 2*row-1, projection="3d")
        ax.set_proj_type("ortho")
        ax.plot_surface(Xs,Ys,Zs,color="#d9e7ff",alpha=0.75,linewidth=0,shade=True)
        allpts = [np.column_stack([Xs.ravel(), Ys.ravel(), Zs.ravel()])]
        for p in projections_by_mode[mode]:
            d = sphere_display_offset(cfg, p["sphere_xyz"])
            ax.plot(d[:,0], d[:,1], d[:,2], color="red", linewidth=cfg.display_line_width)
            allpts.append(d)
        set_axes_equal(ax, np.vstack(allpts), pad=0.12)
        ax.view_init(elev=25, azim=-45)
        ax.set_axis_off()
        ax.set_title(f"Sphere — {mode}")

        ax = fig.add_subplot(len(modes), 2, 2*row, projection="3d")
        ax.set_proj_type("ortho")
        ax.plot_surface(Xt,Yt,Zt,color="#e5e5e5",alpha=0.80,linewidth=0,shade=True)
        allpts = [np.column_stack([Xt.ravel(), Yt.ravel(), Zt.ravel()])]
        for p in projections_by_mode[mode]:
            d = torus_display_offset(cfg, p["torus_xyz"])
            ax.plot(d[:,0], d[:,1], d[:,2], color="blue", linewidth=cfg.display_line_width)
            allpts.append(d)
        set_axes_equal(ax, np.vstack(allpts), pad=0.12)
        ax.view_init(elev=26, azim=-40)
        ax.set_axis_off()
        ax.set_title(f"Torus — {mode}")
    fig.tight_layout()
    fig.savefig(out / "04_projection_mode_comparison.png", dpi=cfg.dpi)
    plt.close(fig)


# -----------------------------
# STAGE 8/9: EXPORT + RECONSTRUCTION
# -----------------------------

def reconstruct_sphere(cfg: Config, phi, theta):
    return sphere_embed(cfg.sphere_radius, phi, theta)

def reconstruct_torus(cfg: Config, u, v):
    return torus_embed(cfg.torus_major_radius, cfg.torus_minor_radius, u, v)

def score_projection(proj: dict):
    # Simple proxy metrics: coverage in secondary coordinate and smoothness.
    Q = proj["Q"]
    coverage = float(np.max(Q) - np.min(Q))
    smoothness = float(np.mean(np.abs(np.diff(Q, n=2)))) if len(Q) > 2 else 0.0
    # Higher is better: coverage good, roughness moderate penalty.
    return coverage - 0.25*smoothness

def export_branch_mode_csv(out: Path, cfg: Config, branch_id: int, mode: str, branch_xy, s_norm, arclength, channels, proj, f_np):
    x = branch_xy[:,0]
    y = branch_xy[:,1]
    F = eval_np_func(f_np, x, y)
    sphere = proj["sphere_xyz"]
    torus = proj["torus_xyz"]
    sphere_display = sphere_display_offset(cfg, sphere)
    torus_display = torus_display_offset(cfg, torus)

    df = pd.DataFrame({
        "branch_id": branch_id,
        "mode": mode,
        "s": s_norm,
        "arclength_total": arclength,
        "x": x,
        "y": y,
        "F": F,
        "curvature": channels["curvature"],
        "gradient_norm": channels["gradient"],
        "radius": channels["radius"],
        "Q": proj["Q"],
        "sphere_hemisphere": proj["sphere_hemisphere"],
        "sphere_phi": proj["sphere_phi"],
        "sphere_theta": proj["sphere_theta"],
        "sphere_X": sphere[:,0],
        "sphere_Y": sphere[:,1],
        "sphere_Z": sphere[:,2],
        "torus_u": proj["torus_u"],
        "torus_v": proj["torus_v"],
        "torus_X": torus[:,0],
        "torus_Y": torus[:,1],
        "torus_Z": torus[:,2],
        "sphere_display_X": sphere_display[:,0],
        "sphere_display_Y": sphere_display[:,1],
        "sphere_display_Z": sphere_display[:,2],
        "torus_display_X": torus_display[:,0],
        "torus_display_Y": torus_display[:,1],
        "torus_display_Z": torus_display[:,2],
    })
    path = out / f"branch_{branch_id:02d}_{mode}_data.csv"
    df.to_csv(path, index=False)
    return path, df

def write_progress(out: Path, stage_status: Dict[str, bool], todo: List[str], files: List[str]):
    lines = []
    lines.append("🚩 ACTION PLAN PROGRESS — EQUATION → TRUE CURVE → SURFACE PROJECTION\n")
    for i in range(13):
        key = f"STAGE {i}"
        mark = "✅" if stage_status.get(key, False) else "⬜"
        lines.append(f"{mark} {key} COMPLETE")
    lines.append("\nTODO / FAILED SELF-CHECKS")
    if todo:
        for t in todo:
            lines.append(f"- {t}")
    else:
        lines.append("- None")
    lines.append("\nOUTPUT FILES")
    for f in files:
        lines.append(f"- {f}")
    lines.append("\n🔁 UPDATE THIS LIST REMINDER")
    lines.append("After each completed stage: mark complete, add failed self-checks as TODO, record exact files, revise next stage.")
    (out / "ACTION_PLAN_PROGRESS.txt").write_text("\n".join(lines), encoding="utf-8")

def run(cfg: Config):
    out = Path(cfg.outdir)
    out.mkdir(parents=True, exist_ok=True)

    stage_status = {f"STAGE {i}": False for i in range(13)}
    todo = []
    files = []

    # Stage 0
    stage_status["STAGE 0"] = True

    # Stage 1
    x_sym, y_sym, F_sym, f_np, dFx_np, dFy_np = parse_equation(cfg.equation)
    stage_status["STAGE 1"] = True

    # Stage 2
    xs, ys, X, Y, Z = evaluate_grid(cfg, f_np)
    raw_branches = extract_zero_contours(X, Y, Z, cfg.min_branch_points)
    if not raw_branches:
        todo.append("STAGE 2 FAILED: no zero contour branches found.")
        write_progress(out, stage_status, todo, files)
        raise RuntimeError("No zero contour branches found.")
    stage_status["STAGE 2"] = True

    # Stage 3/4
    branch_records = []
    resampled_for_plot = []
    for i, raw in enumerate(raw_branches):
        resampled, s_norm, arclength = resample_by_arclength(raw, cfg.resample_points_per_branch)
        channels, normalized, degenerate = compute_channels(resampled, s_norm, f_np, dFx_np, dFy_np)
        branch_records.append({
            "branch_id": i,
            "raw": raw,
            "resampled": resampled,
            "s": s_norm,
            "arclength": arclength,
            "channels": channels,
            "normalized": normalized,
            "degenerate": degenerate,
        })
        resampled_for_plot.append(resampled)
        raw_path = out / f"branch_{i:02d}_raw_source_xy.csv"
        np.savetxt(raw_path, raw, delimiter=",", header="x,y", comments="")
        files.append(raw_path.name)
        resampled_path = out / f"branch_{i:02d}_resampled_source_xy.csv"
        np.savetxt(resampled_path, resampled, delimiter=",", header="x,y", comments="")
        files.append(resampled_path.name)

    stage_status["STAGE 3"] = True
    stage_status["STAGE 4"] = True

    # Stage 5/6/7/8/9
    projections_by_mode = {}
    csv_paths = []
    diagnostics = {
        "equation": cfg.equation,
        "canonical_residual": str(F_sym),
        "config": asdict(cfg),
        "branch_count": len(branch_records),
        "branches": [],
        "modes": {},
        "final_acceptance": {},
    }

    for mode, channel_name in PROJECTION_MODES.items():
        projections_by_mode[mode] = []
        mode_scores = []
        diagnostics["modes"][mode] = {"branches": [], "score_mean": None}
        for rec in branch_records:
            q_norm = rec["normalized"][channel_name]
            proj = intrinsic_projection(cfg, rec["s"], q_norm, mode, branch_id=rec["branch_id"])
            projections_by_mode[mode].append(proj)

            sphere_err = sphere_surface_error(cfg, proj["sphere_xyz"])
            torus_err = torus_surface_error(cfg, proj["torus_xyz"])
            score = score_projection(proj)
            mode_scores.append(score)

            path, df = export_branch_mode_csv(
                out, cfg, rec["branch_id"], mode, rec["resampled"], rec["s"],
                rec["arclength"], rec["channels"], proj, f_np
            )
            csv_paths.append(path)
            files.append(path.name)

            # Reconstruction tests
            sphere_re = reconstruct_sphere(cfg, df["sphere_phi"].values, df["sphere_theta"].values)
            torus_re = reconstruct_torus(cfg, df["torus_u"].values, df["torus_v"].values)
            sphere_re_err = float(np.max(np.linalg.norm(sphere_re - df[["sphere_X","sphere_Y","sphere_Z"]].values, axis=1)))
            torus_re_err = float(np.max(np.linalg.norm(torus_re - df[["torus_X","torus_Y","torus_Z"]].values, axis=1)))
            max_abs_F = float(np.max(np.abs(df["F"].values)))
            mean_abs_F = float(np.mean(np.abs(df["F"].values)))

            diagnostics["modes"][mode]["branches"].append({
                "branch_id": rec["branch_id"],
                "channel": channel_name,
                "channel_degenerate": bool(rec["degenerate"][channel_name]),
                "sphere_surface_error": sphere_err,
                "torus_surface_error": torus_err,
                "sphere_reconstruction_error": sphere_re_err,
                "torus_reconstruction_error": torus_re_err,
                "max_abs_F": max_abs_F,
                "mean_abs_F": mean_abs_F,
                "score": score,
                "csv": path.name,
            })

            if max_abs_F > cfg.residual_tolerance_warning:
                todo.append(f"STAGE 2/3 WARNING: branch {rec['branch_id']} mode {mode} max |F|={max_abs_F:.4g}; contour extraction is finite-grid approximate.")
            if sphere_err > cfg.reconstruction_tolerance:
                todo.append(f"STAGE 6 FAILED: sphere surface error {sphere_err} for branch {rec['branch_id']} mode {mode}.")
            if torus_err > cfg.reconstruction_tolerance:
                todo.append(f"STAGE 6 FAILED: torus surface error {torus_err} for branch {rec['branch_id']} mode {mode}.")
            if sphere_re_err > cfg.reconstruction_tolerance:
                todo.append(f"STAGE 9 FAILED: sphere reconstruction error {sphere_re_err} for branch {rec['branch_id']} mode {mode}.")
            if torus_re_err > cfg.reconstruction_tolerance:
                todo.append(f"STAGE 9 FAILED: torus reconstruction error {torus_re_err} for branch {rec['branch_id']} mode {mode}.")

        diagnostics["modes"][mode]["score_mean"] = float(np.mean(mode_scores))

    stage_status["STAGE 5"] = True
    stage_status["STAGE 6"] = True
    stage_status["STAGE 7"] = True
    stage_status["STAGE 8"] = True
    stage_status["STAGE 9"] = True

    # Stage 10 renders
    plot_source_xy(out, cfg, X, Y, Z, raw_branches, resampled_for_plot)
    files.append("01_source_xy_output_curve.png")
    for mode, projections in projections_by_mode.items():
        plot_single_mode(out, cfg, mode, projections)
        files.append(f"02_projection_{mode}.png")
        plot_intrinsic_charts(out, cfg, mode, projections)
        files.append(f"03_intrinsic_charts_{mode}.png")
    plot_mode_comparison(out, cfg, projections_by_mode)
    files.append("04_projection_mode_comparison.png")
    stage_status["STAGE 10"] = True

    # Stage 11 mode comparison
    best_mode = max(diagnostics["modes"].items(), key=lambda kv: kv[1]["score_mean"])[0]
    diagnostics["mode_comparison"] = {
        "scores": {m: diagnostics["modes"][m]["score_mean"] for m in diagnostics["modes"]},
        "best_mode_by_simple_score": best_mode,
        "score_note": "Simple score = Q coverage minus roughness penalty; visual inspection still required."
    }
    stage_status["STAGE 11"] = True

    # Stage 12 final acceptance
    diagnostics["final_acceptance"] = {
        "all_diagnostics_pass": not any("FAILED" in t for t in todo),
        "warnings_present": any("WARNING" in t for t in todo),
        "symbolic_reconstruction_claimed": False,
        "sampled_source_and_surface_curves_reconstruct": not any("STAGE 9 FAILED" in t for t in todo),
        "clean_carrier_surfaces": True,
        "display_layer_excluded_from_reconstruction": True,
    }
    stage_status["STAGE 12"] = True

    pkg_path = out / "projection_package.json"
    pkg_path.write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    files.append(pkg_path.name)

    summary_path = out / "summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Equation → true curve → surface projection\n")
        f.write("==========================================\n\n")
        f.write(f"Equation: {cfg.equation}\n")
        f.write(f"Canonical residual: {F_sym}\n")
        f.write(f"Branch count: {len(branch_records)}\n")
        f.write(f"Projection modes: {', '.join(PROJECTION_MODES.keys())}\n")
        f.write(f"Best mode by simple score: {best_mode}\n\n")
        f.write("Final acceptance:\n")
        for k,v in diagnostics["final_acceptance"].items():
            f.write(f"  {k}: {v}\n")
        f.write("\nTODO / warnings:\n")
        if todo:
            for t in todo:
                f.write(f"  - {t}\n")
        else:
            f.write("  None\n")
    files.append(summary_path.name)

    write_progress(out, stage_status, todo, files)
    files.append("ACTION_PLAN_PROGRESS.txt")

    # Zip output
    zip_path = out.parent / "equation_true_curve_surface_projection_output.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in out.rglob("*"):
            z.write(p, p.relative_to(out.parent))

    print("Wrote outputs to", out.resolve())
    print("ZIP:", zip_path.resolve())
    print("Equation:", cfg.equation)
    print("Residual:", F_sym)
    print("Branch count:", len(branch_records))
    print("Best mode by simple score:", best_mode)
    print("Final acceptance:", diagnostics["final_acceptance"])
    if todo:
        print("TODO/WARNINGS:")
        for t in todo[:10]:
            print("-", t)
        if len(todo) > 10:
            print("... plus", len(todo)-10, "more")
    return out, zip_path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--equation", default=Config.equation)
    p.add_argument("--outdir", default=Config.outdir)
    p.add_argument("--x-range", nargs=2, type=float, default=Config.x_range)
    p.add_argument("--y-range", nargs=2, type=float, default=Config.y_range)
    p.add_argument("--grid-nx", type=int, default=Config.grid_nx)
    p.add_argument("--grid-ny", type=int, default=Config.grid_ny)
    p.add_argument("--resample-points-per-branch", type=int, default=Config.resample_points_per_branch)
    p.add_argument("--dpi", type=int, default=Config.dpi)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    cfg = Config(
        equation=args.equation,
        outdir=args.outdir,
        x_range=tuple(args.x_range),
        y_range=tuple(args.y_range),
        grid_nx=args.grid_nx,
        grid_ny=args.grid_ny,
        resample_points_per_branch=args.resample_points_per_branch,
        dpi=args.dpi,
    )
    run(cfg)
