import os, re, random, numpy as np, pyvista as pv

def parse_id_bounded(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # This splits the file at every 9-digit sequence
    # Capturing the ID and the content following it
    entries = re.split(r'(?=\b\d{9}\b)', content)
    
    catalog = []
    for entry in entries:
        # Ensure it actually starts with a 9-digit ID
        match = re.match(r'(\d{9})(.*)', entry, re.DOTALL)
        if not match:
            continue
            
        uid, data = match.groups()
        
        # Extract kinematics from this specific entry
        univ = {
            'id': uid,
            'h': {k: 0.0 for k in 'xyzw'},
            'w': {k: 0.0 for k in ['xy','xz','xw','yz','yw','zw']}
        }
        
        # Aggressive extraction: check for axis/rotation presence in the data block
        for axis in 'xyzw':
            if f'expansion:{axis}' in data: univ['h'][axis] = 0.5
            if f'contraction:{axis}' in data: univ['h'][axis] = -0.5
            
        for rot in univ['w'].keys():
            if rot in data: univ['w'][rot] = 0.5
            
        catalog.append(univ)
    return catalog

# ... (Rest of the Observatory renderer)