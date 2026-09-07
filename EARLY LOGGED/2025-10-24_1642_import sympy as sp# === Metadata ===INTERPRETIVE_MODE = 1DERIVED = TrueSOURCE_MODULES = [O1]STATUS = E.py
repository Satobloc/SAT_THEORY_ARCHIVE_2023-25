import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1"]
STATUS = "Experimental"

# === Transverse Perturbation Field ===
xi0, xi1, xi2, xi3 = sp.symbols('xi0 xi1 xi2 xi3')
xi = sp.Matrix([xi0, xi1, xi2, xi3])

# === Basic Norm ===
xi_dot_xi = xi.dot(xi)

# === Higher-Order Self-Interaction Terms ===
lambda4, lambda6 = sp.symbols('lambda4 lambda6')
L_self = lambda4 * xi_dot_xi**2 + lambda6 * xi_dot_xi**3

def get_structure():
    return {
        "xi": xi,
        "xi_dot_xi": xi_dot_xi,
        "L_self": L_self,
        "terms": {
            "quartic": lambda4 * xi_dot_xi**2,
            "sextic": lambda6 * xi_dot_xi**3
        }
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
