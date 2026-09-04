import os, re, random, uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & GLOBAL THEME
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"STABLE_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

pv.global_theme.font.color = 'white'
DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. OMNI-PARSER & DATA RECONSTRUCTION
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
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        if all(v == 0 for v in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

def get_compass_label(univ):
    """Reconstructs the Dimensional Compass shorthand [1]."""
    x = '⁺' if univ['h']['x'] > 0 else '⁻' if univ['h']['x'] < 0 else ' '
    y = '₊' if univ['h']['y'] > 0 else '₋' if univ['h']['y'] < 0 else ' '
    z = '⁺' if univ['h']['z'] > 0 else '⁻' if univ['h']['z'] < 0 else ' '
    w = '₊' if univ['h']['w'] > 0 else '₋' if univ['h']['w'] < 0 else ' '
    g1 = 'ˣ' if (univ['w']['xz'] > 0 or univ['w']['xw'] > 0) else 'ᵛ' if (univ['w']['zw'] < 0) else ' '
    g2 = 'ₓ' if (univ['w']['xy'] > 0 or univ['w']['yz'] > 0) else 'ᵥ' if (univ['w']['yz'] < 0) else ' '
    return f"[{x}{y}[{g1}[H]{g2}]{z}{w}]"

# ==========================================
# 3. INTERACTIVE STABLE-ORBIT ENGINE
# ==========================================
class StableEvolver:
    def __init__(self, univ):
        self.univ = univ
        h_v = np.array(list(univ['h'].values()))
        w_v = np.array(list(univ['w'].values()))
        g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
        self.stress = np.linalg.norm(h_v) + (np.sum(np.abs(w_v)) * g_avg)
        
        self.plotter = pv.Plotter(title=f"Universe {univ['id']} Observatory")
        self.plotter.set_background("black")
        self.base_radius = 21.0
        # High-res mesh for buckling details [3]
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=360, theta_resolution=360)
        
        # UI: Reconstructed Compass and Minimal Indicators
        compass = get_compass_label(univ)
        info_str = (f"ID: {univ['id']}  {univ['raw'][:15]}\n"
                    f"COMPASS: {compass}\n"
                    f"METRIC STRESS: {self.stress:.3f}\n"
                    f"COUPLINGS: {', '.join(univ['couplings'])}")
        self.plotter.add_text(info_str, font_size=10, position='upper_left', name='stack')
        self.plotter.add_text("Press 'S' for Screenshot", font_size=8, position='lower_left')
        
        # MESH INITIALIZATION
        self.mesh_actor = self.plotter.add_mesh(self.base_mesh.copy(), cmap='twilight', smooth_shading=True)
        
        # [!] Minimal Axis Indicators [USER REQUEST]
        self.plotter.add_axes(line_width=2, cone_radius=0.6, shaft_length=0.7, label_size=(0.3, 0.1))

        # SLIDER CONFIG: Stable color and placement
        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, 
                                      title="Cosmic Epoch", color="white", 
                                      pointa=(0.7, 0.05), pointb=(0.95, 0.05))
        
        # CAMERA SETUP: Fixes the "swinging too much" issue by locking focal point
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.reset_camera()
        self.plotter.add_key_event('s', self.save_snap)

    def update_topology(self, t):
        evolved = self.base_mesh.copy(); pts = evolved.points
        # 1. Metric Stretching (Velocity Gradient) [4]
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.1 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.1 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.1 * t)
        
        # 2. Helical Torsion [4]
        if self.univ['w']['xy'] != 0:
            angle = self.univ['w']['xy'] * (pts[:, 2] / self.base_radius) * 0.2 * t
            x_new = pts[:, 0] * np.cos(angle) - pts[:, 1] * np.sin(angle)
            y_new = pts[:, 0] * np.sin(angle) + pts[:, 1] * np.cos(angle)
            pts[:, 0], pts[:, 1] = x_new, y_new
        
        # 3. Stress Buckling (The serrations seen in 000000033) [3]
        if self.stress > 1.2:
            pts += np.random.normal(0, 0.005 * self.stress * (t / 10), pts.shape)
        
        self.mesh_actor.mapper.dataset.points = pts

        # 4. FIX: SMOOTH ZOOM & ROTATION [USER REQUEST]
        # Prevents "axial snap" and the "funky offset" by adjusting relative to existing position
        current_extent = self.base_radius * (1.0 + self.max_rate * 0.1 * t)
        self.plotter.camera.distance = current_extent * 5.0
        self.plotter.camera.azimuth += 1.1 # Very slow, predictable revolution
        self.plotter.camera.focal_point = (0, 0, 0) # Keep camera aimed at core

    def save_snap(self):
        fname = os.path.join(RUN_DIR, f"{self.univ['id']}_evolved.png")
        self.plotter.screenshot(fname)
        print(f"Archived topology: {fname}")

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(("SIXTY", "RANDOM", "TRILLION"))]
    if files:
        target = random.choice(files)
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        selected = random.choice(catalog)
        print(f"--- OBSERVING UNIVERSE {selected['id']} from {target} ---")
        engine = StableEvolver(selected)
        engine.plotter.show()