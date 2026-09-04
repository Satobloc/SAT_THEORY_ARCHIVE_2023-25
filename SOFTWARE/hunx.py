import os, re, random, uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & THEME SETUP
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"VOYAGER_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

pv.global_theme.font.color = 'white'
DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. HARDENED OMNI-PARSER
# ==========================================
def parse_universes(data_string):
    """Parses continuous rates, discrete lists, and compass stacks."""
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
        # A. Format 1 Rates
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        # B. Format 2 & Condensed Shorthand Detection
        if all(v == 0 for v in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

def get_compass_label(univ):
    """Reconstructs symbolic stack from kinematics [4, 5]."""
    x = '⁺' if univ['h']['x'] > 0 else '⁻' if univ['h']['x'] < 0 else ' '
    y = '₊' if univ['h']['y'] > 0 else '₋' if univ['h']['y'] < 0 else ' '
    z = '⁺' if univ['h']['z'] > 0 else '⁻' if univ['h']['z'] < 0 else ' '
    w = '₊' if univ['h']['w'] > 0 else '₋' if univ['h']['w'] < 0 else ' '
    return f"[{x}{y}[H]{z}{w}]"

# ==========================================
# 3. INTERACTIVE X-RAY ENGINE (STABLE)
# ==========================================
class OmniCoreEvolver:
    def __init__(self, univ, physics):
        # [!] FIX 1: Move variables before widget creation to avoid AttributeError
        self.univ = univ
        self.physics = physics
        self.base_radius = 21.0
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        self.g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
        
        self.plotter = pv.Plotter(title=f"Omni-Core: Universe {univ['id']}")
        self.plotter.set_background("black")
        
        # A. OUTER SHELL: Twilight Heatmap + Transparency [6]
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=160, theta_resolution=160)
        self.shell_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), cmap='twilight', smooth_shading=True,
            opacity=0.3, name='outer_shell', show_scalar_bar=False
        )
        
        # B. TENSION NUCLEUS: Inner Structure reacting to Coupling (G) [7, 8]
        # Nucleus size is boosted by average absolute coupling
        self.inner_radius = self.base_radius * 0.3 * (1.0 + self.g_avg)
        self.inner_mesh = pv.Sphere(radius=self.inner_radius, phi_resolution=50, theta_resolution=50)
        self.nucleus_actor = self.plotter.add_mesh(
            self.inner_mesh.copy(), color='white', opacity=0.85, 
            name='nucleus', lighting=True
        )

        # C. 4D AXIS INDICATOR: Fixed Coordinate Vector [User Request]
        # [!] FIX 2: Added object coordinates to np.array
        w_origin = np.array() 
        w_vector = np.array([9]) * (self.base_radius * 1.5)
        self.plotter.add_arrows(w_origin, w_vector, mag=1, color='magenta')
        self.plotter.add_point_labels([w_vector], ["W-AXIS"], font_size=12, text_color='magenta')
        self.plotter.add_axes(line_width=3, label_size=(0.05, 0.05))

        # UI Text Data Pull
        info = (f"ID: {univ['id']} | {get_compass_label(univ)}\n"
                f"STRESS: {physics['Stress']:.3f} | COUPLINGS: {len(univ['couplings'])}\n"
                f"G_AVG: {self.g_avg:.3f} (CORE RIGIDITY)")
        self.plotter.add_text(info, font_size=10, position='upper_left')

        # Interactive Slider (Range: 0-200 epochs)
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
        
        # Helical Torsion [10, 11]
        if self.univ['w']['xy'] != 0:
            angle = self.univ['w']['xy'] * (pts[:, 2] / self.base_radius) * 0.1 * t
            pts[:, 0], pts[:, 1] = pts[:, 0]*np.cos(angle)-pts[:, 1]*np.sin(angle), pts[:, 0]*np.sin(angle)+pts[:, 1]*np.cos(angle)
        
        # Metric Buckling (Serrations) [7, 12]
        if self.physics['Stress'] > 1.2:
            pts += np.random.normal(0, 0.005 * self.physics['Stress'] * (t / 20), pts.shape)
        self.shell_actor.mapper.dataset.points = pts

        # 2. Evolve Tension Nucleus (Internal Structural Reaction)
        inner = self.inner_mesh.copy(); i_pts = inner.points
        i_pts *= (1.0 + self.univ['h']['w'] * 0.015 * t) 
        self.nucleus_actor.mapper.dataset.points = i_pts

        # 3. Stable Orbit Zoom
        current_extent = self.base_radius * (1.0 + self.max_rate * 0.04 * t)
        self.plotter.camera.distance = current_extent * 5.5
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.azimuth += 0.06

    def save_snap(self):
        fname = os.path.join(RUN_DIR, f"{self.univ['id']}_core_topology.png")
        self.plotter.screenshot(fname)
        print(f"Archived Core Snap: {fname}")

# ==========================================
# 4. DOUBLE-RANDOM EXECUTION
# ==========================================
if __name__ == "__main__":
    prefixes = ("SIXTY", "RANDOM", "TRILLION")
    all_files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(prefixes)]
    
    if all_files:
        # Step 1: Select Random File from the list [User Request]
        target_file = random.choice(all_files)
        print(f"Engaging Source: {target_file}")
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        if catalog:
            # Step 2: Select Random Universe from the catalog [13]
            selected = random.choice(catalog)
            
            # Metric Stress & Helicity Scores [1, 2, 14]
            h_v = np.array(list(selected['h'].values()))
            w_v = np.array(list(selected['w'].values()))
            g_avg = np.mean(np.abs(selected['g'])) if selected['g'] else 0.5
            stress = np.linalg.norm(h_v) + (np.sum(np.abs(w_v)) * g_avg)
            
            print(f"--- OBSERVING UNIVERSE {selected['id']} ---")
            engine = OmniCoreEvolver(selected, {"Stress": stress})
            engine.plotter.show()