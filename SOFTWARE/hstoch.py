import os, re, random, numpy as np, pyvista as pv

# ==========================================
# 1. STOCHASTIC PARSER (Latent Potential)
# ==========================================
def fuzzy_parse(data_string):
    blocks = re.split(r'(?=\b\d{9}\b)', data_string.strip())
    catalog = []
    
    for block in blocks:
        if not block[:9].isdigit(): continue
        
        # Init with RANDOMIZED latent potentials (-0.05 to 0.05)
        # This ensures no two universes are ever truly 'default'
        univ = {
            'id': block[:9],
            'h': {k: random.uniform(-0.05, 0.05) for k in 'xyzw'},
            'w': {k: random.uniform(-0.05, 0.05) for k in ['xy','xz','xw','yz','yw','zw']},
            'g': [random.uniform(0.1, 0.9)] 
        }
        
        # Overwrite with hard data if found
        for axis in 'xyzw':
            cont = re.search(fr'{axis}@([+-]?\d*\.\d+|\d+)', block)
            if cont: univ['h'][axis] = float(cont.group(1))
            
        for p in univ['w'].keys():
            cont = re.search(fr'{p}@([+-]?\d*\.\d+|\d+)', block)
            if cont: univ['w'][p] = float(cont.group(1))
            
        catalog.append(univ)
    return catalog

# ==========================================
# 2. INTERACTIVE TOPOLOGY (Interaction-Aware)
# ==========================================
class NormalizedObservatory:
    def __init__(self, univ):
        self.univ = univ
        self.plotter = pv.Plotter()
        self.plotter.set_background("black")
        
        # The base mesh is now perturbed by its latent potentials immediately
        self.mesh = pv.Sphere(radius=15, phi_resolution=100, theta_resolution=100)
        
        # INTERACTION MATRIX: Apply the 'Stochastic Pulse'
        # Rotation planes warp the expansion axes (e.g., strong XY torsion 'pinches' Z)
        self.apply_interaction()
        
        self.plotter.add_mesh(self.mesh, color='cyan', show_edges=True, opacity=0.6)
        self.plotter.show()

    def apply_interaction(self):
        pts = self.mesh.points
        # The interaction: Torsion planes create secondary distortions on linear axes
        # (e.g., Rotation around XY biases the Z-expansion)
        torsion_bias = sum(self.univ['w'].values())
        
        # Apply latent potential + defined kinematics
        pts[:, 0] *= (1.0 + self.univ['h']['x'] + (torsion_bias * 0.01))
        pts[:, 1] *= (1.0 + self.univ['h']['y'] - (torsion_bias * 0.01))
        pts[:, 2] *= (1.0 + self.univ['h']['z'] + (self.univ['g'][0] * 0.1))
        
        self.mesh.points = pts