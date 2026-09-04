import os, re, random, numpy as np, pyvista as pv
from datetime import datetime

# ==========================================
# 1. THE PHYSICS HIERARCHY (LAWS OF NATURE)
# ==========================================
# Hierarchical Constants arranged by 'Reach'
CONSTANTS = {
    'h': {'w': 0.15, 'z': 0.12, 'y': 0.08, 'x': 0.05}, # Expansion constants
    'w': {'zw': 0.10, 'xw': 0.09, 'yw': 0.08, 'xz': 0.07, 'yz': 0.06, 'xy': 0.05} # Torsion constants
}
pv.global_theme.font.color = 'white'
pv.global_theme.background = 'black'

# ==========================================
# 2. THE STOCHASTIC SYNERGY PARSER
# ==========================================
def synergy_ingestor(block):
    """maximal + uncertain: finds rates, keywords, and signs to fill 4D slots."""
    univ = {
        'id': re.search(r'(\d{9})', block).group(1) if re.search(r'(\d{9})', block) else "000000000",
        'h': {a: CONSTANTS['h'][a] for a in 'xyzw'}, # Default to hierarchy
        'w': {p: CONSTANTS['w'][p] for p in CONSTANTS['w'].keys()},
        'g': [float(g) for g in re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)] or [0.1],
        'flags': {k: 'CONSTANT' for k in ['x','y','z','w','xy','xz','xw','yz','yw','zw']},
        'raw': block
    }
    
    # PASS 1: Extract Exact Rates (Format 1)
    for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block):
        univ['h'][a] = float(v); univ['flags'][a] = 'SPECIFIED'
    for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block):
        univ['w'][p] = float(v); univ['flags'][p] = 'SPECIFIED'
    
    # PASS 2: Keyword Activation (Format 2)
    for a in 'xyzw':
        if f'expansion: {a}' in block or f'+{a}' in block:
            univ['h'][a] = 1.2; univ['flags'][a] = 'ACTIVE' # Specified bigger than constant
        if f'contraction: {a}' in block or f'-{a}' in block:
            univ['h'][a] = -1.2; univ['flags'][a] = 'ACTIVE'

    # PASS 3: SYNERGY RULE - If a slot is SPECIFIED, pump related constants
    for key, flag in univ['flags'].items():
        if flag in ('SPECIFIED', 'ACTIVE'):
            # Pump any Hierarchy Constant that shares an axis with the trigger
            for slot in univ['flags'].keys():
                if univ['flags'][slot] == 'CONSTANT' and any(char in key for char in slot):
                    if slot in univ['h']: univ['h'][slot] *= 2.5
                    if slot in univ['w']: univ['w'][slot] *= 3.0
                    univ['flags'][slot] = 'SYNERGY'
    return univ

# ==========================================
# 3. INTERACTIVE SYNERGY OBSERVATORY
# ==========================================
class SynergyObservatory:
    def __init__(self, univ):
        self.univ = univ
        self.base_r = 21.0
        self.g_avg = np.mean(np.abs(univ['g']))
        # Move logic BEFORE plotter to avoid AttributeError
        self.max_rate = max(abs(v) for v in univ['h'].values())
        self.stress = np.linalg.norm(list(univ['h'].values())) + (sum(abs(v) for v in univ['w'].values()) * self.g_avg)

        self.plotter = pv.Plotter(title=f"Synergy Observer: {univ['id']}")
        
        # MESH: Transparent twilight shell [Source 26, 4.8 code]
        self.base_mesh = pv.Sphere(radius=self.base_r, phi_resolution=160, theta_resolution=160)
        self.shell_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), cmap='twilight', opacity=0.35, smooth_shading=True
        )
        
        # NUCLEUS: Inner Tension Core
        self.nuc_mesh = pv.Sphere(radius=self.base_r*0.4, phi_resolution=50, theta_resolution=50)
        self.nuc_actor = self.plotter.add_mesh(self.nuc_mesh.copy(), color='white', opacity=0.8)

        # FIXED ARRAYS: Magenta W-Pole [Source 132, History]
        self.plotter.add_arrows(np.array(), np.array([3])*self.base_r*1.5, color='magenta')
        self.plotter.add_axes()

        self.render_synergy_hud()
        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, color="white")
        self.plotter.add_key_event('s', self.plotter.screenshot)

    def render_synergy_hud(self):
        """Builds the hierarchy list down the left side."""
        hud = [f"U-ID: {self.univ['id']} [SYNERGY ENGINE]", f"METRIC STRESS: {self.stress:.3f}", "---"]
        # Axes
        for a in ['w','z','y','x']:
            hud.append(f"{a.upper()}-FLOW: {self.univ['h'][a]:.2f} [{self.univ['flags'][a]}]")
        # Planes
        for p in ['zw','xw','yw','xz','yz','xy']:
            hud.append(f"{p.upper()}-TWIST: {self.univ['w'][p]:.2f} [{self.univ['flags'][p]}]")
        self.plotter.add_text("\n".join(hud), position='upper_left', font_size=9, name='hud')

    def update_topology(self, t):
        pts = self.base_mesh.points.copy()
        h, w = self.univ['h'], self.univ['w']
        
        # 1. Homogeneous Synergistic Flow
        pts[:, 0] *= (1.0 + h['x'] * 0.04 * t)
        pts[:, 1] *= (1.0 + h['y'] * 0.04 * t)
        pts[:, 2] *= (1.0 + h['z'] * 0.04 * t)
        
        # 2. Torsional Precession Rule: If coupled, rotation axis wobbles [UNEXPECTED EFFECT]
        for plane, rate in w.items():
            if rate == 0: continue
            ang = rate * 0.08 * t
            # Standard XY Rotation
            if plane == 'xy':
                x, y = pts[:, 0], pts[:, 1]
                pts[:, 0], pts[:, 1] = x*np.cos(ang)-y*np.sin(ang), x*np.sin(ang)+y*np.cos(ang)
            # Synergy-triggered Precession (XZ)
            if plane == 'xz' and self.univ['flags']['xz'] == 'SYNERGY':
                ang *= 1.5 # Boosted speed
                x, z = pts[:, 0], pts[:, 2]
                pts[:, 0], pts[:, 2] = x*np.cos(ang)-z*np.sin(ang), x*np.sin(ang)+z*np.cos(ang)

        # 3. G-Stiffness Folds (Metric Knots)
        if self.g_avg > 0.4:
            # Use a sine wave instead of noise for 'Geographical' ripples
            folds = np.sin(pts[:, 2] * 0.5) * (self.stress * 0.01 * t)
            pts += (pts / self.base_r) * folds[:, np.newaxis]
            
        self.shell_actor.mapper.dataset.points = pts
        
        # Nucleus expansion tied to W-axis pole
        n_pts = self.nuc_mesh.points.copy()
        n_pts *= (1.0 + h['w'] * 0.02 * t)
        self.nuc_actor.mapper.dataset.points = n_pts

        # CAMERA ORBIT
        self.plotter.camera.distance = (self.base_r * (1.0 + self.max_rate * 0.04 * t)) * 5.0
        self.plotter.camera.azimuth += 0.05

# ==========================================
# 4. IGNITION (THE GOLD STANDARD)
# ==========================================
if __name__ == "__main__":
    # Robust file selection using prefixes [1, 2]
    prefixes = ("SIXTY", "RANDOM_H", "TRILLION")
    files = [f for f in os.listdir(".") if f.endswith(".txt") and f.startswith(prefixes)]
    
    if files:
        target = random.choice(files)
        print(f"Stochastic Target: {target}")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            # Split chunks using the Gold Standard ID regex [1, 2]
            entries = re.split(r'(?=\b\d{9}\b)', f.read())
            
        valid = [e for e in entries if len(e) > 50]
        if valid:
            selected_data = synergy_ingestor(random.choice(valid))
            print(f"Observing Synergy for {selected_data['id']}...")
            obs = SynergyObservatory(selected_data)
            obs.plotter.show()