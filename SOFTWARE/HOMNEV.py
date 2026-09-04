import os
import re
import random
import uuid
import numpy as np
import pandas as pd
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & CONSOLIDATION SETUP
# ==========================================
# Ensuring outputs are saved in the specific folder provided
OUTPUT_BASE = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
SESSION_ID = f"BEST_OF_RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
RUN_DIR = os.path.join(OUTPUT_BASE, SESSION_ID)
os.makedirs(RUN_DIR, exist_ok=True)

DEFAULT_EVOL_SPEED = 1.0

# ==========================================
# 2. THE OMNI-PARSER (Handles all 6 Styles)
# ==========================================
def parse_universes(data_string):
    """Flexible parser using regex lookaheads for IDs."""
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
        # Format 1: Continuous Rates (h* and ω*)
        for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
        for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
        
        # Format 2: Discrete Lists (expansion: x+y) - Enrichment
        if all(val == 0 for val in univ['h'].values()):
            for a in 'xyzw':
                if f'expansion: {a}' in block or f'+{a}' in block: univ['h'][a] = DEFAULT_EVOL_SPEED
                if f'contraction: {a}' in block or f'+{a}' in block: univ['h'][a] = -DEFAULT_EVOL_SPEED
        catalog.append(univ)
    return catalog

# ==========================================
# 3. PHYSICS CALCULATIONS (GEMINI RECCS)
# ==========================================
def calculate_physics(univ):
    h_vec = np.array(list(univ['h'].values()))
    w_vec = np.array(list(univ['w'].values()))
    g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5
    
    # Universal Stress and Helicity (Screw-Thread Index)
    stress = np.linalg.norm(h_vec) + (np.sum(np.abs(w_vec)) * g_avg)
    helicity = (univ['h']['z'] * univ['w']['xy'] + univ['h']['w'] * univ['w']['xz']) * g_avg
    return {
        "ID": univ['id'],
        "Stress": round(stress, 4),
        "Helicity": round(helicity, 4),
        "Gearing": round(np.sum(w_vec)/(np.sum(np.abs(w_vec))+1e-9), 4)
    }

# ==========================================
# 4. ENHANCED EVOLVER (FIXED SLIDER)
# ==========================================
class ManifoldEvolver:
    def __init__(self, univ, physics):
        self.univ = univ
        self.physics = physics
        # Create a sphere to start
        self.base_mesh = pv.Sphere(radius=51.0, phi_resolution=560, theta_resolution=560)
        self.plotter = pv.Plotter(title=f"Evolution of Manifold {univ['id']}")
        
        # Add metadata text
        info = f"ID: {univ['id']} | Stress: {physics['Stress']} | Helicity: {physics['Helicity']}"
        self.plotter.add_text(info, font_size=11, color='white', position='upper_left')
        
        # Initial Mesh with 'twilight' heatmap for Hyperspatial shift
        self.mesh_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), scalars=self.base_mesh.points[:, 2], 
            cmap='twilight', smooth_shading=True
        )
        
        # CRITICAL FIX: The range [0.0, 100.0] must have exactly two numbers.
        slider_range = [0.0, 100.0]
        self.plotter.add_slider_widget(
            self.update_topology, slider_range, value=0.0, 
            title="Cosmic Epoch (T)", pointa=(0.7, 0.1), pointb=(0.95, 0.1)
        )

    def update_topology(self, t):
        evolved = self.base_mesh.copy()
        pts = evolved.points
        
        # A. Velocity Gradient Flow (h* rates)
        # Translates points outward/inward proportional to their distance
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.2 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.2 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.2 * t)

        # B. Helical Shearing (w* rates)
        # If xy rotation is active, twist the manifold around the Z-axis
        if self.univ['w']['xy'] != 0:
            angle = self.univ['w']['xy'] * pts[:, 2] * 0.4 * t
            x_new = pts[:, 0] * np.cos(angle) - pts[:, 1] * np.sin(angle)
            y_new = pts[:, 0] * np.sin(angle) + pts[:, 1] * np.cos(angle)
            pts[:, 0], pts[:, 1] = x_new, y_new

        # C. Metric Buckling (Stress induced ripples)
        if self.physics['Stress'] > 1.8:
            # High-tension manifolds develop surface noise as time progresses
            noise = np.random.normal(0, 0.006 * self.physics['Stress'] * t, pts.shape)
            pts += noise

        self.mesh_actor.mapper.dataset.points = pts

# ==========================================
# 5. CONSOLIDATED EXECUTION
# ==========================================
if __name__ == "__main__":
    # Scan directory for H-Universe files
    prefixes = ("SIXTY", "RANDOM", "TRILLION")
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(prefixes)]
    
    if files:
        target = random.choice(files)
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = parse_universes(f.read())
        
        # Sample 3 random universes for this interactive run
        samples = random.sample(catalog, min(3, len(catalog)))
        summary_list = []

        for univ in samples:
            physics_scores = calculate_physics(univ)
            summary_list.append(physics_scores)
            
            # Launch Window
            print(f"--- RENDERING INTERACTIVE {univ['id']} ---")
            evolver = ManifoldEvolver(univ, physics_scores)
            evolver.plotter.show()
        
        # Consolidate all stats into a single CSV in the run folder
        df = pd.DataFrame(summary_list)
        summary_path = os.path.join(RUN_DIR, "Batch_Physics_Summary.csv")
        df.to_csv(summary_path, index=False)
        print(f"\nBATCH COMPLETE. Stats saved to: {summary_path}")