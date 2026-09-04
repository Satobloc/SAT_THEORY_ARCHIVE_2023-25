import os, re, random, numpy as np, pyvista as pv

# ==========================================
# 1. DIRECTORY SCANNER & TARGET ACQUISITION
# ==========================================
def get_target_file(directory):
    print("\nScanning local directory for universe clusters...")
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return None
    
    # Priority 1: RANDOM_H_UNIVERSES
    primary_targets = [f for f in files if f.startswith("RANDOM_H_UNIVERSES") and f.endswith(".txt")]
    if primary_targets:
        chosen_file = random.choice(primary_targets)
        print(f"[SUCCESS] Primary target acquired: {chosen_file}")
        return os.path.join(directory, chosen_file)
        
    # Priority 2: SIXTY THOUSAND UNIVERSES
    fallback_targets = [f for f in files if f.startswith("SIXTY THOUSAND UNIVERSES") and f.endswith(".txt")]
    if fallback_targets:
        chosen_file = random.choice(fallback_targets)
        print(f"[FALLBACK] Secondary target acquired: {chosen_file}")
        return os.path.join(directory, chosen_file)
        
    print("[FATAL] No valid universe data files found in the directory.")
    return None

# ==========================================
# 2. STOCHASTIC INGESTOR
# ==========================================
def stochastic_parse(raw_chunk):
    uid_match = re.search(r'\b\d{9}\b', raw_chunk)
    uid = uid_match.group(0) if uid_match else f"UNKNOWN_{random.randint(1000,9999)}"
    
    is_paired = "HH" in raw_chunk[:50]
    
    def extract_manifold(text_block):
        manifold = {
            'h': {k: random.uniform(-0.05, 0.05) for k in 'xyzw'},
            'w': {k: random.uniform(-0.05, 0.05) for k in ['xy','xz','xw','yz','yw','zw']}
        }
        
        h_matches = re.findall(r'([xyzw])@([+-]\d+\.\d+)h\*', text_block)
        for axis, val in h_matches:
            manifold['h'][axis] = float(val)
            
        w_matches = re.findall(r'([xyzw]{2})@([+-]\d+\.\d+)(?:ω|w|\\omega)\*', text_block)
        for plane, val in w_matches:
            manifold['w'][plane] = float(val)
            
        return manifold

    universes = {}
    if is_paired:
        a_block = re.search(r'A:(.*?)(?=B:|$)', raw_chunk, re.DOTALL)
        b_block = re.search(r'B:(.*?)(?=pairing:|$)', raw_chunk, re.DOTALL)
        if a_block: universes['A'] = extract_manifold(a_block.group(1))
        if b_block: universes['B'] = extract_manifold(b_block.group(1))
    else:
        h_block = re.search(r'H:(.*?)(?=couplings:|$)', raw_chunk, re.DOTALL)
        if h_block: universes['H'] = extract_manifold(h_block.group(1))
        else: universes['H'] = extract_manifold(raw_chunk)

    couplings = []
    coupling_matches = re.findall(r'(C\d+)\{(.*?)\}\[g=([+-]\d+\.\d+)\]', raw_chunk)
    for c_id, nodes_raw, g_val in coupling_matches:
        nodes = [n.strip() for n in re.split(r'↔|<->', nodes_raw)]
        couplings.append({'id': c_id, 'nodes': nodes, 'g': float(g_val)})

    return {'id': uid, 'type': 'HH' if is_paired else 'H', 'manifolds': universes, 'couplings': couplings}

def fetch_random_system(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    entries = re.split(r'(?=\b\d{9}\b)', content)
    valid_entries = [e for e in entries if len(e) > 50] 
    
    target_chunk = random.choice(valid_entries)
    return stochastic_parse(target_chunk)


# ==========================================
# 3. THE KINEMATIC RENDERER
# ==========================================
def render_system(file_path):
    system = fetch_random_system(file_path)
    
    plotter = pv.Plotter()
    plotter.set_background("black")
    
    base_meshes = []
    active_meshes = []
    manifold_keys = list(system['manifolds'].keys())
    
    print(f"\n--- INITIATING SYSTEM {system['id']} ({system['type']}) ---")
    
    for key in manifold_keys:
        manifold = system['manifolds'][key]
        print(f"Manifold {key}: H-Strains {manifold['h']}")
        
        # Spawn at origin
        mesh = pv.Sphere(radius=10, phi_resolution=50, theta_resolution=50)
        base_meshes.append(mesh.copy())
        active_meshes.append(mesh)
        
        random_hex = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        plotter.add_mesh(mesh, color=random_hex, show_edges=True, opacity=0.4, name=f"manifold_{key}")

    print(f"Couplings Found: {len(system['couplings'])}")

####
    def update_time(time_step):
        stresses = {}
        for key in manifold_keys:
            manifold = system['manifolds'][key]
            sx_raw = 1.0 + (manifold['h']['x'] * time_step * 0.05)
            sy_raw = 1.0 + (manifold['h']['y'] * time_step * 0.05)
            sz_raw = 1.0 + (manifold['h']['z'] * time_step * 0.05)
            
            floor = 0.1
            stresses[key] = max(0, floor - sx_raw) + max(0, floor - sy_raw) + max(0, floor - sz_raw)
            
        shared_hh_stress = sum(stresses.values())

        # Store calculated points before applying them so we can check for intersections
        new_pts_list = []

        for i, key in enumerate(manifold_keys):
            manifold = system['manifolds'][key]
            base = base_meshes[i]
            pts = base.points.copy()
            
            # 1. Base Strain & Null Avoidance
            sx_raw = 1.0 + (manifold['h']['x'] * time_step * 0.05)
            sy_raw = 1.0 + (manifold['h']['y'] * time_step * 0.05)
            sz_raw = 1.0 + (manifold['h']['z'] * time_step * 0.05)
            floor = 0.1
            
            sx = max(floor, sx_raw)
            sy = max(floor, sy_raw)
            sz = max(floor, sz_raw)
            my_stress = stresses[key]
            
            if system['type'] == 'HH':
                # Phase 1: Waist Constriction
                if shared_hh_stress > 0.1:
                    z_factor = pts[:, 2] / 10.0 
                    pinch_depth = shared_hh_stress * 0.8
                    profile = (np.cos(z_factor * np.pi) + 1.0) * 0.5 
                    pinch = np.exp(-pinch_depth * profile)
                    sx *= pinch
                    sy *= pinch
                    
                # Phase 2: Toroidal Inversion
                if shared_hh_stress > 0.6:
                    pts[:, 0] *= sx
                    pts[:, 1] *= sy
                    pts[:, 2] *= sz
                    
                    r_2d = np.linalg.norm(pts[:, :2], axis=1) + 1e-5
                    donut_hole_radius = (shared_hh_stress - 0.6) * 15.0 
                    z_falloff = np.exp(-(pts[:, 2]**2) / 15.0)
                    
                    pts[:, 0] += (pts[:, 0] / r_2d) * donut_hole_radius * z_falloff
                    pts[:, 1] += (pts[:, 1] / r_2d) * donut_hole_radius * z_falloff
                    pts[:, 2] *= max(0.2, 1.0 - ((shared_hh_stress - 0.6) * 0.3))
                    
                    sx = sy = sz = 1.0 
            else:
                if my_stress > 0:
                    sx += (max(0, floor - sy_raw) + max(0, floor - sz_raw)) * 0.8
                    sy += (max(0, floor - sx_raw) + max(0, floor - sz_raw)) * 0.8
                    sz += (max(0, floor - sx_raw) + max(0, floor - sy_raw)) * 0.8
                    
                if my_stress > 0.05:
                    radii = np.linalg.norm(pts, axis=1)
                    ripple = np.sin(base.points[:, 2] * 4.0 + (time_step * 2.0)) * (my_stress * 1.5)
                    pts += (pts / (radii[:, None] + 1e-5)) * ripple[:, None]
                    
            # 2. Finalize Scale
            pts[:, 0] *= sx
            pts[:, 1] *= sy
            pts[:, 2] *= sz
            
            # 3. Torsion
            base_w = manifold['w']['xy']
            spin_dir = np.sign(base_w) if base_w != 0 else 1.0 
            panic_spin = spin_dir * (shared_hh_stress if system['type'] == 'HH' else my_stress) * time_step * 0.5
            angle = (base_w * time_step * 0.1) + panic_spin
            
            if angle != 0:
                cos_a, sin_a = np.cos(angle), np.sin(angle)
                x_val, y_val = pts[:, 0].copy(), pts[:, 1].copy()
                pts[:, 0] = (x_val * cos_a - y_val * sin_a)
                pts[:, 1] = (x_val * sin_a + y_val * cos_a)
                
            new_pts_list.append(pts)

        # 4. INTERSECTION RE-COUPLING (The Weld)
        if system['type'] == 'HH' and len(new_pts_list) >= 2:
            pts_A = new_pts_list[0]
            pts_B = new_pts_list[1]
            
            # Measure the gap between corresponding vertices
            gap = np.linalg.norm(pts_A - pts_B, axis=1)
            
            # If the shells get too close (meaning they are colliding or intersecting)
            weld_threshold = 0.5 + (shared_hh_stress * 0.2) 
            weld_mask = gap < weld_threshold
            
            # Snap the colliding points to their exact midpoint, permanently webbing them
            if np.any(weld_mask):
                midpoints = (pts_A + pts_B) / 2.0
                new_pts_list[0][weld_mask] = midpoints[weld_mask]
                new_pts_list[1][weld_mask] = midpoints[weld_mask]

        # 5. ASSIGNMENT & TOPOLOGICAL RELAXATION
        for i, key in enumerate(manifold_keys):
            mesh = active_meshes[i]
            mesh.points = new_pts_list[i]
            
            # Only run the Taubin smoother if the system is under actual stress
            if shared_hh_stress > 0.1 or stresses[key] > 0.05:
                mesh.points = mesh.smooth_taubin(n_iter=10, pass_band=0.1).points

    plotter.add_slider_widget(
        update_time, 
        rng=[0, 100],      
        value=0,          
        title=f"Evolution: System {system['id']}", 
        pointa=(0.025, 0.1), 
        pointb=(0.31, 0.1),
        style='modern'
    )
    
    ui_text = f"System: {system['id']} [{system['type']}]\nCouplings: {len(system['couplings'])}"
    plotter.add_text(ui_text, position='upper_left', font_size=12)
    plotter.show()

# ==========================================
# 4. IGNITION
# ==========================================
if __name__ == "__main__":
    # Uses the directory where this Python script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    target_path = get_target_file(base_dir)
    
if target_path:
        render_system(target_path)