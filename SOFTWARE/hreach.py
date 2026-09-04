import os, re, random, numpy as np, pandas as pd, pyvista as pv
from datetime import datetime

# ==========================================
# 1. THE PHYSICS HIERARCHY (CONSTANTS)
# ==========================================
# Defaults arranged from highest "Reach" to lowest "Reach"
HIERARCHY = {
    'h': {'w': 0.15, 'z': 0.12, 'y': 0.08, 'x': 0.05},
    'w': {'zw': 0.10, 'xw': 0.09, 'yw': 0.08, 'xz': 0.07, 'yz': 0.06, 'xy': 0.05}
}
BASE_RADIUS = 21.0
pv.global_theme.font.color = 'white'

# ==========================================
# 2. THE SYNERGY PARSER (MAXIMAL + UNCERTAIN)
# ==========================================
def synergy_parse(block):
    univ = {
        'id': re.search(r'(\d{9})', block).group(1) if re.search(r'(\d{9})', block) else "000000000",
        'h': {a: 0.0 for a in 'xyzw'}, 'w': {p: 0.0 for p in HIERARCHY['w'].keys()},
        'g': [float(g) for g in re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)] or [0.1],
        'specified': [], 'synergies': [], 'raw': block
    }
    # Load-in: Maximal extraction
    for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block):
        univ['h'][a] = float(v); univ['specified'].append(a)
    for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block):
        univ['w'][p] = float(v); univ['specified'].append(p)
    
    # [!] SYNERGY RULE: If specified effects share axes, pump the defaults
    for spec in univ['specified']:
        for h_axis, h_val in HIERARCHY['h'].items():
            if h_axis in spec and h_axis not in univ['specified']:
                univ['h'][h_axis] = h_val * 2.5 # Synergy Activation
                univ['synergies'].append(f"Boost:{h_axis}")
        for w_plane, w_val in HIERARCHY['w'].items():
            if any(char in spec for char in w_plane) and w_plane not in univ['specified']:
                univ['w'][w_plane] = w_val * 3.0
                univ['synergies'].append(f"Gear:{w_plane}")
                
    return univ

# ==========================================
# 3. INTERACTIVE SYNERGY OBSERVATORY
# ==========================================
class SynergyObservatory:
    def __init__(self, univ):
        self.univ = univ
        self.g_avg = np.mean(np.abs(univ['g']))
        # Calculate Stress based on the result of specified + synergistic forces [4, 5]
        self.total_stress = np.linalg.norm(list(univ['h'].values())) + (sum(abs(v) for v in univ['w'].values()) * self.g_avg)
        self.max_rate = max(abs(v) for v in univ['h'].values()) if any(univ['h'].values()) else 0.1

        self.plotter = pv.Plotter(title=f"Synergy Engine: {univ['id']}")
        self.plotter.set_background("black")
        
        # MESH: Multi-Gradient Layering [USER REQUEST]
        self.mesh = pv.Sphere(radius=BASE_RADIUS, phi_resolution=160, theta_resolution=160)
        self.actor = self.plotter.add_mesh(
            self.mesh.copy(), cmap='magma', opacity=0.35, # Brightness = Potential [6]
            smooth_shading=True, show_scalar_bar=False
        )
        
        # 4D Axis & HUD
        self.plotter.add_axes()
        self.plotter.add_arrows(np.array(), np.array([7])*BASE_RADIUS*1.5, color='magenta')
        self.render_hud()
        
        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, color="white")
        self.plotter.reset_camera()

    def render_hud(self):
        """Creates the 'Real' HUD list on the left screen."""
        hud_list = [f"--- UNIVERSAL HUD: {self.univ['id']} ---", f"METRIC STRESS: {self.total_stress:.3f}"]
        
        # List properties by Hierarchy
        for a in ['w', 'z', 'y', 'x']:
            status = "SPECIFIED" if a in self.univ['specified'] else "SYNERGY" if f"Boost:{a}" in self.univ['synergies'] else "CONSTANT"
            hud_list.append(f"AXIS-{a.upper()}: {self.univ['h'][a]:.2f} [{status}]")
        
        for p in ['zw', 'xw', 'yw', 'xz', 'yz', 'xy']:
            status = "SPECIFIED" if p in self.univ['specified'] else "SYNERGY" if f"Gear:{p}" in self.univ['synergies'] else "CONSTANT"
            hud_list.append(f"PLANE-{p.upper()}: {self.univ['w'][p]:.2f} [{status}]")
            
        self.plotter.add_text("\n".join(hud_list), position='upper_left', font_size=9, name='hud')

    def update_topology(self, t):
        pts = self.mesh.points.copy()
        h, w = self.univ['h'], self.univ['w']
        
        # 1. Cascading Flow (Expansion)
        pts[:, 0] *= (1.0 + h['x'] * 0.04 * t)
        pts[:, 1] *= (1.0 + h['y'] * 0.04 * t)
        pts[:, 2] *= (1.0 + h['z'] * 0.04 * t)
        
        # 2. Complex Torsion (SO(4) Tumbling) [8, 9]
        # XY Rotation
        if w['xy'] != 0:
            ang = w['xy'] * 0.08 * t
            pts[:, 0], pts[:, 1] = pts[:, 0]*np.cos(ang)-pts[:, 1]*np.sin(ang), pts[:, 0]*np.sin(ang)+pts[:, 1]*np.cos(ang)
        # XZ Rotation (Sharing 'X' axis creates secondary resultant torsion)
        if w['xz'] != 0:
            ang = w['xz'] * 0.06 * t
            pts[:, 0], pts[:, 2] = pts[:, 0]*np.cos(ang)-pts[:, 2]*np.sin(ang), pts[:, 0]*np.sin(ang)+pts[:, 2]*np.cos(ang)
        
        # 3. G-Stiffness Buckling: Tide to local Strain Gradients [10]
        if self.g_avg > 0.5:
            # Create "Metric Knots" (folds) instead of random noise
            noise = np.sin(pts[:, 2] * self.g_avg) * (self.total_stress * 0.01 * t)
            pts += (pts / BASE_RADIUS) * noise[:, np.newaxis]

        # 4. Multi-Gradient Shading: Color maps to local Helicity (Screw-motion) [1, 11]
        helicity_field = pts[:, 0] * w['yz'] + pts[:, 1] * w['xz'] + pts[:, 2] * w['xy']
        self.actor.mapper.dataset.points = pts
        self.actor.mapper.dataset.point_data['scalars'] = helicity_field
        
        # Orbit Logic
        self.plotter.camera.distance = (BASE_RADIUS * (1.0 + self.max_rate * 0.04 * t)) * 5.0
        self.plotter.camera.azimuth += 0.05

# ==========================================
# 4. RANDOM SOURCE EXECUTION
# ==========================================
if __name__ == "__main__":
    files = [f for f in os.listdir(".") if f.endswith(".txt") and "RANDOM_H" in f]
    if files:
        target = random.choice(files)
        print(f"Feeding Synergy Engine from: {target}")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        
        blocks = re.split(r'(?=\d{9})', data)
        catalog = [synergy_parse(b) for b in blocks if len(b.strip()) > 50]
        
        if catalog:
            engine = SynergyObservatory(random.choice(catalog))
            engine.plotter.show()