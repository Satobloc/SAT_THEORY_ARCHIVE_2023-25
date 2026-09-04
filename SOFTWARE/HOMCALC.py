import os
import re
import random
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv

# ==========================================
# 1. FILE & DIRECTORY MANAGEMENT
# ==========================================
def setup_environment():
    """Ensures read-only safety and creates an output folder for exports."""
    current_dir = "."
    output_dir = os.path.join(current_dir, "ENGINE_OUTPUTS")
    os.makedirs(output_dir, exist_ok=True)
    return current_dir, output_dir

def find_and_read_random_file(directory, max_size_mb=50):
    """Scans for valid txt files and returns one at random (Read-Only)."""
    valid_prefixes = ("SIXTY THOUSAND UNIVERSES", "RANDOM_H_UNIVERSES")
    max_size_bytes = max_size_mb * 1024 * 1024
    valid_files = []

    for filename in os.listdir(directory):
        if not filename.lower().endswith(".txt"): continue
        normalized_name = filename.replace("_", " ").upper()
        if any(normalized_name.startswith(p) for p in [x.upper() for x in valid_prefixes]):
            filepath = os.path.join(directory, filename)
            if os.path.getsize(filepath) <= max_size_bytes:
                valid_files.append(filepath)
                
    if not valid_files: return None, None

    selected_file = random.choice(valid_files)
    with open(selected_file, 'r', encoding='utf-8', errors='ignore') as f:
        return selected_file, f.read()

# ==========================================
# 2. OMNI-PARSER (Handles All 6 Formats)
# ==========================================
def omni_parse_universes(data_string):
    """Universal parser that handles multi-line, continuous, discrete, and condensed formats."""
    # Split the entire document using the 9-digit ID as the anchor
    blocks = re.split(r'(?=\b\d{9}\b)', data_string.strip())
    universes = []
    
    for block in blocks:
        block = block.strip()
        if not block or not block[:9].isdigit(): continue
        
        uid = block[:9]
        
        # Detect Morphology Tags (Brackets or condensed H-symbols)
        morphologies = re.findall(r'(\[.*?\])', block)
        if not morphologies:
            # Catch concise bracketless format (e.g. ⁻H̬ˣ⁺₊)
            condensed_match = re.search(r'[^\s]*H[^\s]*', block)
            if condensed_match: morphologies = [condensed_match.group(0)]
            
        # Detect Format Attributes
        is_continuous = 'h*' in block or 'ω*' in block
        is_paired = 'HH' in block or 'pairing:' in block or 'A:' in block
        
        # Unify Kinematics: If discrete, assign them standard vector units of 1.0
        h_rates = []
        w_rates = []
        
        if is_continuous:
            h_rates = [float(v) for v in re.findall(r'@([+-]?\d+\.\d+)h\*', block)]
            w_rates = [float(v) for v in re.findall(r'@([+-]?\d+\.\d+)ω\*', block)]
        else:
            # Parse discrete and assign unit vectors
            for key, sign, target_list in [
                ('expansion', 1.0, h_rates), ('contraction', -1.0, h_rates),
                ('clockwise rotation', 1.0, w_rates), ('widdershins rotation', -1.0, w_rates)
            ]:
                match = re.search(fr'{key}:\s*([a-z+]+)', block)
                if match:
                    axes = match.group(1).split('+')
                    target_list.extend([sign] * len(axes))

        # Extract Coupling Moduli
        g_vals = [float(v) for v in re.findall(r'\[g=([+-]?\d+\.\d+)\]', block)]
        if not g_vals: g_vals = [0.0] # Default to 0 if no explicit couplings exist

        universes.append({
            'id': uid,
            'type': 'HH (Paired)' if is_paired else 'H (Single)',
            'morphology': morphologies,
            'h_rates': np.array(h_rates) if h_rates else np.array([0.0]),
            'w_rates': np.array(w_rates) if w_rates else np.array([0.0]),
            'g_vals': np.array(g_vals),
            'raw': block
        })
    return universes

# ==========================================
# 3. COSMOLOGICAL EVOLUTION DATA
# ==========================================
def generate_evolution_data(univ, out_dir):
    """Calculates temporal coupling evolutions and saves a matplotlib chart."""
    h = univ['h_rates']
    w = univ['w_rates']
    g_avg = np.mean(univ['g_vals'])
    
    base_stress = np.linalg.norm(h) + (np.sum(np.abs(w)) * np.abs(g_avg))
    base_helicity = g_avg * np.mean(h) * np.mean(w) if h.size > 0 and w.size > 0 else 0
    
    # Simulate an epoch from T=0 to T=100
    time_steps = np.linspace(0, 100, 100)
    
    # Simple evolution model: Stress scales exponentially with coupling over time
    # Helicity oscillates if torsion is present
    evolution_stress = base_stress * np.exp(g_avg * 0.02 * time_steps)
    evolution_helicity = base_helicity * np.cos(np.mean(w) * 0.1 * time_steps) * np.exp(-np.abs(g_avg) * 0.01 * time_steps)

    plt.figure(figsize=(10, 5))
    plt.plot(time_steps, evolution_stress, label='Metric Stress (Hookean)', color='crimson', linewidth=2)
    plt.plot(time_steps, evolution_helicity, label='Helicity (Flow)', color='teal', linewidth=2)
    plt.title(f"Cosmological Evolution: Universe {univ['id']}")
    plt.xlabel("Epoch Time (T)")
    plt.ylabel("Kinematic Magnitude")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Save chart to the output directory
    save_path = os.path.join(out_dir, f"EVOL_DATA_{univ['id']}.png")
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    return save_path

# ==========================================
# 4. 3D RENDERER (PYVISTA)
# ==========================================
def render_3d(univ):
    """Spatial 3D projection of the dimensional arrays."""
    pv.global_theme.background = '#111111'
    plotter = pv.Plotter(title=f"Universe {univ['id']} Morphology")
    
    mesh = pv.Sphere(radius=1.0, theta_resolution=50, phi_resolution=50)
    
    # Apply generalized deformation based on net h_rates
    net_strain = np.sum(univ['h_rates'])
    sx = max(0.2, 1.0 + (net_strain * 0.1))
    sy = max(0.2, 1.0 + (net_strain * 0.15)) # slight arbitrary offset for visual distinction
    sz = max(0.2, 1.0 - (net_strain * 0.05))
    
    mesh = mesh.scale([sx, sy, sz], inplace=False)
    
    # Color mapping based on net torsion and coupling
    w_sum = np.sum(univ['w_rates'])
    if w_sum > 0: color = "orange"
    elif w_sum < 0: color = "cyan"
    else: color = "white"

    plotter.add_mesh(mesh, color=color, show_edges=True, edge_color='#444444', opacity=0.9)
    plotter.add_bounding_box(color='white')
    
    info_text = f"ID: {univ['id']}\nType: {univ['type']}\nStrains (h*): {len(univ['h_rates'])}\nTorsions (w*): {len(univ['w_rates'])}\nAvg Coupling (g): {np.mean(univ['g_vals']):.3f}"
    plotter.add_text(info_text, position='upper_left', color='white', font_size=10)
    
    print("\n[!] Launching 3D Render Window. Close the window to exit the engine.")
    plotter.show()

# ==========================================
# 5. EXECUTION
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