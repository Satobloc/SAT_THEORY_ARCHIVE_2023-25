import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O3", "O8"]
STATUS = "Experimental"

# === Symbols and Spinor Bundle ===
psi_plus, psi_minus = sp.symbols('psi_plus psi_minus')
Psi_bundle = sp.Matrix([psi_plus, psi_minus])

# === Topological Mass Suppression for Hopf Link (Q = 2) ===
m0 = sp.symbols('m0')
Q = 2
meff = m0 / Q

# === Emergent Gamma Matrices and Covariant Derivatives ===
gamma = [sp.Symbol(f'gamma_{mu}') for mu in range(4)]
D = [sp.Symbol(f'D_{mu}') for mu in range(4)]

# === Dirac Action ===
Dirac_action = sum([
    (Psi_bundle.T * gamma[mu] * D[mu] * Psi_bundle)[0] for mu in range(4)
]) - meff * (Psi_bundle.T * Psi_bundle)[0]

def get_structure():
    return {
        "Psi_bundle": Psi_bundle,
        "gamma_mu": gamma,
        "D_mu": D,
        "meff": meff,
        "Dirac_action": Dirac_action
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
