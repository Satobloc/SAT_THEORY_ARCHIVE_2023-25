# Generate and save SAT_O4_structure_lock.py
import sympy as sp

# Topological binding parameters
n, k = sp.symbols('n k', integer=True)
phi_i, phi_j = sp.symbols('phi_i phi_j')
binding_condition = sp.Eq(phi_i - phi_j, 2*sp.pi*k/n)

# Stability bound
n_max = 3

# Topological invariant Q components
L_wind, L_link, W_writhe = sp.symbols('L_wind L_link W_writhe')
Q = L_wind + L_link + W_writhe

module_code = f'''import sympy as sp

# Phase binding condition for stability
n, k = sp.symbols('n k', integer=True)
phi_i, phi_j = sp.symbols('phi_i phi_j')
binding_condition = sp.Eq(phi_i - phi_j, 2*sp.pi*k/n)

# Maximum stable bundle size
n_max = {n_max}

# Topological invariant components
L_wind, L_link, W_writhe = sp.symbols('L_wind L_link W_writhe')
Q = L_wind + L_link + W_writhe

def get_structure():
    """
    Returns the core topological definitions for SAT.O4:
    - binding_condition: phase-lock condition phi_i - phi_j = 2*pi*k/n
    - n_max: maximum stable n (<=3)
    - Q: topological invariant sum of winding, linking, writhe
    """
    return {{
        'binding_condition': binding_condition,
        'n_max': n_max,
        'Q': Q
    }}

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {{name}} ---")
        print(val)
'''

with open('/mnt/data/SAT_O4_structure_lock.py', 'w') as f:
    f.write(module_code)

print("Structure-locking module for SAT.O4 has been created and saved as /mnt/data/SAT_O4_structure_lock.py.")
