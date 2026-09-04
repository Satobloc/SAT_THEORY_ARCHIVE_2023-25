import os, re, random, numpy as np, pyvista as pv

# ==========================================
# 0. CONFIGURATION & LIMITS
# ==========================================
BENDING_LIMIT = 0.75 

def get_compass_label(univ):
    """Reconstructs the symbolic stack (e.g., [⁺₋[ˣ [H] ᵥ]⁻₊]) from kinematics."""
    # Note: Using the first manifold found (usually 'H' or 'A') for the label
    m = next(iter(univ['manifolds'].values()))
    
    x_sig = '⁺' if m['h']['x'] > 0 else '⁻' if m['h']['x'] < 0 else ' '
    y_sig = '₊' if m['h']['y'] > 0 else '₋' if m['h']['y'] < 0 else ' '
    z_sig = '⁺' if m['h']['z'] > 0 else '⁻' if m['h']['z'] < 0 else ' '
    w_sig = '₊' if m['h']['w'] > 0 else '₋' if m['h']['w'] < 0 else ' '
    
    g_up = 'ˣ' if (m['w']['xz'] > 0 or m['w']['xw'] > 0) else \
           'ᵛ' if (m['w']['zw'] < 0 or m['w']['xz'] < 0) else ' '
    g_lo = 'ₓ' if (m['w']['xy'] > 0 or m['w']['yz'] > 0) else \
           'ᵥ' if (m['w']['yz'] < 0 or m['w']['zw'] > 0) else ' '

    return f"[{x_sig}{y_sig}[ {g_up}[H]{g_lo} ]{z_sig}{w_sig}]"

def stochastic_parse(raw_chunk):
    uid_match = re.search(r'\b\d{9}\b', raw_chunk)
    uid = uid_match.group(0) if uid_match else f"UNKNOWN_{random.randint(1000,9999)}"
    is_paired = "HH" in raw_chunk[:50]
    
    def extract_manifold(text_block):
        manifold = {'h': {k: random.uniform(-0.05, 0.05) for k in 'xyzw'},
                    'w': {k: random.uniform(-0.05, 0.05) for k in ['xy','xz','xw','yz','yw','zw']}}
        for axis, val in re.findall(r'([xyzw])@([+-]\d+\.\d+)h\*', text_block): manifold['h'][axis] = float(val)
        for plane, val in re.findall(r'([xyzw]{2})@([+-]\d+\.\d+)(?:ω|w|\\omega)\*', text_block): manifold['w'][plane] = float(val)
        return manifold

    universes = {}
    if is_paired:
        a_block = re.search(r'A:(.*?)(?=B:|$)', raw_chunk, re.DOTALL)
        b_block = re.search(r'B:(.*?)(?=pairing:|$)', raw_chunk, re.DOTALL)
        if a_block: universes['A'] = extract_manifold(a_block.group(1))
        if b_block: universes['B'] = extract_manifold(b_block.group(1))
    else:
        h_block = re.search(r'H:(.*?)(?=couplings:|$)', raw_chunk, re.DOTALL)
        universes['H'] = extract_manifold(h_block.group(1)) if h_block else extract_manifold(raw_chunk)

    # Initialize flags for the HUD telemetry
    flags = {k: 'CONSTANT' for k in ['x','y','z','w','xy','xz','xw','yz','yw','zw']}
    
    return {'id': uid, 'type': 'HH' if is_paired else 'H', 'manifolds': universes, 'flags': flags}

def render_system(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        entries = re.split(r'(?=\b\d{9}\b)', f.read())
    system = stochastic_parse(random.choice([e for e in entries if len(e) > 50]))
    
    plotter = pv.Plotter()
    plotter.set_background("black")
    
    manifold_keys = list(system['manifolds'].keys())
    base_meshes = [pv.Sphere(radius=10, phi_resolution=50, theta_resolution=50) for _ in manifold_keys]
    active_meshes = [pv.Sphere(radius=10, phi_resolution=50, theta_resolution=50) for _ in manifold_keys]
    
    for i, key in enumerate(manifold_keys):
        plotter.add_mesh(active_meshes[i], color=f"#{random.randint(0, 0xFFFFFF):06x}", show_edges=True, opacity=0.4)

    def update_time(time_step):
        stresses = {}
        for key in manifold_keys:
            m = system['manifolds'][key]
            vals = [1.0 + (m['h'][ax] * time_step * 0.05) for ax in 'xyz']
            stresses[key] = sum(max(0, 0.1 - v) for v in vals)
        shared_stress = sum(stresses.values())

        # --- HUD RENDER LOGIC ---
        compass = get_compass_label(system)
        hud_lines = [
            f"--- UNIVERSAL HUD: {system['id']} ---",
            f"COMPASS: {compass}",
            f"METRIC STRESS: {shared_stress:.3f}",
            "---------------------------"
        ]
        
        # Accessing flags from the system dict
        for a in ['w', 'z', 'y', 'x']:
            status = system['flags'].get(a, 'CONSTANT')
            val = system['manifolds'][manifold_keys[0]]['h'].get(a, 0.0)
            hud_lines.append(f"AXIS-{a.upper()}: {val:.2f} [{status}]")
        
        for p in ['zw', 'xw', 'yw', 'xz', 'yz', 'xy']:
            status = system['flags'].get(p, 'CONSTANT')
            val = system['manifolds'][manifold_keys[0]]['w'].get(p, 0.0)
            hud_lines.append(f"PLANE-{p.upper()}: {val:.2f} [{status}]")
            
        plotter.add_text("\n".join(hud_lines), position='upper_left', font_size=9, name='universal_hud', shadow=True)
        # ------------------------

        new_pts_list = []
        for i, key in enumerate(manifold_keys):
            m = system['manifolds'][key]
            pts = base_meshes[i].points.copy()
            
            # ... (Rest of your geometry update logic remains the same)
            sx = max(0.1, 1.0 + (m['h']['x'] * time_step * 0.05))
            sy = max(0.1, 1.0 + (m['h']['y'] * time_step * 0.05))
            sz = max(0.1, 1.0 + (m['h']['z'] * time_step * 0.05))

            if system['type'] == 'HH':
                if shared_stress > BENDING_LIMIT:
                    r_2d = np.linalg.norm(pts[:, :2], axis=1) + 1e-5
                    donut_radius = (shared_stress - BENDING_LIMIT) * 15.0
                    z_falloff = np.exp(-(pts[:, 2]**2) / 15.0)
                    pts[:, 0] += (pts[:, 0] / r_2d) * donut_radius * z_falloff
                    pts[:, 1] += (pts[:, 1] / r_2d) * donut_radius * z_falloff
                elif shared_stress > 0.1:
                    profile = (np.cos(pts[:, 2] / 10.0 * np.pi) + 1.0) * 0.5
                    pinch = np.exp(-(shared_stress * 0.8) * profile)
                    sx *= pinch; sy *= pinch
            
            pts[:, 0] *= sx; pts[:, 1] *= sy; pts[:, 2] *= sz
            
            angle = (m['w']['xy'] * time_step * 0.1) + (np.sign(m['w']['xy'] or 1) * shared_stress * time_step * 0.5)
            c, s = np.cos(angle), np.sin(angle)
            pts[:, 0], pts[:, 1] = (pts[:, 0] * c - pts[:, 1] * s), (pts[:, 0] * s + pts[:, 1] * c)
            new_pts_list.append(pts)

        if system['type'] == 'HH' and len(new_pts_list) >= 2:
            gap = np.linalg.norm(new_pts_list[0] - new_pts_list[1], axis=1)
            mask = gap < (0.5 + (shared_stress * 0.2))
            mid = (new_pts_list[0] + new_pts_list[1]) / 2.0
            new_pts_list[0][mask] = mid[mask]
            new_pts_list[1][mask] = mid[mask]

        for i, mesh in enumerate(active_meshes):
            mesh.points = new_pts_list[i]
            if shared_stress > 0.1: mesh.points = mesh.smooth_taubin(n_iter=10, pass_band=0.1).points

    plotter.add_slider_widget(update_time, rng=[0, 100], value=0, title=f"Evolution", 
                              pointa=(0.35, 0.05), pointb=(0.65, 0.05), style='modern')
    plotter.show()

if __name__ == "__main__":
    target = get_target_file(os.path.dirname(os.path.abspath(__file__)))
    if target: render_system(target)