import os, re, random, numpy as np, pyvista as pv
from datetime import datetime

# ==========================================
# 1. STABLE HUD THEME
# ==========================================
pv.global_theme.font.color = 'white'
OUTPUT_DIR = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# 2. NORMALIZING OBSERVATORY ENGINE
# ==========================================
class NormalizedObservatory:
    def __init__(self, univ):
        self.univ = univ
        self.base_radius = 21.0
        
        # NORMALIZATION: Bracket rates to observability percentages
        # We cap visual deformation at 30% of base radius
        self.h_norm = {k: np.clip(v, -2.0, 2.0) * 0.15 for k, v in univ['h'].items()}
        self.w_norm = {k: np.clip(v, -2.0, 2.0) * 0.1 for k, v in univ['w'].items()}
        self.g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5

        self.plotter = pv.Plotter(title=f"Normalized Observer: {univ['id']}")
        self.plotter.set_background("black")
        
        # MANIFOLD: X-Ray transparency with twilight shader
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=160, theta_resolution=160)
        self.shell_actor = self.plotter.add_mesh(self.base_mesh.copy(), cmap='twilight', opacity=0.3)
        
        # HUD: Geographized Indicators
        self.plotter.add_axes()
        w_vec = np.array([20]) * (self.base_radius * 1.4)
        self.plotter.add_arrows(np.array(), w_vec, color='magenta', label='W-Pole')
        
        # TEXT HUD
        info = (f"U-ID: {univ['id']}\nSTIFFNESS (G): {self.g_avg:.2f}\n"
                f"ACTIVE PLANES: {len([v for v in univ['w'].values() if v != 0])}")
        self.plotter.add_text(info, position='upper_left', font_size=10)

        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, color="white")

    def update_topology(self, t):
        shell = self.base_mesh.copy(); pts = shell.points
        
        # 1. Normalizing Flow (Percentage-based expansion)
        pts[:, 0] *= (1.0 + self.h_norm['x'] * (t / 100))
        pts[:, 1] *= (1.0 + self.h_norm['y'] * (t / 100))
        pts[:, 2] *= (1.0 + self.h_norm['z'] * (t / 100))

        # 2. Simultaneous Rotation (Tumbling Logic)
        if self.univ['w']['xy'] != 0:
            ang = self.w_norm['xy'] * t * 0.1
            x, y = pts[:, 0], pts[:, 1]
            pts[:, 0], pts[:, 1] = x*np.cos(ang)-y*np.sin(ang), x*np.sin(ang)+y*np.cos(ang)
        
        if self.univ['w']['xz'] != 0: # Secondary rotation plane
            ang = self.w_norm['xz'] * t * 0.05
            x, z = pts[:, 0], pts[:, 2]
            pts[:, 0], pts[:, 2] = x*np.cos(ang)-z*np.sin(ang), x*np.sin(ang)+z*np.cos(ang)

        # 3. Metric Buckling (Driven by G-Stiffness)
        if self.g_avg > 0.6:
            pts += np.random.normal(0, 0.004 * self.g_avg * (t / 20), pts.shape)

        self.shell_actor.mapper.dataset.points = pts
        self.plotter.camera.distance = self.base_radius * 6.0
        self.plotter.camera.azimuth += 0.05

# ==========================================
# 4. RANDOM_H DEFAULT LOADER
# ==========================================
def parse_universes(data_string):
    blocks = re.split(r'(?=\d{9})', data_string)
    catalog = []
    for block in blocks:
        if not block.strip(): continue
        id_match = re.search(r'^(\d{9})', block.strip())
        univ = {'id': id_match.group(1) if id_match else "000000000",
                'h': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0},
                'w': {'xy': 0.0, 'xz': 0.0, 'xw': 0.0, 'yz': 0.0, 'yw': 0.0, 'zw': 0.0},
                'g': [float(g) for g in re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)]}
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        catalog.append(univ)
    return catalog

if __name__ == "__main__":
    # DEFAULT LOAD: Specifically looks for RANDOM_H documents as requested
    files = [f for f in os.listdir(".") if f.startswith("RANDOM_H")]
    if files:
        target = random.choice(files)
        print(f"Observing Complex Dataset: {target}")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        if catalog:
            obs = NormalizedObservatory(random.choice(catalog))
            obs.plotter.show()