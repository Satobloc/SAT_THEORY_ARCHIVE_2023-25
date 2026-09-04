import os, re, random, uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & GLOBAL THEME
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"OBSERVATORY_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

pv.global_theme.font.color = 'white'
DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. OMNI-PARSER & COMPASS RECONSTRUCTOR
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
        # Rates
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        # Discrete Fallback
        if all(v == 0 for v in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

def get_compass_label(univ):
    """Reconstructs the Dimensional Compass symbolic notation [8-10]."""
    x = '⁺' if univ['h']['x'] > 0 else '⁻' if univ['h']['x'] < 0 else ' '
    y = '₊' if univ['h']['y'] > 0 else '₋' if univ['h']['y'] < 0 else ' '
    z = '⁺' if univ['h']['z'] > 0 else '⁻' if univ['h']['z'] < 0 else ' '
    w = '₊' if univ['h']['w'] > 0 else '₋' if univ['h']['w'] < 0 else ' '
    
    # Rotation symbols [9, 10]
    # Clockwise: xz/xw (ˣ), xy/yw/yz (ₓ) | Widdershins: zw/xz (ᵛ), zw/yz (ᵥ)
    g1 = 'ˣ' if (univ['w']['xz'] > 0 or univ['w']['xw'] > 0) else 'ᵛ' if (univ['w']['zw'] < 0) else ' '
    g2 = 'ₓ' if (univ['w']['xy'] > 0 or univ['w']['yz'] > 0) else 'ᵥ' if (univ['w']['yz'] < 0) else ' '
    
    return f"[{x}{y}[{g1}[H]{g2}]{z}{w}]"

# ==========================================
# 3. INTERACTIVE OBSERVATORY ENGINE
# ==========================================
class ObservatoryEvolver:
    def __init__(self, univ):
        self.univ = univ
        h_v = np.array(list(univ['h'].values()))
        w_v = np.array(list(univ['w'].values()))
        g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
        self.stress = np.linalg.norm(h_v) + (np.sum(np.abs(w_v)) * g_avg)
        
        self.plotter = pv.Plotter(title=f"Observatory: {univ['id']}")
        self.plotter.set_background("black")
        self.base_radius = 21.0
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=200, theta_resolution=200)
        
        # DISPLAY: Full Data Stack [11, 12]
        compass = get_compass_label(univ)
        info_str = (f"ID: {univ['id']}\nCOMPASS: {compass}\n"
                    f"STRESS: {self.stress:.3f}\n"
                    f"COUPLINGS: {len(univ['couplings'])}\n"
                    f"{' | '.join(univ['couplings'][:2])}...")
        self.plotter.add_text(info_str, font_size=9, position='upper_left', name='data_stack')
        self.plotter.add_text("Press 'S' to save screenshot", font_size=8, position='lower_left')

        self.mesh_actor = self.plotter.add_mesh(self.base_mesh.copy(), cmap='twilight', smooth_shading=True)
        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, title="Cosmic Epoch", color="white")
        self.plotter.add_key_event('s', self.save_snap) # [!] Screenshot button/key
        
        # For non-resetting zoom logic
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        self.plotter.reset_camera()

    def update_topology(self, t):
        evolved = self.base_mesh.copy(); pts = evolved.points
        # 1. Flow & Torsion [1, 13]
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.05 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.05 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.05 * t)
        if self.univ['w']['xy'] != 0:
            angle = self.univ['w']['xy'] * (pts[:, 2] / self.base_radius) * 0.1 * t
            x, y = pts[:, 0], pts[:, 1]
            pts[:, 0], pts[:, 1] = x * np.cos(angle) - y * np.sin(angle), x * np.sin(angle) + y * np.cos(angle)
        
        # 2. Metric Buckling (Serrations like 000000033) [1, 14]
        if self.stress > 1.2:
            pts += np.random.normal(0, 0.004 * self.stress * (t / 10), pts.shape)
        
        self.mesh_actor.mapper.dataset.points = pts

        # 3. FIX: Gentle Revolution & Non-Axial Zoom [13]
        # Instead of resetting position, we adjust only the view distance (zoom)
        # and apply a small rotation to the existing camera view.
        self.plotter.camera.azimuth += 0.2  # Gentle revolution
        current_dist = self.plotter.camera.distance
        target_dist = (self.base_radius * (1.0 + self.max_rate * 0.05 * t)) * 4.5
        self.plotter.camera.distance = target_dist

    def save_snap(self):
        fname = os.path.join(RUN_DIR, f"{self.univ['id']}_capture.png")
        self.plotter.screenshot(fname)
        print(f"Captured: {fname}")

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
        print(f"--- OBSERVING {selected['id']} from {target} ---")
        evolver = ObservatoryEvolver(selected)
        evolver.plotter.show()