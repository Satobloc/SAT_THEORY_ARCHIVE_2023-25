from pathlib import Path
import textwrap, os, json, math

outdir = Path("/mnt/data/t4_raindrop_sim")
outdir.mkdir(parents=True, exist_ok=True)

script = r'''
"""
Toy intrinsic-view simulation for a deforming "raindrop universe".

Outputs five images:
1. external_embedding.png      — model-builder's outside view
2. metric_tension_map.png      — intrinsic strain/tension proxy
3. last_scattering_map.png     — source field at transparency
4. observed_sky_map.png        — delayed/redshifted intrinsic view
5. delay_winding_map.png       — travel-time / winding structure

This is a qualitative toy model, not a solution of Einstein's equations
or a full T^4 ray tracer. It uses an axisymmetric closed surface surrogate.
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ----------------------------
# User controls
# ----------------------------
OUTPUT_DIR = Path("t4_raindrop_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_LAT = 360
N_LON = 720

# Transparency time: 0 = nearly spherical, 1 = strongly pinched/sac-like
T_TRANSPARENT = 0.38

# Observation time
T_OBS = 1.00

# Observer latitude/longitude on the intrinsic surface
OBS_LAT = np.deg2rad(20.0)
OBS_LON = np.deg2rad(25.0)

# Number of toy winding families included in the observed sky
WINDINGS = (-1, 0, 1)

# ----------------------------
# CMB-like diverging palette
# ----------------------------
cmb_colors = [
    "#061a40", "#123b7a", "#2d68b2", "#73a9d8",
    "#d8eef5", "#fff8dc", "#f6c37a", "#dc6b4a",
    "#a8232c", "#5b0b1d"
]
CMB_CMAP = LinearSegmentedColormap.from_list("cmb_like", cmb_colors, N=256)

# ----------------------------
# Coordinate grids
# ----------------------------
lat = np.linspace(-np.pi/2, np.pi/2, N_LAT)
lon = np.linspace(-np.pi, np.pi, N_LON)
LON, LAT = np.meshgrid(lon, lat)

# Colatitude for embedding
TH = np.pi/2 - LAT
PH = LON

def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x*x*(3 - 2*x)

def shape_parameters(t):
    """
    Smoothly moves through:
    sphere -> flattened bulk -> membrane -> sac/pinch.
    """
    s = smoothstep(t)
    flatten = 0.30 * s
    sac = 0.23 * smoothstep((t - 0.28) / 0.72)
    pinch = 0.60 * smoothstep((t - 0.52) / 0.48)
    breathing = 0.045 * np.sin(7*np.pi*t) * np.exp(-1.5*t)
    return flatten, sac, pinch, breathing

def radius_field(theta, t):
    """
    Axisymmetric embedding radius.
    theta = colatitude; equator at theta=pi/2.
    """
    flatten, sac, pinch, breathing = shape_parameters(t)
    mu = np.cos(theta)

    # Oblate deformation: wider near equator, shorter at poles
    oblate = 1.0 + flatten * (0.5 - 1.5*mu**2)

    # Upper sac / bag bulge
    upper = np.exp(-((theta - 0.65*np.pi)**2) / (2*(0.22*np.pi)**2))
    sac_term = 1.0 + sac * upper

    # Equatorial thinning / necking
    neck = np.exp(-((theta - 0.5*np.pi)**2) / (2*(0.10*np.pi)**2))
    pinch_term = 1.0 - pinch * neck

    # Small global breathing oscillation
    breathe = 1.0 + breathing * np.cos(2*theta)

    return oblate * sac_term * pinch_term * breathe

def embedding_xyz(t):
    r = radius_field(TH, t)
    x = r * np.sin(TH) * np.cos(PH)
    y = r * np.sin(TH) * np.sin(PH)
    z = r * np.cos(TH)
    return x, y, z, r

def angular_distance(lat1, lon1, lat2, lon2):
    c = (
        np.sin(lat1)*np.sin(lat2)
        + np.cos(lat1)*np.cos(lat2)*np.cos(lon1-lon2)
    )
    return np.arccos(np.clip(c, -1.0, 1.0))

def intrinsic_metric_proxies(t):
    """
    Crude intrinsic proxies from the embedded radial profile.
    They are not exact curvature invariants.
    """
    r = radius_field(TH, t)
    dr_dtheta = np.gradient(r, TH[:, 0], axis=0)
    d2r_dtheta2 = np.gradient(dr_dtheta, TH[:, 0], axis=0)

    # Stretch / strain proxy
    meridional_stretch = np.sqrt(r**2 + dr_dtheta**2)
    azimuthal_stretch = np.maximum(r*np.sin(TH), 1e-6)

    # Tension-gradient / curvature-like proxy
    tension = np.log(meridional_stretch / np.mean(meridional_stretch))
    curvature_proxy = d2r_dtheta2 / np.maximum(r, 1e-6)

    return r, tension, curvature_proxy, meridional_stretch, azimuthal_stretch

def source_field(t_transparent):
    """
    Toy last-scattering temperature field:
    low-order coherent structure + small-scale fluctuations.
    """
    rng = np.random.default_rng(7)
    base = (
        0.75*np.sin(2*LAT)
        + 0.45*np.cos(3*LON)*np.cos(LAT)**2
        + 0.28*np.sin(5*LON + 1.7*LAT)
    )

    # Smoothed random harmonics
    noise = np.zeros_like(base)
    for k in range(1, 10):
        amp = rng.normal(scale=0.16/(k**0.7))
        phase = rng.uniform(-np.pi, np.pi)
        noise += amp*np.cos(k*LON + phase)*np.cos((k % 5 + 1)*LAT)

    _, tension, curvature, _, _ = intrinsic_metric_proxies(t_transparent)
    field = base + noise + 0.8*tension - 0.35*curvature
    field -= np.mean(field)
    field /= np.std(field)
    return field

def bilinear_sample(field, lat_q, lon_q):
    lon_q = (lon_q + np.pi) % (2*np.pi) - np.pi
    lat_q = np.clip(lat_q, -np.pi/2, np.pi/2)

    u = (lon_q + np.pi) / (2*np.pi) * (N_LON - 1)
    v = (lat_q + np.pi/2) / np.pi * (N_LAT - 1)

    u0 = np.floor(u).astype(int)
    v0 = np.floor(v).astype(int)
    u1 = (u0 + 1) % N_LON
    v1 = np.minimum(v0 + 1, N_LAT - 1)

    fu = u - u0
    fv = v - v0

    return (
        field[v0, u0]*(1-fu)*(1-fv)
        + field[v0, u1]*fu*(1-fv)
        + field[v1, u0]*(1-fu)*fv
        + field[v1, u1]*fu*fv
    )

def observed_sky(t_transparent, t_obs):
    """
    Backward-map observer sky directions to the transparency surface.
    Adds toy metric delay, redshift, lensing, and winding images.
    """
    src = source_field(t_transparent)
    _, tension_now, curvature_now, _, _ = intrinsic_metric_proxies(t_obs)

    sky = np.zeros_like(src)
    weight_sum = np.zeros_like(src)
    delay_map = np.zeros_like(src)

    # Observer-centered angular separation
    gamma = angular_distance(LAT, LON, OBS_LAT, OBS_LON)

    # Local fold contribution
    fold = 0.55*tension_now + 0.25*curvature_now

    for w in WINDINGS:
        # Longer path for nonzero winding
        path = gamma + 2*np.pi*abs(w)

        # Toy lensing / remapping
        lon_emit = LON + 0.20*np.sin(2*LAT)*smoothstep(t_obs) + 2*np.pi*w
        lat_emit = LAT + 0.10*np.sin(LON + 0.7*w)*np.cos(LAT)*smoothstep(t_obs)
        lat_emit -= 0.08*fold*np.sin(gamma)

        # Travel-time delay and redshift proxy
        delay = path * (1.0 + 0.32*np.abs(fold))
        redshift = 1.0 + 0.28*delay/(1.0 + delay) + 0.12*fold

        # Weight suppresses long winding paths
        weight = np.exp(-0.85*abs(w)) / np.maximum(redshift, 0.35)**3

        sample = bilinear_sample(src, lat_emit, lon_emit)
        sky += weight * sample / np.maximum(redshift, 0.35)
        weight_sum += weight
        delay_map += weight * delay

    sky /= np.maximum(weight_sum, 1e-9)
    delay_map /= np.maximum(weight_sum, 1e-9)

    sky -= np.mean(sky)
    sky /= np.std(sky)
    delay_map = (delay_map - np.min(delay_map)) / (np.ptp(delay_map) + 1e-9)
    return src, sky, delay_map

def save_mollweide(data, title, filename, cbar_label, vlim=None):
    fig = plt.figure(figsize=(12, 6.2))
    ax = fig.add_subplot(111, projection="mollweide")
    if vlim is None:
        vmax = np.nanpercentile(np.abs(data), 98)
    else:
        vmax = vlim
    im = ax.pcolormesh(LON, LAT, data, shading="auto",
                       cmap=CMB_CMAP, vmin=-vmax, vmax=vmax)
    ax.grid(True, alpha=0.25)
    ax.set_title(title, pad=18)
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.08, fraction=0.055)
    cb.set_label(cbar_label)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)

def save_external_embedding(t):
    x, y, z, r = embedding_xyz(t)

    # Downsample for 3D plotting
    step_lat = 6
    step_lon = 8
    xs = x[::step_lat, ::step_lon]
    ys = y[::step_lat, ::step_lon]
    zs = z[::step_lat, ::step_lon]

    _, tension, _, _, _ = intrinsic_metric_proxies(t)
    cs = tension[::step_lat, ::step_lon]
    vmax = np.percentile(np.abs(cs), 98)
    norm = plt.Normalize(-vmax, vmax)

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(xs, ys, zs,
                    facecolors=CMB_CMAP(norm(cs)),
                    linewidth=0, antialiased=True, shade=False)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=18, azim=-55)
    ax.set_title("1. External embedding at observation time")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "external_embedding.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

def make_montage():
    from PIL import Image, ImageOps, ImageDraw

    files = [
        "external_embedding.png",
        "metric_tension_map.png",
        "last_scattering_map.png",
        "observed_sky_map.png",
        "delay_winding_map.png",
    ]
    imgs = [Image.open(OUTPUT_DIR / f).convert("RGB") for f in files]

    thumb_w, thumb_h = 900, 520
    thumbs = []
    for im in imgs:
        fitted = ImageOps.contain(im, (thumb_w, thumb_h))
        canvas = Image.new("RGB", (thumb_w, thumb_h), "white")
        x = (thumb_w - fitted.width)//2
        y = (thumb_h - fitted.height)//2
        canvas.paste(fitted, (x, y))
        thumbs.append(canvas)

    montage = Image.new("RGB", (thumb_w*2, thumb_h*3), "white")
    positions = [(0,0), (thumb_w,0), (0,thumb_h), (thumb_w,thumb_h), (thumb_w//2,thumb_h*2)]
    for im, pos in zip(thumbs, positions):
        montage.paste(im, pos)

    montage.save(OUTPUT_DIR / "five_image_montage.png", quality=95)

def main():
    save_external_embedding(T_OBS)

    _, tension, curvature, _, _ = intrinsic_metric_proxies(T_OBS)
    metric_map = 0.75*tension + 0.25*curvature
    save_mollweide(
        metric_map,
        "2. Intrinsic tension-gradient / metric proxy",
        "metric_tension_map.png",
        "relative metric deformation"
    )

    src, sky, delay = observed_sky(T_TRANSPARENT, T_OBS)
    save_mollweide(
        src,
        f"3. Last-scattering field at transparency time t={T_TRANSPARENT:.2f}",
        "last_scattering_map.png",
        "source fluctuation"
    )
    save_mollweide(
        sky,
        f"4. Observer sky at t={T_OBS:.2f}",
        "observed_sky_map.png",
        "observed fluctuation"
    )

    # Delay map is positive, but center it for the same CMB-like diverging palette
    delay_centered = delay - np.mean(delay)
    save_mollweide(
        delay_centered,
        "5. Relative travel-time / winding-delay structure",
        "delay_winding_map.png",
        "relative delay"
    )

    make_montage()

    print(f"Wrote outputs to: {OUTPUT_DIR.resolve()}")
    for p in sorted(OUTPUT_DIR.glob("*.png")):
        print(" -", p.name)

if __name__ == "__main__":
    main()
'''

script_path = outdir / "t4_raindrop_sim.py"
script_path.write_text(textwrap.dedent(script), encoding="utf-8")

# Run script in its directory
import subprocess, sys
res = subprocess.run([sys.executable, str(script_path)], cwd=outdir, capture_output=True, text=True, timeout=120)
print(res.stdout)
print(res.stderr)

