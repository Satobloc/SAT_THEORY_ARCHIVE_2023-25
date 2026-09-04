import os, re, random, uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & THEME
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"STABLE_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

pv.global_theme.font.color = 'white'
DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. HARDENED OMNI-PARSER (FORMAT 1 & 2)
# ==========================================
def parse_universes(data_string):
    """Parses universes, indifferent to tabs, spaces, or format type."""
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
        # Rates (Format 1)
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        # Discrete States (Format 2)
        if all(v == 0 for v in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

def get_compass_label(univ):
    """Reconstructs the symbolic stack for the UI."""
    x = '⁺' if univ['h']['x'] > 0 else '⁻' if univ['h']['x'] < 0 else ' '
    y = '₊' if univ['h']['y'] > 0 else '₋' if univ['h']['y'] < 0 else ' '
    z = '⁺' if univ['h']['z'] > 0 else '⁻' if univ['h']['z'] < 0 else ' '
    w = '₊' if univ['h']['w'] > 0 else '₋' if univ['h']['w'] < 0 else ' '
    return f"[{x}{y}[H]{z}{w}]"

# ==========================================
# 3. STABLE INTERACTIVE ENGINE
# ==========================================
class StableCoreEvolver:
    def __init__(self, univ, physics):
        # [!] FIX: Move all variables BEFORE adding any widgets/renderers
        self.univ = univ
        self.physics = physics
        self.base_radius = 21.0
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        self.g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
        
        self.plotter = pv.Plotter(title=f"Observatory: {univ['id']}")
        self.plotter.set_background("black")
        
        # MESH 1: Transparent Outer Shell (Twilight colormap)
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=160, theta_resolution=160)
        self.shell_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), cmap='twilight', smooth_shading=True,
            opacity=0.3, name='outer_shell', show_scalar_bar=False
        )
        
        # MESH 2: Dynamic Nucleus (Reacts to Internal G)
        inner_r = self.base_radius * 0.3 * (0.5 + self.g_avg)
        self.inner_mesh = pv.Sphere(radius=inner_r, phi_resolution=50, theta_resolution=50)
        self.nucleus_actor = self.plotter.add_mesh(
            self.inner_mesh.copy(), color='white', opacity=0.8, name='nucleus'
        )

        # [!] FIX: np.array() arguments filled to prevent TypeError
        w_origin = np.array([0.0, 0.0, 0.0])
        w_dir = np.array([1.0, 1.0, 1.0]) * (self.base_radius * 0.5)
        self.plotter.add_arrows(w_origin, w_dir, mag=1, color='magenta')
        self.plotter.add_point_labels([w_dir], ["W-AXIS"], font_size=6, text_color='magenta')
        self.plotter.add_axes(line_width=3, label_size=(0.05, 0.05))

        # UI Overlay
        info = (f"ID: {univ['id']} | {get_compass_label(univ)}\n"
                f"STRESS: {physics['Stress']:.3f} | COUPLINGS: {len(univ['couplings'])}\n"
                f"G_AVG: {self.g_avg:.3f} (CORE STIFFNESS)")
        self.plotter.add_text(info, font_size=10, position='upper_left')

        # WIDGETS
        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, 
                                      title="Cosmic Epoch", color="white", 
                                      pointa=(0.7, 0.05), pointb=(0.95, 0.05))
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.reset_camera()
        self.plotter.add_key_event('s', self.save_snap)

    def update_topology(self, t):
        # 1. Evolve Outer Shell
        shell = self.base_mesh.copy(); pts = shell.points
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.04 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.04 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.04 * t)
        if self.univ['w']['xy'] != 0:
            ang = self.univ['w']['xy'] * (pts[:, 2] / self.base_radius) * 0.1 * t
            pts[:, 0], pts[:, 1] = pts[:, 0]*np.cos(ang)-pts[:, 1]*np.sin(ang), pts[:, 0]*np.sin(ang)+pts[:, 1]*np.cos(ang)
        if self.physics['Stress'] > 1.2:
            pts += np.random.normal(0, 0.005 * self.physics['Stress'] * (t / 20), pts.shape)
        self.shell_actor.mapper.dataset.points = pts

        # 2. Evolve Nucleus
        inner = self.inner_mesh.copy(); i_pts = inner.points
        i_pts *= (1.0 + self.univ['h']['w'] * 0.02 * t) 
        self.nucleus_actor.mapper.dataset.points = i_pts

        # Orbit and Zoom logic
        extent = self.base_radius * (1.0 + self.max_rate * 0.04 * t)
        self.plotter.camera.distance = extent * 5.5
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.azimuth += 0.05

    def save_snap(self):
        fname = os.path.join(RUN_DIR, f"{self.univ['id']}_snap.png")
        self.plotter.screenshot(fname)
        print(f"Archived topology: {fname}")

# ==========================================
# 4. DOUBLE-RANDOM EXECUTION
# ==========================================
if __name__ == "__main__":
    # RANDOM FILE SELECTION
    prefixes = ("SIXTY", "RANDOM", "TRILLION")
    all_files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(prefixes)]
    
    if all_files:
        target_file = random.choice(all_files)
        print(f"Source: {target_file}")
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        if catalog:
            # RANDOM UNIVERSE SELECTION
            selected = random.choice(catalog)
            
            # Physics Scoring
            h_v = np.array(list(selected['h'].values()))
            w_v = np.array(list(selected['w'].values()))
            g_avg = np.mean(np.abs(selected['g'])) if selected['g'] else 0.5
            stress = np.linalg.norm(h_v) + (np.sum(np.abs(w_v)) * g_avg)
            
            print(f"--- LAUNCHING OBSERVATORY FOR {selected['id']} ---")
            engine = StableCoreEvolver(selected, {"Stress": stress})
            engine.plotter.show()