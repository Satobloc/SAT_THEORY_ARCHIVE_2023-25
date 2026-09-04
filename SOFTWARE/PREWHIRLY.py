from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

base = Path("D:\__SAT26\H_UNIVERSES")
out = base / "clear_render_fix"
out.mkdir(exist_ok=True)

sphere_files = sorted(base.glob("branch_*_sphere_xyz.csv"))
torus_files = sorted(base.glob("branch_*_torus_xyz.csv"))
source_files = sorted(base.glob("branch_*_resampled_xy.csv"))

sphere_curves = [np.loadtxt(p, delimiter=",", skiprows=1) for p in sphere_files]
torus_curves = [np.loadtxt(p, delimiter=",", skiprows=1) for p in torus_files]
source_curves = [np.loadtxt(p, delimiter=",", skiprows=1) for p in source_files]

sphere_radius = 0.5
R = 1.0
r = 0.5

def sphere_mesh(nu=200, nv=140):
    u = np.linspace(0, 2*np.pi, nu)
    v = np.linspace(0, np.pi, nv)
    U, V = np.meshgrid(u, v, indexing="ij")
    return (
        sphere_radius*np.sin(V)*np.cos(U),
        sphere_radius*np.sin(V)*np.sin(U),
        sphere_radius*np.cos(V),
        U, V
    )

def torus_mesh(nu=220, nv=140):
    u = np.linspace(0, 2*np.pi, nu)
    v = np.linspace(0, 2*np.pi, nv)
    U, V = np.meshgrid(u, v, indexing="ij")
    return (
        (R+r*np.cos(V))*np.cos(U),
        (R+r*np.cos(V))*np.sin(U),
        r*np.sin(V),
        U, V
    )

def set_axes_equal(ax, points, pad=0.08):
    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    centers = (mins+maxs)/2
    rad = np.max(maxs-mins)/2 * (1+pad)
    ax.set_xlim(centers[0]-rad, centers[0]+rad)
    ax.set_ylim(centers[1]-rad, centers[1]+rad)
    ax.set_zlim(centers[2]-rad, centers[2]+rad)

def sphere_display_offset(curve, amount=0.035):
    n = curve / np.linalg.norm(curve, axis=1, keepdims=True)
    return curve + amount*n

def torus_display_offset(curve, amount=0.045):
    rho = np.sqrt(curve[:,0]**2 + curve[:,1]**2)
    # Center of tube circle at same major angle
    center = np.column_stack([R*curve[:,0]/rho, R*curve[:,1]/rho, np.zeros(len(curve))])
    normal = curve - center
    normal /= np.linalg.norm(normal, axis=1, keepdims=True)
    return curve + amount*normal

Xs,Ys,Zs,Us,Vs = sphere_mesh()
Xt,Yt,Zt,Ut,Vt = torus_mesh()

# 1. Big clear side-by-side render: solid surfaces, mesh, offset curves.
fig = plt.figure(figsize=(24, 12), facecolor="white")

ax = fig.add_subplot(121, projection="3d")
ax.set_proj_type("ortho")
ax.plot_surface(Xs, Ys, Zs, color="#d9e7ff", linewidth=0, alpha=0.92, shade=True)
ax.plot_wireframe(Xs[::10, ::10], Ys[::10, ::10], Zs[::10, ::10], linewidth=0.35, alpha=0.35)
allpts = [np.column_stack([Xs.ravel(), Ys.ravel(), Zs.ravel()])]
for c in sphere_curves:
    co = sphere_display_offset(c, 0.035)
    ax.plot(co[:,0], co[:,1], co[:,2], linewidth=7.0, color="red")
    ax.plot(c[:,0], c[:,1], c[:,2], linewidth=2.0, color="black", alpha=0.8)
    ax.scatter(co[::140,0], co[::140,1], co[::140,2], s=20, color="yellow", edgecolors="black", linewidths=0.4)
    allpts.append(co)
set_axes_equal(ax, np.vstack(allpts), pad=0.12)
ax.view_init(elev=25, azim=-45)
ax.set_axis_off()
ax.set_title("Sphere: projected heart curve\nred = display-offset copy; black = exact on-surface curve", fontsize=18)

ax = fig.add_subplot(122, projection="3d")
ax.set_proj_type("ortho")
ax.plot_surface(Xt, Yt, Zt, color="#e6e6e6", linewidth=0, alpha=0.96, shade=True)
ax.plot_wireframe(Xt[::10, ::10], Yt[::10, ::10], Zt[::10, ::10], linewidth=0.35, alpha=0.35)
allpts = [np.column_stack([Xt.ravel(), Yt.ravel(), Zt.ravel()])]
for c in torus_curves:
    co = torus_display_offset(c, 0.045)
    ax.plot(co[:,0], co[:,1], co[:,2], linewidth=7.0, color="blue")
    ax.plot(c[:,0], c[:,1], c[:,2], linewidth=2.0, color="black", alpha=0.8)
    ax.scatter(co[::140,0], co[::140,1], co[::140,2], s=20, color="yellow", edgecolors="black", linewidths=0.4)
    allpts.append(co)
set_axes_equal(ax, np.vstack(allpts), pad=0.12)
ax.view_init(elev=26, azim=-40)
ax.set_axis_off()
ax.set_title("Torus: projected heart curve\nblue = display-offset copy; black = exact on-surface curve", fontsize=18)

fig.tight_layout()
fig.savefig(out / "01_clear_projected_curves_display_offset.png", dpi=220)
plt.close(fig)

# 2. Four views with solid visibility
fig = plt.figure(figsize=(24, 18), facecolor="white")
views = [
    ("Sphere front", "sphere", 25, -45),
    ("Sphere top", "sphere", 90, -90),
    ("Torus front", "torus", 26, -40),
    ("Torus top", "torus", 90, -90),
]
for idx, (title, kind, elev, azim) in enumerate(views, start=1):
    ax = fig.add_subplot(2, 2, idx, projection="3d")
    ax.set_proj_type("ortho")
    if kind == "sphere":
        ax.plot_surface(Xs, Ys, Zs, color="#d9e7ff", linewidth=0, alpha=0.85, shade=True)
        ax.plot_wireframe(Xs[::12, ::12], Ys[::12, ::12], Zs[::12, ::12], linewidth=0.3, alpha=0.3)
        allpts = [np.column_stack([Xs.ravel(), Ys.ravel(), Zs.ravel()])]
        for c in sphere_curves:
            co = sphere_display_offset(c, 0.04)
            ax.plot(co[:,0], co[:,1], co[:,2], linewidth=6.0, color="red")
            allpts.append(co)
        set_axes_equal(ax, np.vstack(allpts), pad=0.14)
    else:
        ax.plot_surface(Xt, Yt, Zt, color="#e6e6e6", linewidth=0, alpha=0.90, shade=True)
        ax.plot_wireframe(Xt[::12, ::12], Yt[::12, ::12], Zt[::12, ::12], linewidth=0.3, alpha=0.3)
        allpts = [np.column_stack([Xt.ravel(), Yt.ravel(), Zt.ravel()])]
        for c in torus_curves:
            co = torus_display_offset(c, 0.05)
            ax.plot(co[:,0], co[:,1], co[:,2], linewidth=6.0, color="blue")
            allpts.append(co)
        set_axes_equal(ax, np.vstack(allpts), pad=0.14)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=18)
fig.tight_layout()
fig.savefig(out / "02_clear_projection_four_views.png", dpi=210)
plt.close(fig)

# 3. Intrinsic coordinate plot: this proves/provides a visible projection in chart space.
# Recompute intrinsic coordinates from original xy projection mapping used earlier:
# x_range=(-1.6,1.6), y_range=(-1.4,1.8)
x_min, x_max = -1.6, 1.6
y_min, y_max = -1.4, 1.8
fig, axes = plt.subplots(1, 2, figsize=(18, 7), facecolor="white")
for branch in source_curves:
    x = branch[:,0]
    y = branch[:,1]
    u = 2*np.pi*(x-x_min)/(x_max-x_min)
    v_sphere = 0.12 + ((y-y_min)/(y_max-y_min))*(np.pi-0.24)
    v_torus = 2*np.pi*(y-y_min)/(y_max-y_min)
    axes[0].plot(u, v_sphere, linewidth=3.0, color="red")
    axes[1].plot(u, v_torus, linewidth=3.0, color="blue")
axes[0].set_title("Sphere intrinsic chart: longitude vs colatitude", fontsize=16)
axes[0].set_xlabel("longitude")
axes[0].set_ylabel("colatitude")
axes[0].grid(alpha=0.3)
axes[1].set_title("Torus intrinsic chart: major angle vs minor angle", fontsize=16)
axes[1].set_xlabel("major angle")
axes[1].set_ylabel("minor angle")
axes[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(out / "03_intrinsic_projection_charts.png", dpi=220)
plt.close(fig)

# 4. Save diagnostics
diag = {
    "note": "Black curves are exact on-surface curves. Red/blue curves are only a small normal display offset to make them visible against the surface.",
    "sphere_curve_points": [int(len(c)) for c in sphere_curves],
    "torus_curve_points": [int(len(c)) for c in torus_curves],
    "sphere_radius_error_exact_curve": [float(np.max(np.abs(np.linalg.norm(c, axis=1)-sphere_radius))) for c in sphere_curves],
    "torus_implicit_error_exact_curve": [float(np.max(np.abs((np.sqrt(c[:,0]**2+c[:,1]**2)-R)**2 + c[:,2]**2-r**2))) for c in torus_curves],
    "display_offset_used": {
        "sphere_radial_offset": 0.035,
        "torus_normal_offset": 0.045
    }
}
(out / "clear_render_diagnostics.json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
print("Wrote clear render outputs to", out)
print(json.dumps(diag, indent=2))
