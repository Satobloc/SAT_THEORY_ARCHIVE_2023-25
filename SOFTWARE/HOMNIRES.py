# FIRST WINNER

import os, re, random, uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & DIRECTORY
# ==========================================
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"VOYAGER_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. DEEP-SCAN OMNI-PARSER (HARDENED)
# ==========================================
def parse_universes(data_string):
    """Hardened parser Indifferent to spaces, tabs, or missing H/HH tags."""
    blocks = re.split(r'(?=\d{9})', data_string)
    catalog = []
    for block in blocks:
        if not block.strip(): continue
        id_match = re.search(r'^(\d{9})', block.strip())
        univ_id = id_match.group(1) if id_match else "000000000"
        univ = {
            'id': univ_id,
            'h': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0},
            'w': {'xy': 0.0, 'xz': 0.0, 'xw': 0.0, 'yz': 0.0, 'yw': 0.0, 'zw': 0.0},
            'g': [float(g) for g in re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)]
        }
        # A. Format 1: Continuous (e.g., y@+1.2h*)
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        
        # B. Format 2: Discrete (e.g., expansion: x + y) - Space Hardened
        if all(v == 0 for v in univ['h'].values()):
            exp_find = re.search(r'expansion:[\s\t]*([xyzw\s\+\t]+)', block)
            con_find = re.search(r'contraction:[\s\t]*([xyzw\s\+\t]+)', block)
            if exp_find:
                for a in re.findall(r'[xyzw]', exp_find.group(1)): univ['h'][a] = DEFAULT_EVOL_SPEED
            if con_find:
                for a in re.findall(r'[xyzw]', con_find.group(1)): univ['h'][a] = -DEFAULT_EVOL_SPEED
                
        if all(v == 0 for v in univ['w'].values()):
            cw_find = re.search(r'clockwise rotation:[\s\t]*([xyzw\s\+\t]+)', block)
            wid_find = re.search(r'widdershins rotation:[\s\t]*([xyzw\s\+\t]+)', block)
            if cw_find:
                for p in re.findall(r'[xyzw]{2}', cw_find.group(1)): univ['w'][p] = DEFAULT_EVOL_SPEED
            if wid_find:
                for p in re.findall(r'[xyzw]{2}', wid_find.group(1)): univ['w'][p] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

# ==========================================
# 3. INTERACTIVE ADAPTIVE EVOLVER
# ==========================================
def calculate_physics(univ):
    h_v = np.array(list(univ['h'].values())); w_v = np.array(list(univ['w'].values()))
    g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
    stress = np.linalg.norm(h_v) + (np.sum(np.abs(w_v)) * g_avg)
    helicity = (univ['h']['z'] * univ['w']['xy'] + univ['h']['w'] * univ['w']['xz']) * g_avg
    return {"ID": univ['id'], "Stress": round(stress, 4), "Helicity": round(helicity, 4)}

class ManifoldEvolver:
    def __init__(self, univ, physics):
        self.univ = univ; self.physics = physics; self.base_radius = 21.0
        # High-Res Mesh as requested
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=360, theta_resolution=360)
        self.plotter = pv.Plotter(title=f"Evolution Engine: Universe {univ['id']}")
        self.plotter.set_background("black")
        
        # Initial Mesh Actor
        self.mesh_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), scalars=self.base_mesh.points[:, 2], 
            cmap='twilight', smooth_shading=True, show_scalar_bar=False
        )
        
class ManifoldEvolver:
    def __init__(self, univ, physics):
        self.univ = univ
        self.physics = physics
        self.base_radius = 21.0
        
        # 1. ENHANCED MESH
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=360, theta_resolution=360)
        self.plotter = pv.Plotter(title=f"Evolution Engine: {univ['id']}")
        self.plotter.set_background("black")
        
        # 2. ADAPTIVE CAMERA PREP: Track Max Possible Extent for Zooming logic
        self.max_rate = max(abs(v) for v in univ['h'].values()) if univ['h'] else 0.1
        
        # Initial Mesh Actor
        self.mesh_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), scalars=self.base_mesh.points[:, 2], 
            cmap='twilight', smooth_shading=True, show_scalar_bar=False
        )

        # 3. HYBRID SLIDER: White Visibility, Extended Range, and Specific Screen Placement
        self.plotter.add_slider_widget(
            self.update_topology, 
            [0.0, 200.0],           # Best Range: massive 200-epoch evolution window
            value=0.0, 
            title="Cosmic Epoch (T)", 
            color="white",          # Best Visibility: Colors the bar and knob white
            pointa=(0.7, 0.1),      # Best Placement: Bottom-right grouping
            pointb=(0.95, 0.1)
        )
        
        self.plotter.reset_camera() # Initial focus at T=0

    def update_topology(self, t):
        evolved = self.base_mesh.copy(); pts = evolved.points
        # 1. Flow Field Expansion
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.1 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.1 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.1 * t)
        # 2. Helical Gear Torsion
        if self.univ['w']['xy'] != 0:
            angle = self.univ['w']['xy'] * (pts[:, 2] / self.base_radius) * 0.2 * t
            x, y = pts[:, 0], pts[:, 1]
            pts[:, 0], pts[:, 1] = x * np.cos(angle) - y * np.sin(angle), x * np.sin(angle) + y * np.cos(angle)
        # 3. Metric Buckling
        if self.physics['Stress'] > 1.5:
            pts += np.random.normal(0, 0.005 * self.physics['Stress'] * (t / 10), pts.shape)
        
        self.mesh_actor.mapper.dataset.points = pts
        
        # 4. ADAPTIVE ZOOM: Adjust camera so the object always fills ~60% of view
        current_extent = self.base_radius * (1.0 + self.max_rate * 0.1 * t)
        self.plotter.camera.position = (0, 0, current_extent * 4.5)
        self.plotter.camera.focal_point = (0, 0, 0)

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(("SIXTY", "RANDOM", "TRILLION"))]
    if files:
        target = random.choice(files); print(f"Analysing Source: {target}")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        samples = random.sample(catalog, min(3, len(catalog)))
        summary = []
        for univ in samples:
            scores = calculate_physics(univ); summary.append(scores)
            print(f"--- LAUNCHING RENDER: {univ['id']} ---")
            evolver = ManifoldEvolver(univ, scores)
            evolver.plotter.show()
        
        pd.DataFrame(summary).to_csv(os.path.join(RUN_DIR, "Final_Batch_Summary.csv"), index=False)
        print(f"Done. Batch data consolidated in {RUN_DIR}")