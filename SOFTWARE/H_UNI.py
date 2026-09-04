
The Omni-H-Sampler (Version 2.0)
import os
import re
import random
import uuid
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
from datetime import datetime

# ==========================================
# 1. CORE CONFIGURATION & DIRECTORY SETUP
# ==========================================
VALID_PREFIXES = ("SIXTY THOUSAND UNIVERSES", "RANDOM_H_UNIVERSES", "TRILLION UNIVERSE")
MAX_FILE_SIZE_MB = 50

# Create a unique session folder to prevent overwriting
SESSION_ID = f"MANIFOLD_SAMPLING_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if not os.path.exists(SESSION_ID):
    os.makedirs(SESSION_ID)

# ==========================================
# 2. FILE DISCOVERY & OMNI-PARSER
# ==========================================
def find_random_source(directory="."):
    valid_files = [f for f in os.listdir(directory) 
                   if f.endswith('.txt') and f.startswith(VALID_PREFIXES)]
    valid_files = [f for f in valid_files 
                   if os.path.getsize(os.path.join(directory, f)) < MAX_FILE_SIZE_MB * 1024 * 1024]
    
    if not valid_files:
        return None, None
    
    target = random.choice(valid_files)
    with open(target, 'r', encoding='utf-8', errors='ignore') as f:
        return target, f.read()

def parse_omni_format(raw_data):
    """
    Highly flexible parser that splits by 9-digit IDs and detects 
    Format 1 (Continuous) vs Format 2 (Discrete) automatically.
    """
    # Split by looking for the 9-digit ID at start of lines or blocks
    blocks = re.split(r'(?=\d{9})', raw_data)
    universes = []

    for block in blocks:
        if not block.strip(): continue
        
        univ = {
            'id': re.search(r'^(\d{9})', block.strip()).group(1) if re.search(r'^(\d{9})', block.strip()) else "Unknown",
            'type': "HH" if " HH" in block[:20] else "H",
            'h_rates': {}, # Mapping axis (x,y,z,w) to value
            'w_rates': {}, # Mapping plane (xy, xz, etc) to value
            'g_vals': [],
            'raw': block.strip()
        }

        # 1. Extract Continuous Rates (Format 1: y@+0.974h*)
        h_cont = re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block)
        w_cont = re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block)
        g_matches = re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)

        for axis, val in h_cont: univ['h_rates'][axis] = float(val)
        for plane, val in w_cont: univ['w_rates'][plane] = float(val)
        univ['g_vals'] = [float(g) for g in g_matches]

        # 2. Extract Discrete States (Format 2: expansion: x+y)
        # Only runs if continuous rates weren't found for that axis
        if not univ['h_rates']:
            exp_match = re.search(r'expansion:\s*([xyzw+]+)', block)
            con_match = re.search(r'contraction:\s*([xyzw+]+)', block)
            if exp_match:
                for axis in re.findall(r'[xyzw]', exp_match.group(1)):
                    univ['h_rates'][axis] = 1.0
            if con_match:
                for axis in re.findall(r'[xyzw]', con_match.group(1)):
                    univ['h_rates'][axis] = -1.0

        # 3. Extract Rotational Planes (Discrete)
        if not univ['w_rates']:
            cw_match = re.search(r'clockwise rotation:\s*([xyzw+]+)', block)
            ccw_match = re.search(r'widdershins rotation:\s*([xyzw+]+)', block)
            if cw_match:
                for plane in re.findall(r'[xyzw]{2}', cw_match.group(1)):
                    univ['w_rates'][plane] = 1.0
            if ccw_match:
                for plane in re.findall(r'[xyzw]{2}', ccw_match.group(1)):
                    univ['w_rates'][plane] = -1.0

        if univ['h_rates'] or univ['w_rates']:
            universes.append(univ)

    return universes

# ==========================================
# 3. PHYSICS ENGINE (GEMINI RECOMMENDATIONS)
# ==========================================
def calculate_advanced_metrics(univ):
    h = np.array(list(univ['h_rates'].values())) if univ['h_rates'] else np.array([0.0])
    w = np.array(list(univ['w_rates'].values())) if univ['w_rates'] else np.array([0.0])
    g_avg = np.mean(np.abs(univ['g_vals'])) if univ['g_vals'] else 0.5 # Default stiffness if uncoupled

    # 1. Hookean Metric Stress (Total Von Mises)
    # Norm of expansion + sum of torsion scaled by coupling
    metric_stress = np.linalg.norm(h) + (np.sum(np.abs(w)) * g_avg)

    # 2. Frustration Index (Directional Mass)
    # Sum of squared rates modulated by coupling
    frustration = np.sum(h**2) * g_avg + np.sum(w**2) * g_avg

    # 3. Helicity Score (Screw-Thread Index)
    # Detects if z/w expansion is geared to orthogonal rotations
    helicity = 0.0
    if 'z' in univ['h_rates'] and 'xy' in univ['w_rates']:
        helicity += univ['h_rates']['z'] * univ['w_rates']['xy'] * g_avg
    if 'w' in univ['h_rates'] and 'xz' in univ['w_rates']:
        helicity += univ['h_rates']['w'] * univ['w_rates']['xz'] * g_avg

    # 4. Gearing Ratio (Net Torsion Flux)
    gearing = np.sum(w) / (np.sum(np.abs(w)) + 1e-9)

    return {
        "Stress": round(metric_stress, 4),
        "Mass_Frustration": round(frustration, 4),
        "Helicity": round(helicity, 4),
        "Gearing": round(gearing, 4)
    }

# ==========================================
# 4. MULTI-OUTPUT GENERATORS
# ==========================================
def save_outputs(univ, metrics, file_id):
    unique_name = f"{univ['id']}_{uuid.uuid4().hex[:6]}"
    path_base = os.path.join(SESSION_ID, unique_name)

    # Output A: Matplotlib Dashboard
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"Manifold {univ['id']} Diagnostic", fontsize=14, fontweight='bold')
    
    # Chart 1: Axis Rates
    axs.bar(univ['h_rates'].keys(), univ['h_rates'].values(), color='skyblue')
    axs.set_title("Linear Strains (h*)")
    
    # Chart 2: Advanced Metrics
    axs[1].bar(metrics.keys(), metrics.values(), color='salmon')
    axs[1].set_title("Gemini Physics Indices")
    plt.savefig(f"{path_base}_dashboard.png")
    plt.close()

    # Output B: PyVista 3D Morphology
    # Deform a sphere based on x, y, z rates; color by w/helicity
    sphere = pv.Sphere(radius=1.0, phi_resolution=30, theta_resolution=30)
    x_def = univ['h_rates'].get('x', 0) * 0.5
    y_def = univ['h_rates'].get('y', 0) * 0.5
    z_def = univ['h_rates'].get('z', 0) * 0.5
    
    # Apply deformation vectors
    deformed = sphere.copy()
    deformed.points[:, 0] *= (1.0 + x_def)
    deformed.points[:, 1] *= (1.0 + y_def)
    deformed.points[:, 2] *= (1.0 + z_def)
    
    # Save as image
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(deformed, color='cyan', scalars=np.arange(deformed.n_points), cmap='magma')
    plotter.add_text(f"ID: {univ['id']}\nStress: {metrics['Stress']}", font_size=10)
    plotter.screenshot(f"{path_base}_morphology.png")

    print(f"Saved results for Universe {univ['id']} to folder: {SESSION_ID}")

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    filename, data = find_random_source()
    if data:
        catalog = parse_omni_format(data)
        if catalog:
            selected = random.choice(catalog)
            print(f"--- ANALYZING UNIVERSE {selected['id']} from {filename} ---")
            
            results = calculate_advanced_metrics(selected)
            save_outputs(selected, results, selected['id'])
            
            print(f"Stability Indices: {results}")
        else:
            print("No valid universes parsed from the file.")
    else:
        print("No valid data files found in the current directory.")