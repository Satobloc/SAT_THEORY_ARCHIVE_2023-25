import os, re, random, uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & GLOBAL THEME
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"HYPER_STABLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
        # Discrete Enrichment [3]
        if all(v == 0 for v in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

def get_compass_label(univ):
    """Reconstructs the Dimensional Compass shorthand [4, 5]."""
    x = '⁺' if univ['h']['x'] > 0 else '⁻' if univ['h']['x'] < 0 else ' '
    y = '₊' if univ['h']['y'] > 0 else '₋' if univ['h']['y'] < 0 else ' '
    z = '⁺' if univ['h']['z'] > 0 else '⁻' if univ['h']['z'] < 0 else ' '
    w = '₊' if univ['h']['w'] > 0 else '₋' if univ['h']['w'] < 0 else ' '
    g1 = 'ˣ' if (univ['w']['xz'] > 0 or univ['w']['xw'] > 0) else 'ᵛ' if (univ['w']['zw'] < 0) else ' '
    g2 = 'ₓ' if (univ['w']['xy'] > 0 or univ['w']['yz'] > 0) else 'ᵥ' if (univ['w']['yz'] < 0) else ' '
    return f"[{x}{y}[{g1}[H]{g2}]{z}{w}]"

# ==========================================
# 3. INTERACTIVE ENGINE (FIXED & ENHANCED)
# ==========================================
class StableEvolver:
    def __init__(self, univ, physics):
        # FIX: Define max_rate BEFORE the plotter/widgets to avoid AttributeError [6]
        self.univ = univ
        self.physics = physics
        self.base_radius = 21.0
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        
        self.plotter = pv.Plotter(title=f"Observatory: {univ['id']}")
        self.plotter.set_background("black")
        
        # MESH setup
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=160, theta_resolution=160)
        self.mesh_actor = self.plotter.add_mesh(self.base_mesh.copy(), cmap='twilight', smooth_shading=True)
        
        # AXIS 1: Standard XYZ
        self.plotter.add_axes(line_width=3, label_size=(0.05, 0.05))
        
        # AXIS 2: The 4D W-Axis Projection [USER REQUEST]
        # Projected as a magenta vector pointing toward (1,1,1)
        w_origin = np.array()
        w_vector = np.array([7]) * (self.base_radius * 1.5)
        self.plotter.add_arrows(w_origin, w_vector, mag=1, color='magenta', label='w-axis')
        self.plotter.add_point_labels([w_vector], ["W"], font_size=12, text_color='magenta')

        # UI Overlay
        compass = get_compass_label(univ)
        info = (f"ID: {univ['id']} | COMPASS: {compass}\n"
                f"STRESS: {physics['Stress']:.3f} | HELICITY: {physics['Helicity']:.3f}\n"
                f"COUPLINGS: {', '.join(univ['couplings'][:3])}")
        self.plotter.add_text(info, font_size=10, position='upper_left', name='stack')

        # WIDGETS
        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, 
                                      title="Cosmic Epoch", color="white", 
                                      pointa=(0.7, 0.05), pointb=(0.95, 0.05))
        
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.reset_camera()
        self.plotter.add_key_event('s', self.save_snap)

    def update_topology(self, t):
        evolved = self.base_mesh.copy(); pts = evolved.points
        # 1. 4D Flow Gradient [1, 8]
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.05 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.05 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.05 * t)
        
        # 2. Windmill Torsion [9, 10]
        if self.univ['w']['xy'] != 0:
            angle = self.univ['w']['xy'] * (pts[:, 2] / self.base_radius) * 0.1 * t
            x_new = pts[:, 0] * np.cos(angle) - pts[:, 1] * np.sin(angle)
            y_new = pts[:, 0] * np.sin(angle) + pts[:, 1] * np.cos(angle)
            pts[:, 0], pts[:, 1] = x_new, y_new
        
        # 3. Metric Buckling (The Metric Knot effect) [11, 12]
        if self.physics['Stress'] > 1.2:
            pts += np.random.normal(0, 0.005 * self.physics['Stress'] * (t / 20), pts.shape)
        
        self.mesh_actor.mapper.dataset.points = pts

        # Stable Orbit Logic
        current_extent = self.base_radius * (1.0 + self.max_rate * 0.05 * t)
        self.plotter.camera.distance = current_extent * 5.0
        self.plotter.camera.focal_point = (0, 0, 0)

    def save_snap(self):
        fname = os.path.join(RUN_DIR, f"{self.univ['id']}_evolved.png")
        self.plotter.screenshot(fname)
        print(f"Archived topology: {fname}")

# ==========================================
# 4. EXECUTION (DOUBLE-RANDOM SAMPLING)
# ==========================================
if __name__ == "__main__":
    # A. Pull the list of valid files [13]
    prefixes = ("SIXTY", "RANDOM", "TRILLION")
    all_files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(prefixes)]
    
    if all_files:
        # B. Select a random file from the list [USER REQUEST]
        target_file = random.choice(all_files)
        print(f"Source Selected: {target_file}")
        
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        if catalog:
            # C. Pick a random universe from that file [14]
            selected = random.choice(catalog)
            
            # Physics Calculation [15-17]
            h_v = np.array(list(selected['h'].values()))
            w_v = np.array(list(selected['w'].values()))
            g_avg = np.mean(np.abs(selected['g'])) if selected['g'] else 0.5
            stress = np.linalg.norm(h_v) + (np.sum(np.abs(w_v)) * g_avg)
            helicity = (selected['h']['z'] * selected['w']['xy'] + selected['h']['w'] * selected['w']['xz']) * g_avg
            physics = {"Stress": stress, "Helicity": helicity}

            print(f"--- OBSERVING UNIVERSE {selected['id']} ---")
            engine = StableEvolver(selected, physics)
            engine.plotter.show()