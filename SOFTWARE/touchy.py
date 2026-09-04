import os, re, random, numpy as np, pyvista as pv

# ==========================================
# 0. GLOBAL STABILITY CONSTANTS
# ==========================================
MIN_DIMENSION_PCT = 0.2
MIN_VOLUME_PCT = 0.6
MAX_ASPECT_RATIO = 2.5

def get_target_file(directory):
    files = [f for f in os.listdir(directory) if f.endswith(".txt")]
    primary = [f for f in files if f.startswith("RANDOM_H_UNIVERSES")]
    if primary: return os.path.join(directory, random.choice(primary))
    fallback = [f for f in files if f.startswith("SIXTY THOUSAND UNIVERSES")]
    if fallback: return os.path.join(directory, random.choice(fallback))
    return None

def stochastic_parse(raw_chunk):
    uid = re.search(r'\b\d{9}\b', raw_chunk)
    uid = uid.group(0) if uid else f"UNKNOWN_{random.randint(1000,9999)}"
    is_paired = "HH" in raw_chunk[:50]
    
    def extract_manifold(text_block):
        m = {'h': {k: random.uniform(-0.05, 0.05) for k in 'xyzw'},
             'w': {k: random.uniform(-0.05, 0.05) for k in ['xy','xz','xw','yz','yw','zw']}}
        for axis, val in re.findall(r'([xyzw])@([+-]\d+\.\d+)h\*', text_block): m['h'][axis] = float(val)
        return m

    universes = {}
    if is_paired:
        a = re.search(r'A:(.*?)(?=B:|$)', raw_chunk, re.DOTALL)
        b = re.search(r'B:(.*?)(?=pairing:|$)', raw_chunk, re.DOTALL)
        if a: universes['A'] = extract_manifold(a.group(1))
        if b: universes['B'] = extract_manifold(b.group(1))
    else:
        h = re.search(r'H:(.*?)(?=couplings:|$)', raw_chunk, re.DOTALL)
        universes['H'] = extract_manifold(h.group(1)) if h else extract_manifold(raw_chunk)
    return {'id': uid, 'type': 'HH' if is_paired else 'H', 'manifolds': universes}

def render_system(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        entries = re.split(r'(?=\b\d{9}\b)', f.read())
    system = stochastic_parse(random.choice([e for e in entries if len(e) > 50]))
    
    plotter = pv.Plotter()
    plotter.set_background("black")
    
    # Store reference to original base shapes so we don't distort the source mesh
    base_geoms = [pv.Sphere(radius=10, phi_resolution=50, theta_resolution=50) for _ in system['manifolds']]
    meshes = [pv.Sphere(radius=10, phi_resolution=50, theta_resolution=50) for _ in system['manifolds']]
    
    for i, key in enumerate(system['manifolds']):
        plotter.add_mesh(meshes[i], color=f"#{random.randint(0, 0xFFFFFF):06x}", show_edges=True, opacity=0.5)

    def update_time(t):
        keys = list(system['manifolds'].keys())
        shared_stress = 0
        
        # Calculate stress
        for i, key in enumerate(keys):
            m = system['manifolds'][key]
            sx = 1.0 + (m['h']['x'] * t * 0.05)
            sy = 1.0 + (m['h']['y'] * t * 0.05)
            sz = 1.0 + (m['h']['z'] * t * 0.05)
            shared_stress += max(0, MIN_DIMENSION_PCT - sx) + max(0, MIN_DIMENSION_PCT - sy) + max(0, MIN_DIMENSION_PCT - sz)

        for i, key in enumerate(keys):
            m = system['manifolds'][key]
            pts = base_geoms[i].points.copy() # Start from pristine base geometry
            
            sx = max(MIN_DIMENSION_PCT, 1.0 + (m['h']['x'] * t * 0.05))
            sy = max(MIN_DIMENSION_PCT, 1.0 + (m['h']['y'] * t * 0.05))
            sz = max(MIN_DIMENSION_PCT, 1.0 + (m['h']['z'] * t * 0.05))
            
            # Apply Pinch/Expansion
            if system['type'] == 'HH' and shared_stress > 0.1:
                z_f = pts[:, 2] / 10.0 
                pinch = np.exp(-(shared_stress * 0.5) * ((np.cos(z_f * np.pi) + 1.0) * 0.5))
                sx *= pinch; sy *= pinch
                sz *= (1.0 / (pinch**2))
            
            # Aspect Ratio check
            dims = np.array([sx, sy, sz])
            if np.max(dims) / np.max([np.min(dims), 0.01]) > MAX_ASPECT_RATIO:
                long_idx = np.argmax(dims)
                dims[long_idx] *= 0.9 
                dims[dims != dims[long_idx]] *= 1.05 
                sx, sy, sz = dims

            # Apply scaling
            pts[:, 0] *= sx; pts[:, 1] *= sy; pts[:, 2] *= sz
            
            # Update the mesh
            meshes[i].points = pts
            meshes[i].points = meshes[i].smooth_taubin(n_iter=5, pass_band=0.1).points

    plotter.add_slider_widget(update_time, rng=[0, 100], value=0, title=f"Evolution: {system['id']}", 
                              pointa=(0.025, 0.1), pointb=(0.31, 0.1), style='modern')
    plotter.show()

if __name__ == "__main__":
    path = get_target_file(os.path.dirname(os.path.abspath(__file__)))
    if path: render_system(path)