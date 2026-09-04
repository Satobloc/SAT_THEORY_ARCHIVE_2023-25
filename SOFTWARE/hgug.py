import os, re, random, numpy as np, pandas as pd, pyvista as pv
from datetime import datetime

# ==========================================
# 1. THE GREEDY OMNI-PARSER (MAXIMAL + UNCERTAIN)
# ==========================================
DEFAULT_VAL = 0.8   # Magnitude if axis is named but has no number
EPSILON = 0.001     # Baseline metric activity for unmentioned slots

def greedy_parse(block):
    """
    Search-and-Slot algorithm: Identifies axis/plane mentions anywhere in text.
    Prioritizes 'Maximal + Uncertain' data over 'Minimal + Sure' data.
    """
    univ = {
        'id': re.search(r'(\d{9})', block).group(1) if re.search(r'(\d{9})', block) else "000000000",
        'h': {a: EPSILON for a in 'xyzw'},
        'w': {p: EPSILON for p in ['xy','xz','xw','yz','yw','zw']},
        'g': [float(g) for g in re.findall(r'\[g=([-+]?\d*\.\d+|\d+)\]', block)] or [0.5],
        'raw': block.strip()
    }
    # Pass 1: Floating point rates (Format 1)
    for a, v in re.findall(r'([xyzw])@([-+]?\d*\.\d+|\d+)h\*', block): univ['h'][a] = float(v)
    for p, v in re.findall(r'([xyzw]{2})@([-+]?\d*\.\d+|\d+)ω\*', block): univ['w'][p] = float(v)
    
    # Pass 2: Keyword/Sign Search (Format 2 and Condensed)
    for a in 'xyzw':
        if univ['h'][a] == EPSILON:
            if re.search(f'expansion.*{a}', block, re.I) or f'+{a}' in block: univ['h'][a] = DEFAULT_VAL
            if re.search(f'contraction.*{a}', block, re.I) or f'-{a}' in block: univ['h'][a] = -DEFAULT_VAL
    for p in univ['w'].keys():
        if univ['w'][p] == EPSILON:
            if re.search(f'rotation.*{p}', block, re.I) or f'{p}' in block: univ['w'][p] = DEFAULT_VAL
            
    return univ

# ==========================================
# 2. GREEDY OBSERVATORY ENGINE (STABLE)
# ==========================================
class GreedyObservatory:
    def __init__(self, univ):
        # [!] FIX 1: Move all variable assignments BEFORE plotter/widget creation
        self.univ = univ
        self.base_radius = 21.0
        self.max_rate = max(abs(v) for v in univ['h'].values())
        self.g_avg = np.mean(np.abs(univ['g']))
        # Metric Stress driving the HUD and serration intensity [4, 5]
        self.stress = np.linalg.norm(list(univ['h'].values())) + (sum(abs(v) for v in univ['w'].values()) * self.g_avg)

        self.plotter = pv.Plotter(title=f"Greedy Observer: {univ['id']}")
        self.plotter.set_background("black")
        
        # MESH 1: The Transparent Manifold (Twilight colormap for buckling)
        self.base_mesh = pv.Sphere(radius=self.base_radius, phi_resolution=160, theta_resolution=160)
        self.shell_actor = self.plotter.add_mesh(
            self.base_mesh.copy(), cmap='twilight', smooth_shading=True,
            opacity=0.3, name='shell', show_scalar_bar=False
        )
        
        # MESH 2: Tension Nucleus (Internal Core reacting to G-Coupling) [6]
        self.inner_r = self.base_radius * 0.4
        self.nuc_mesh = pv.Sphere(radius=self.inner_r, phi_resolution=50, theta_resolution=50)
        self.nuc_actor = self.plotter.add_mesh(
            self.nuc_mesh.copy(), color='white', opacity=0.7, name='nuc'
        )

        # [!] FIX 2: Correct NumPy Vector Arguments for W-Axis projection
        w_origin = np.array([0.0, 0.0, 0.0])
        w_dir = np.array([1.0, 1.0, 1.0]) * (self.base_radius * 1.5)
        self.plotter.add_arrows(w_origin, w_dir, mag=1, color='magenta')
        self.plotter.add_point_labels([w_dir], ["W-POLE"], font_size=12, text_color='magenta')
        self.plotter.add_axes()

        # HUD: Map potential to color (Cyan -> Yellow -> Red) [IDEAS 5]
        hud_color = 'red' if self.stress > 2.0 else 'yellow' if self.stress > 1.0 else 'cyan'
        compass = f"[{'+' if univ['h']['x']>0 else '-' if univ['h']['x']<0 else ' '}" \
                  f"{'+' if univ['h']['y']>0 else '-' if univ['h']['y']<0 else ' '}[H]" \
                  f"{'+' if univ['h']['z']>0 else '-' if univ['h']['z']<0 else ' '}" \
                  f"{'+' if univ['h']['w']>0 else '-' if univ['h']['w']<0 else ' '}]"
        
        info = f"ID: {univ['id']}\nSTRESS: {self.stress:.3f}\nCOMPASS: {compass}"
        self.plotter.add_text(info, position='upper_left', font_size=10, color=hud_color)

        self.plotter.add_slider_widget(self.update_topology, [0.0, 200.0], value=0.0, color="white")
        self.plotter.reset_camera()
        self.plotter.add_key_event('s', self.plotter.screenshot)

    def update_topology(self, t):
        # 1. EVOLVE SHELL (4D Homogeneous Flow)
        pts = self.base_mesh.points.copy()
        pts[:, 0] *= (1.0 + self.univ['h']['x'] * 0.04 * t)
        pts[:, 1] *= (1.0 + self.univ['h']['y'] * 0.04 * t)
        pts[:, 2] *= (1.0 + self.univ['h']['z'] * 0.04 * t)

        # 2. SO(4) MULTI-PLANE TORSION [4]
        if self.univ['w']['xy'] != 0:
            ang = self.univ['w']['xy'] * 0.1 * t
            x, y = pts[:, 0], pts[:, 1]
            pts[:, 0], pts[:, 1] = x*np.cos(ang)-y*np.sin(ang), x*np.sin(ang)+y*np.cos(ang)
        
        # 3. METRIC BUCKLING (Serrations from 000000033) [7]
        if self.stress > 1.2:
            pts += np.random.normal(0, 0.004 * self.stress * (t / 15), pts.shape)
        self.shell_actor.mapper.dataset.points = pts

        # 4. EVOLVE NUCLEUS (Internal Reaction to W-Expansion)
        n_pts = self.nuc_mesh.points.copy()
        n_pts *= (1.0 + self.univ['h']['w'] * 0.02 * t)
        self.nuc_actor.mapper.dataset.points = n_pts

        # CAMERA: Normalizing for observability [8]
        dist = (self.base_radius * (1.0 + self.max_rate * 0.04 * t)) * 5.5
        self.plotter.camera.distance = dist
        self.plotter.camera.azimuth += 0.05
        self.plotter.camera.focal_point = (0, 0, 0)

# ==========================================
# 3. EXECUTION (PRIORITIZING RANDOM_H)
# ==========================================
if __name__ == "__main__":
    # Priority Loading: Specifically target complex H_RANDOM files as requested
    all_files = [f for f in os.listdir(".") if f.endswith(".txt") and "RANDOM_H" in f]
    if not all_files:
        all_files = [f for f in os.listdir(".") if f.endswith(".txt")]
    
    if all_files:
        target = random.choice(all_files)
        print(f"Observatory Loading: {target}")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        
        # Greedy Multi-Format Splitting
        blocks = re.split(r'(?=\d{9})', data)
        catalog = [greedy_parse(b) for b in blocks if len(b.strip()) > 50]
        
        if catalog:
            selected = random.choice(catalog)
            print(f"--- OBSERVING UNIVERSE {selected['id']} ---")
            obs = GreedyObservatory(selected)
            obs.plotter.show()