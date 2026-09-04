import os
import re
import random
import numpy as np
import pyvista as pv

# ==========================================
# 1. DIAGNOSTIC SCANNER (The Sweep)
# ==========================================
def perform_universe_sweep(catalog):
    """Sweeps the catalog and returns the top 3 most 'interesting' universes."""
    def complexity_score(u):
        # Score = (Avg Coupling * 10) + (Number of Rotation Planes * 5)
        return (np.mean(np.abs(u['g_vals'])) * 10) + (len(u['w_rates']) * 5)
    
    sorted_catalog = sorted(catalog, key=complexity_score, reverse=True)
    return sorted_catalog[:3] # Returns the top 3 outliers

# ==========================================
# 2. ENHANCED 3D RENDERING (Visualizing Structure)
# ==========================================
def render_3d_complex(univ):
    """Maps rotation planes as vectors/arrows onto the 3D morphology."""
    plotter = pv.Plotter(title=f"Universe {univ['id']} Structural Analysis")
    
    # Base Mesh
    mesh = pv.Sphere(radius=1.0, theta_resolution=40, phi_resolution=40)
    plotter.add_mesh(mesh, color='white', opacity=0.3, show_edges=True)
    
    # Map Rotational Planes as structural indicators
    # Logic: If 'xy' is a rotation plane, place a ring or arrow on the XY plane
    if len(univ['w_rates']) > 0:
        # Simple structural map: add arrows to show torsional axes
        arrows = pv.Arrow(start=(0,0,0), direction=(1,1,1), scale=1.5)
        plotter.add_mesh(arrows, color='yellow')
        
    plotter.add_text(f"ID: {univ['id']} | Complexity: High", position='upper_left')
    plotter.show()

# ==========================================
# 3. OMNI-PARSER (Same logic, better data extraction)
# ==========================================
def omni_parse_universes(data_string):
    blocks = re.split(r'(?=\b\d{9}\b)', data_string.strip())
    universes = []
    for block in blocks:
        if not block[:9].isdigit(): continue
        
        # Extract everything effectively
        g_vals = [float(v) for v in re.findall(r'\[g=([+-]?\d+\.\d+)\]', block)]
        w_rates = re.findall(r'rotation:\s*([a-z+]+)', block)
        
        universes.append({
            'id': block[:9],
            'g_vals': np.array(g_vals) if g_vals else np.array([0.0]),
            'w_rates': w_rates,
            'raw': block
        })
    return universes

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    work_dir, out_dir = setup_environment()
    selected_filename, raw_data = find_and_read_random_file(work_dir)
    
    if raw_data:
        catalog = omni_parse_universes(raw_data)
        if catalog:
            univ = random.choice(catalog)
            
            # 1. Terminal Telemetry
            print("\n" + "="*50)
            print(f"OMNI-ENGINE: DIAGNOSTIC REPORT")
            print("="*50)
            print(f"Target ID     : {univ['id']}")
            print(f"Manifold Type : {univ['type']}")
            print(f"Morphologies  : {' | '.join(univ['morphology']) if univ['morphology'] else 'Unknown'}")
            print(f"Linear Vector : {univ['h_rates']}")
            print(f"Spin Vector   : {univ['w_rates']}")
            print(f"Couplings (g) : {univ['g_vals']}")
            
            # 2. Cosmological Evolution 
            chart_path = generate_evolution_data(univ, out_dir)
            print(f"\n[+] Saved Evolution Chart: {chart_path}")
            
            # 3. Launch 3D Topology
            render_3d(univ)
        else:
            print("Parser yielded no valid H/HH targets from the selected file.")
    print("Omni-Engine Ready. System Sweep functionality integrated.")