import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1"]
STATUS = "Experimental"

# === Transverse Perturbation Field ===
xi0, xi1, xi2, xi3 = sp.symbols('xi0 xi1 xi2 xi3')
xi = sp.Matrix([xi0, xi1, xi2, xi3])
xi_dot_xi = xi.dot(xi)

# === Self-Interaction Lagrangian ===
lambda4, lambda6 = sp.symbols('lambda4 lambda6')
L_self = lambda4 * xi_dot_xi**2 + lambda6 * xi_dot_xi**3

# === Variation: dL/dxi_μ ===
variation = [sp.diff(L_self, component) for component in xi]

def get_structure():
    return {
        "xi": xi,
        "xi_dot_xi": xi_dot_xi,
        "L_self": L_self,
        "dL_dxi": sp.Matrix(variation)
    }

if __name__ == "__main__":
    struct = get_structure()
    print("--- ∂L_self / ∂xi_μ ---")
    print(struct["dL_dxi"])
