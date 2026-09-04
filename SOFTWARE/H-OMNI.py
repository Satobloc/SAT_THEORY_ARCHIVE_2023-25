import os
import re
import random
import uuid
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. ENVIRONMENT & DIRECTORY SETUP
# ==========================================
# Target the specific directory provided in your query
OUTPUT_DIR = r"D:\__SAT26\H_UNIVERSES\ENGINE_OUTPUTS"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

VALID_PREFIXES = ("SIXTY THOUSAND UNIVERSES", "RANDOM_H_UNIVERSES", "TRILLION UNIVERSE")
DEFAULT_EVOL_SPEED = 1.0  # Default dynamics enrichment for sparse data

# ==========================================
# 2. OMNI-PARSER (Handles All 6 Formats)
# ==========================================
def parse_universes(data_string):
    """
    Flexible parser using regex lookaheads for 9-digit IDs.
    Extracts continuous rates (h*, w*), discrete lists, and compass symbols.
    """
    blocks = re.split(r'(?=\d{9})', data_string)
    catalog = []

    for block in blocks:
        if not block.strip(): continue
        
        # Identify ID and Type (H vs HH)
        id_match = re.search(r'^(\d{9})', block.strip())
        univ_id = id_match.group(1) if id_match else "000000000"
        is_hh = " HH" in block[:20]

        univ = {
            'id': univ_id,
            'type': "HH" if is_hh else "H",
            'h': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0},
            'w': {'xy': 0.0, 'xz': 0.0, 'xw': 0.0, 'yz': 0.0, 'yw': 0.0, 'zw': 0.0},
            'g': []
        }

        # Format 1: Continuous Rates (e.g., y@+0.974h*)
        h_cont = re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block)
        w_cont = re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block)
        g_vals = re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)

        for axis, val in h_cont: univ['h'][axis] = float(val)
        for plane, val in w_cont: univ['w'][plane] = float(val)
        univ['g'] = [float(g) for g in g_vals]

        # Format 2: Discrete Lists (e.g., expansion: x+y)
        # Enriches data if continuous rates are missing
        if sum(univ['h'].values()) == 0:
            exp = re.search(r'expansion:\s*([xyzw+]+)', block)
            con = re.search(r'contraction:\s*([xyzw+]+)', block)
            if exp:
                for a in re.findall(r'[xyzw]', exp.group(1)): univ['h'][a] = DEFAULT_EVOL_SPEED
            if con:
                for a in re.findall(r'[xyzw]', con.group(1)): univ['h'][a] = -DEFAULT_EVOL_SPEED

        if sum(univ['w'].values()) == 0:
            cw = re.search(r'clockwise rotation:\s*([xyzw+]+)', block)
            ccw = re.search(r'widdershins rotation:\s*([xyzw+]+)', block)
            if cw:
                for p in re.findall(r'[xyzw]{2}', cw.group(1)): univ['w'][p] = DEFAULT_EVOL_SPEED
            if ccw:
                for p in re.findall(r'[xyzw]{2}', ccw.group(1)): univ['w'][p] = -DEFAULT_EVOL_SPEED

        catalog.append(univ)
    return catalog

# ==========================================
# 3. ADVANCED PHYSICS CALCULATIONS
# ==========================================
def calculate_advanced_physics(univ):
    """Implements Hookean Stress, Frustration, Helicity, and Gearing."""
    h_vec = np.array(list(univ['h'].values()))
    w_vec = np.array(list(univ['w'].values()))
    g_avg = np.mean(np.abs(univ['g'])) if univ['g'] else 0.5

    # 1. Total Von Mises Stress (Metric Knot Index)
    stress = np.linalg.norm(h_vec) + (np.sum(np.abs(w_vec)) * g_avg)

    # 2. Frustration Index (Directional Mass/Potential Energy)
    frustration = np.sum(h_vec**2) * g_avg + np.sum(w_vec**2) * g_avg

    # 3. Helicity Score (Screw-Thread Flow)
    # Checks for z-expansion geared to xy-rotation, etc.
    helicity = (univ['h']['z'] * univ['w']['xy'] + univ['h']['w'] * univ['w']['xz']) * g_avg

    # 4. Gearing Ratio (Torsional Efficiency)
    gearing = np.sum(w_vec) / (np.sum(np.abs(w_vec)) + 1e-9)

    return {"Stress": stress, "Mass": frustration, "Helicity": helicity, "Gearing": gearing}

# ==========================================
# 4. ENHANCED 3D TOPOLOGY RENDERER
# ==========================================
def render_complex_topology(univ, physics, path):
    """
    Renders a 3D manifold where rotations create helical twists 
    and stress creates surface buckling.
    """
    mesh = pv.Sphere(radius=1.0, phi_resolution=50, theta_resolution=50)
    
    # Apply Linear Strain (h*)
    mesh.points[:, 0] *= (1.0 + univ['h']['x'] * 0.4)
    mesh.points[:, 1] *= (1.0 + univ['h']['y'] * 0.4)
    mesh.points[:, 2] *= (1.0 + univ['h']['z'] * 0.4)

    # Apply Torsional Shearing (w*) - Creating the "Corkscrew"
    # Rotate points around Z based on their height if xy-rotation is present
    if univ['w']['xy'] != 0:
        angle = univ['w']['xy'] * mesh.points[:, 2] * 0.5
        x_new = mesh.points[:, 0] * np.cos(angle) - mesh.points[:, 1] * np.sin(angle)
        y_new = mesh.points[:, 0] * np.sin(angle) + mesh.points[:, 1] * np.cos(angle)
        mesh.points[:, 0] = x_new
        mesh.points[:, 1] = y_new

    # Apply Stress Buckling (High Stress = Folds/Wrinkles)
    if physics['Stress'] > 2.0:
        noise = np.random.normal(0, 0.02 * physics['Stress'], mesh.points.shape)
        mesh.points += noise

    # Save Screenshot
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh, scalars=mesh.points[:, 2], cmap='twilight', smooth_shading=True)
    plotter.add_text(f"ID: {univ['id']}\nHelicity: {physics['Helicity']:.2f}", font_size=10)
    plotter.screenshot(f"{path}_topology.png")

# ==========================================
# 5. EXECUTION & UNIQUE FILE OUTPUT
# ==========================================
if __name__ == "__main__":
    # Create a sub-folder for this specific run
    session_stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_folder = os.path.join(OUTPUT_DIR, f"RUN_{session_stamp}")
    os.makedirs(run_folder)

    # Discovery
    files = [f for f in os.listdir(".") if f.startswith(VALID_PREFIXES) and f.endswith(".txt")]
    if files:
        target_file = random.choice(files)
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        
        catalog = parse_universes(data)
        # Select 5 random universes for this run
        samples = random.sample(catalog, min(5, len(catalog)))

        for univ in samples:
            unique_id = f"{univ['id']}_{uuid.uuid4().hex[:4]}"
            path_base = os.path.join(run_folder, unique_id)
            
            # Physics Dashboard
            physics = calculate_advanced_physics(univ)
            
            # Visuals
            render_complex_topology(univ, physics, path_base)
            
            # Stats Logging
            with open(f"{path_base}_stats.txt", "w") as sf:
                sf.write(f"Universe: {univ['id']} [{univ['type']}]\nSource: {target_file}\n")
                sf.write("-" * 20 + "\n")
                for k, v in physics.items(): sf.write(f"{k}: {v:.4f}\n")

        print(f"Sampling complete. Results saved to: {run_folder}")