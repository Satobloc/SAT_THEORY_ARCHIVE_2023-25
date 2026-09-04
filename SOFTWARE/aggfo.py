import os, re, random, numpy as np, pyvista as pv

# ==========================================
# 1. AGGRESSIVE FUZZY PARSER
# ==========================================
def fuzzy_parse(data_string):
    """
    Scrapes the document for any 9-digit sequence followed by a bracket.
    Ignores headers, metadata, and handles weird whitespace/tabs.
    """
    # Regex: Find 9 digits, then optional whitespace, then a bracket
    # The 's+' matches tabs, newlines, and non-breaking spaces
    pattern = re.compile(r'(\d{9})\s*(\[.*?\])(.*?)(?=\d{9}|$)', re.DOTALL)
    matches = pattern.findall(data_string)
    
    catalog = []
    for uid, morph, kin in matches:
        # Create a randomized potential base
        univ = {
            'id': uid,
            'h': {k: random.uniform(-0.05, 0.05) for k in 'xyzw'},
            'w': {k: random.uniform(-0.05, 0.05) for k in ['xy','xz','xw','yz','yw','zw']},
            'g': [0.5] 
        }
        
        # Scrape kinematics using flexible word boundaries
        for axis in 'xyzw':
            # Check for explicit labels
            if f'expansion:{axis}' in kin.replace(" ", ""): univ['h'][axis] = 0.5
            if f'contraction:{axis}' in kin.replace(" ", ""): univ['h'][axis] = -0.5
            
        # Scrape rotation planes
        for p in univ['w'].keys():
            if p in kin.replace(" ", ""): univ['w'][p] = 0.5
            
        catalog.append(univ)
    return catalog

# ==========================================
# 2. RENDERER (Fail-Safe)
# ==========================================
class NormalizedObservatory:
    def __init__(self, univ):
        self.plotter = pv.Plotter()
        self.plotter.set_background("black")
        mesh = pv.Sphere(radius=15, phi_resolution=50, theta_resolution=50)
        
        # Apply deformation
        pts = mesh.points
        pts[:, 0] *= (1.0 + univ['h']['x'])
        pts[:, 1] *= (1.0 + univ['h']['y'])
        pts[:, 2] *= (1.0 + univ['h']['z'])
        mesh.points = pts
        
        self.plotter.add_mesh(mesh, color='cyan', show_edges=True, opacity=0.6)
        self.plotter.add_text(f"ID: {univ['id']}", position='upper_left')
        self.plotter.show()

# ==========================================
# 3. EXECUTION
# ==========================================
if __name__ == "__main__":
    files = [f for f in os.listdir(".") if f.startswith(("SIXTY", "RANDOM_H"))]
    if files:
        target = random.choice(files)
        print(f"Loading {target}...")
        with open(target, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
            catalog = fuzzy_parse(data)
            
        if catalog:
            print(f"Found {len(catalog)} universes.")
            NormalizedObservatory(random.choice(catalog))
        else:
            print("Parser found 0 universes. Check the file format.")