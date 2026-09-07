import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O2", "O7"]
STATUS = "Experimental"

# === Time-Flow and Strain Tensor ===
u0, u1, u2, u3 = sp.symbols('u0 u1 u2 u3')
u = sp.Matrix([u0, u1, u2, u3])

S = sp.MatrixSymbol('S', 4, 4)
S_sq = sp.Trace(S.T * S)
S_scalar = sp.sqrt(S_sq)

# === Entropy Rate per Unit dφ ===
dphi = sp.Symbol('dphi')
entropy_rate = S_scalar * dphi

# === Drift Vector (Optional) ===
# Define drift as projection of strain gradient along uμ
grad_S = sp.Matrix([sp.Symbol(f'dS_d{x}') for x in ['x0', 'x1', 'x2', 'x3']])
drift_vector = S_scalar * u + grad_S

def get_structure():
    return {
        "u": u,
        "S_scalar": S_scalar,
        "entropy_rate": entropy_rate,
        "drift_vector": drift_vector
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
