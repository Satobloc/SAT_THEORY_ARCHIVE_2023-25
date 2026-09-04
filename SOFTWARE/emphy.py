import os, re, random, numpy as np, pyvista as pv

def get_universe_data(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    entries = re.split(r'(?=\b\d{9}\b)', content)
    valid_entries = [e for e in entries if len(e) > 20] 
    raw_data = random.choice(valid_entries)
    
    uid = re.search(r'\d{9}', raw_data).group(0)
    univ = {'id': uid, 'h': {k: 0.0 for k in 'xyzw'}, 'w': {k: 0.0 for k in ['xy','xz','xw','yz','yw','zw']}}
    
    clean_data = re.sub(r'[^a-z0-9]', '', raw_data.lower())
    
    for axis in 'xyzw':
        if f'expansion{axis}' in clean_data: univ['h'][axis] = 1.0
        elif f'contraction{axis}' in clean_data: univ['h'][axis] = -1.0
        
    for plane in univ['w'].keys():
        if plane in clean_data: univ['w'][plane] = 1.0 
            
    return univ

def render_coupled_universes(file_path, count=3):
    plotter = pv.Plotter()
    plotter.set_background("black")
    
    universes = []
    base_meshes = []
    active_meshes = []
    
    # Initialization Phase
    for i in range(count):
        univ = get_universe_data(file_path)
        universes.append(univ)
        
        # All universes spawn at the exact same origin [0,0,0]
        mesh = pv.Sphere(radius=10, phi_resolution=60, theta_resolution=60)
        
        base_meshes.append(mesh.copy())
        active_meshes.append(mesh)
        
        random_hex = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        # Lower opacity to clearly see overlapping interactions
        plotter.add_mesh(mesh, color=random_hex, show_edges=True, opacity=0.35, name=f"univ_{i}")
        
        print(f"Loaded {univ['id']} | H: {univ['h']} | W-Planes: {[k for k,v in univ['w'].items() if v > 0]}")

    # ==========================================
    # COUPLING CALCULATIONS (Bulk Stress)
    # ==========================================
    # Sum the kinematics of all present universes to create a shared "gravity" or stress
    bulk_h = {axis: sum(u['h'][axis] for u in universes) for axis in 'xyzw'}
    coupling_strength = 0.35 # 35% of the bulk stress bleeds into individual universes

    def update_time(time_step):
        for i in range(count):
            u = universes[i]
            base = base_meshes[i]
            mesh = active_meshes[i]
            
            pts = base.points.copy()
            
            # 1. COUPLED DYNAMIC EVOLUTION
            # The universe scales by its own rules PLUS the coupled bulk stress
            sx = max(0.01, 1.0 + ((u['h']['x'] + (bulk_h['x'] * coupling_strength)) * time_step * 0.1))
            sy = max(0.01, 1.0 + ((u['h']['y'] + (bulk_h['y'] * coupling_strength)) * time_step * 0.1))
            sz = max(0.01, 1.0 + ((u['h']['z'] + (bulk_h['z'] * coupling_strength)) * time_step * 0.1))
            
            pts[:, 0] *= sx
            pts[:, 1] *= sy
            pts[:, 2] *= sz
            
            # 2. TORSION / ROTATION
            if u['w']['xy'] > 0:
                angle = time_step * 0.15 
                cos_a, sin_a = np.cos(angle), np.sin(angle)
                
                # 2D Rotation Matrix around Z-axis (XY Plane)
                x_val = pts[:, 0].copy()
                y_val = pts[:, 1].copy()
                
                pts[:, 0] = (x_val * cos_a - y_val * sin_a)
                pts[:, 1] = (x_val * sin_a + y_val * cos_a)
                
            # Update the mesh on screen
            mesh.points = pts

    # Add the UI Slider
    plotter.add_slider_widget(
        update_time, 
        rng=[0, 30],      
        value=0,          
        title="Time (T) - Coupled Evolution", 
        pointa=(0.025, 0.1), 
        pointb=(0.31, 0.1),
        style='modern'
    )
    
    plotter.add_text("Coupled Multiverse Engine", position='upper_left')
    plotter.show()

if __name__ == "__main__":
    path = r"D:\__SAT26\H_UNIVERSES\SIXTY THOUSAND UNIVERSES 5.txt"
    render_coupled_universes(path)