import os, re, random, numpy as np, pandas as pd, pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & STABLE INITIALIZATION
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"HUD_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

pv.global_theme.font.color = 'white'
DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. DEEP-SCAN OMNI-PARSER (COMPASS & GEARS)
# ==========================================
def parse_universes(data_string):
    blocks = re.split(r'(?=\d{9})', data_string)
    catalog = []
    for block in blocks:
        if not block.strip(): continue
        id_match = re.search(r'^(\d{9})', block.strip())
        univ = {
            'id': id_match.group(1) if id_match else "000000000",
            'h': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0},
            'w': {'xy': 0.0, 'xz': 0.0, 'xw': 0.0, 'yz': 0.0, 'yw': 0.0, 'zw': 0.0},
            'g': [float(g) for g in re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)],
            'couplings': re.findall(r'C\d+{[^}]+}\[g=[^\]]+\]', block),
            'raw': block.strip()
        }
        # Extract Kinematics
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        # Discrete Shorthand Fallback (Format 2) [1-3]
        if all(v == 0 for v in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

# ==========================================
# 3. OBSERVATORY HUD ENGINE
# ==========================================
class UniversalHUD:
    def __init__(self, univ):
        # [!] CRITICAL FIX 1: Establish all variables BEFORE widget creation
        self.univ = univ
        self.base_radius = 21.0
        self.h_vec = np.array(list(univ['h'].values()))
        self.w_vec = np.array(list(univ['w'].values()))
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        self.g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
        
        # Calculate Initial Physics for Shading [4, 5]
        # Stress = Magnitude of expansion conflict
        self.stress_score = np.linalg.norm(self.h_vec) + (np.sum(np.abs(self.w_vec)) * self.g_avg)

        self.plotter = pv.Plotter(title=f"Universal Observer HUD: {univ['id']}")
        self.plotter.set_background("black")
        
        # A. MANIFOLD (Shaded by Stress Gradient)
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=160, theta_resolution=160)
        # Use vertex scalars to drive color [14, OMNI-H-UNIVERSE PYTHON]
        self.shell_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), cmap='magma', smooth_shading=True,
            opacity=0.3, name='outer_shell', show_scalar_bar=False
        )
        
        # B. TENSION CORE (Shaded by Torsion/Helicity)
        inner_r = self.base_radius * 0.3 * (1.0 + self.g_avg)
        self.inner_mesh = pv.Sphere(radius=inner_r, phi_resolution=60, theta_resolution=60)
        self.core_actor = self.plotter.add_mesh(
            self.inner_mesh.copy(), cmap='twilight', opacity=0.85, name='nucleus'
        )

        # [!] CRITICAL FIX 2: Correct NumPy Vector Arguments
        w_origin = np.array([0.0, 0.0, 0.0])
        w_dir = np.array([1.0, 1.0, 1.0]) * (self.base_radius * 1.5)
        self.plotter.add_arrows(w_origin, w_dir, mag=1, color='magenta')
        self.plotter.add_point_labels([w_dir], ["W-Axis"], font_size=10, text_color='magenta')
        self.plotter.add_axes()

        # HUD DISPLAY: Reconstructed Compass [6]
        compass = f"[{'⁺' if univ['h']['x']>0 else '⁻' if univ['h']['x']<0 else ' '}" \
                  f"{'₊' if univ['h']['y']>0 else '₋' if univ['h']['y']<0 else ' '}" \
                  f"[H]{'⁺' if univ['h']['z']>0 else '⁻' if univ['h']['z']<0 else ' '}" \
                  f"{'₊' if univ['h']['w']>0 else '₋' if univ['h']['w']<0 else ' '}]"
        
        hud_info = (f"U-ID: {univ['id']}\nCOMPASS: {compass}\n"
                    f"METRIC STRESS: {self.stress_score:.3f}\n"
                    f"STIFFNESS (G): {self.g_avg:.3f}\n"
                    f"GEARS: {len(univ['couplings'])}")
        self.plotter.add_text(hud_info, font_size=10, position='upper_left', shadow=True)

        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, 
                                      title="Cosmic Epoch (T)", color="white")
        self.plotter.reset_camera()
        self.plotter.add_key_event('s', self.save_snap)

    def update_topology(self, t):
        # 1. EVOLVE SHELL (Stress-Driven Shading)
        shell = self.base_mesh.copy(); pts = shell.points
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.04 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.04 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.04 * t)
        
        # Metric Buckling: Local noise driven by total Stress [7]
        if self.stress_score > 1.2:
            pts += np.random.normal(0, 0.005 * self.stress_score * (t / 15), pts.shape)
        
        # Color mapping: Vertex distance from origin as stress proxy
        dist = np.linalg.norm(pts, axis=1)
        self.shell_actor.mapper.dataset.points = pts
        self.shell_actor.mapper.dataset.point_data['scalars'] = dist

        # 2. EVOLVE CORE (Torsion-Driven Shading)
        inner = self.inner_mesh.copy(); i_pts = inner.points
        # The nucleus reacts to the W-expansion rate [5]
        i_pts *= (1.0 + self.univ['h']['w'] * 0.015 * t)
        
        # Apply torsion twist to the core only
        if self.univ['w']['xy'] != 0:
            ang = self.univ['w']['xy'] * 0.1 * t
            x, y = i_pts[:, 0], i_pts[:, 1]
            i_pts[:, 0] = x * np.cos(ang) - y * np.sin(ang)
            i_pts[:, 1] = x * np.sin(ang) + y * np.cos(ang)
            
        self.core_actor.mapper.dataset.points = i_pts
        self.core_actor.mapper.dataset.point_data['scalars'] = i_pts[:, 2] # Color by Z-depth

        # 3. CAMERA PERSISTENCE
        extent = self.base_radius * (1.0 + self.max_rate * 0.04 * t)
        self.plotter.camera.distance = extent * 5.5
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.azimuth += 0.05

    def save_snap(self):
        fname = os.path.join(RUN_DIR, f"{self.univ['id']}_hud_capture.png")
        self.plotter.screenshot(fname)
        print(f"Archived HUD Capture: {fname}")

# ==========================================
# 4. RANDOM SOURCE EXECUTION
# ==========================================
if __name__ == "__main__":
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(("SIXTY", "RANDOM", "TRILLION"))]
    if files:
        target = random.choice(files)
        print(f"Initializing Observatory from: {target}")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        if catalog:
            selected = random.choice(catalog)
            print(f"--- OBSERVING UNIVERSE {selected['id']} ---")
            obs = UniversalHUD(selected)
            obs.plotter.show()