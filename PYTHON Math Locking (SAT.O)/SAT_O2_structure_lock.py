# Generate and save SAT_O2_structure_lock.py using a raw string to avoid formatting issues
module_code = """import sympy as sp

# Coordinates
x0, x1, x2, x3 = sp.symbols('x0 x1 x2 x3')
coords = (x0, x1, x2, x3)

# Emergent co-metric symbols
g00, g01, g02, g03, g11, g12, g13, g22, g23, g33 = sp.symbols('g00 g01 g02 g03 g11 g12 g13 g22 g23 g33')

# Co-metric and metric
g_tilde = sp.Matrix([
    [g00, g01, g02, g03],
    [g01, g11, g12, g13],
    [g02, g12, g22, g23],
    [g03, g13, g23, g33]
])
g = g_tilde.inv()

# Christoffel symbols
Gamma = sp.MutableDenseNDimArray([[[0]*4 for _ in range(4)] for __ in range(4)], (4,4,4))
for lam in range(4):
    for mu in range(4):
        for nu in range(4):
            Gamma[lam, mu, nu] = sp.Rational(1, 2) * sum(
                g[lam, rho] * (sp.diff(g_tilde[rho, mu], coords[nu]) +
                               sp.diff(g_tilde[rho, nu], coords[mu]) -
                               sp.diff(g_tilde[mu, nu], coords[rho]))
                for rho in range(4)
            )

def get_structure():
    return {
        'g_tilde': g_tilde,
        'g': g,
        'Gamma': Gamma
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
"""

with open('/mnt/data/SAT_O2_structure_lock.py', 'w') as f:
    f.write(module_code)

print("Structure-locking module for SAT.O2 has been created and saved as /mnt/data/SAT_O2_structure_lock.py.")
