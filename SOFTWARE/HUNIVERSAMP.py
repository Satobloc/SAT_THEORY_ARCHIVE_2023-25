import os
import re
import random
import numpy as np
import pyvista as pv

# ==========================================
# 1. FILE DISCOVERY & FILTERING
# ==========================================
def find_and_read_random_file(directory=".", max_size_mb=50):
    valid_prefixes = ("SIXTY THOUSAND UNIVERSES", "RANDOM_H_UNIVERSES")
    max_size_bytes = max_size_mb * 1024 * 1024
    valid_files = []

    for filename in os.listdir(directory):
        if not filename.lower().endswith(".txt"):
            continue
            
        normalized_name = filename.replace("_", " ").upper()
        normalized_prefixes = [p.replace("_", " ").upper() for p in valid_prefixes]
        
        if any(normalized_name.startswith(p) for p in normalized_prefixes):
            filepath = os.path.join(directory, filename)
            if os.path.getsize(filepath) <= max_size_bytes:
                valid_files.append(filepath)
                
    if not valid_files:
        print(f"No valid .txt files under {max_size_mb}MB found.")
        return None, None

    selected_file = random.choice(valid_files)
    print(f"Selected Data File: {selected_file}")
    
    with open(selected_file, 'r', encoding='utf-8', errors='ignore') as f:
        return selected_file, f.read()

# ==========================================
# 2. DISCRETE PARSER (FORMAT 2)
# ==========================================
def parse_discrete_universes(data_string):
    """Parses line-by-line discrete states instead of continuous rates."""
    universes = []
    lines = data_string.strip().split('\n')
    
    for line in lines:
        if not line.strip() or not line[0].isdigit():
            continue
            
        # Extract ID and Morphology Bracket
        match = re.match(r'^(\d{9})\s+(\[.*?\])\s+(.*)', line)
        if not match: continue
        
        uid, morphology, kinematics = match.groups()
        
        # Helper to extract dimensions (e.g., "x+y+w" -> ['x', 'y', 'w'])
        def extract_dims(keyword):
            k_match = re.search(fr'{keyword}:\s*([a-z+]+)', kinematics)
            return k_match.group(1).split('+') if k_match else []
            
        universes.append({
            'id': uid,
            'morphology': morphology,
            'exp': extract_dims('expansion'),
            'con': extract_dims('contraction'),
            'cw': extract_dims('clockwise rotation'),
            'ccw': extract_dims('widdershins rotation'),
            'raw': line
        })
    return universes

# ==========================================
# 3. 3D MORPHOLOGY RENDERER (PYVISTA)
# ==========================================
def render_3d_morphology(univ, filename):
    """Uses PyVista to render a 3D representation of the universe's dimensional state."""
    pv.global_theme.background = 'black'
    plotter = pv.Plotter(title=f"Universe {univ['id']} - Morphological State")
    
    # 1. Base Core (The 'H' particle)
    mesh = pv.Sphere(radius=1.0, theta_resolution=60, phi_resolution=60)
    
    # 2. Apply Linear Strains (Scale X, Y, Z)
    sx, sy, sz = 1.0, 1.0, 1.0
    strain_factor = 0.6 # How dramatic the stretch/squash is
    
    if 'x' in univ['exp']: sx += strain_factor
    if 'x' in univ['con']: sx -= strain_factor
    if 'y' in univ['exp']: sy += strain_factor
    if 'y' in univ['con']: sy -= strain_factor
    if 'z' in univ['exp']: sz += strain_factor
    if 'z' in univ['con']: sz -= strain_factor
    
    # Prevent inverting the mesh if compression is total
    sx, sy, sz = max(0.1, sx), max(0.1, sy), max(0.1, sz)
    mesh = mesh.scale([sx, sy, sz], inplace=False)
    
    # 3. Handle 4D (w-axis) via Color Mapping
    # If w expands, it shifts red/hot. If w contracts, blue/cold.
    w_state = "Neutral"
    base_color = "white"
    if 'w' in univ['exp']:
        base_color = "crimson"
        w_state = "Hyperspatial Expansion"
    elif 'w' in univ['con']:
        base_color = "cyan"
        w_state = "Hyperspatial Contraction"
        
    # 4. Generate visual representation of rotation (Torsion)
    torsion_text = f"CW: {', '.join(univ['cw']) if univ['cw'] else 'None'}\n"
    torsion_text += f"CCW: {', '.join(univ['ccw']) if univ['ccw'] else 'None'}"
    
    # Render Mesh
    plotter.add_mesh(mesh, color=base_color, show_edges=True, edge_color='gray', opacity=0.85)
    
    # Add Bounding Box and Axes for spatial reference
    plotter.add_bounding_box(color='white', line_width=2)
    plotter.add_axes()
    
    # Add On-Screen Diagnostics
    file_basename = os.path.basename(filename) if filename else "Unknown File"
    plotter.add_text(f"ID: {univ['id']}\nSource: {file_basename}\nMorphology: {univ['morphology']}", 
                     position='upper_left', color='white', font_size=12)
    plotter.add_text(f"W-Axis (4D): {w_state}\n\nTorsional Planes:\n{torsion_text}", 
                     position='upper_right', color='yellow', font_size=10)
    
    print("\n[!] Launching PyVista Interactive Window. Close the window to end the script.")
    plotter.show()

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    current_dir = "."
    selected_filename, raw_data = find_and_read_random_file(directory=current_dir, max_size_mb=50)
    
    if raw_data:
        catalog = parse_discrete_universes(raw_data)
        
        if catalog:
            selected_universe = random.choice(catalog)
            
            print(f"\n--- ISOLATING UNIVERSE {selected_universe['id']} ---")
            print(f"Morphology Vector: {selected_universe['morphology']}")
            print(f"Expansions: {selected_universe['exp']}")
            print(f"Contractions: {selected_universe['con']}")
            print(f"CW Torsion: {selected_universe['cw']}")
            print(f"CCW Torsion: {selected_universe['ccw']}")
            
            render_3d_morphology(selected_universe, selected_filename)
        else:
            print("Failed to parse the discrete format. Check the document format.")