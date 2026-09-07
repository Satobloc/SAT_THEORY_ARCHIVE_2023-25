import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O2", "O3", "O8"]
STATUS = "Experimental"

# === Spinor Bundle ===
psi_plus, psi_minus = sp.symbols('psi_plus psi_minus')
Psi_bundle = sp.Matrix([psi_plus, psi_minus])
Psi_conj = Psi_bundle.T

# === Symbols for Curvature and Mass ===
m0 = sp.Symbol('m0')     # Bare mass scale
Q = sp.Symbol('Q')       # Topological index
R = sp.Symbol('R')       # Ricci scalar from SAT.O2
alpha = sp.Symbol('alpha')  # Curvature coupling coefficient

# === Effective Mass with Curvature Correction ===
meff = m0 / Q + alpha * R

# === Gamma Matrices and Covariant Derivative ===
gamma = [sp.Symbol(f'gamma_{mu}') for mu in range(4)]
D_mu = [sp.Symbol(f'D_{mu}') for mu in range(4)]

# === Curvature-Coupled Dirac Action ===
Dirac_curved_action = sum([
    (Psi_conj * gamma[mu] * D_mu[mu] * Psi_bundle)[0] for mu in range(4)
]) - meff * (Psi_conj * Psi_bundle)[0]

def get_structure():
    return {
        "Psi_bundle": Psi_bundle,
        "Psi_conjugate": Psi_conj,
        "gamma_mu": gamma,
        "D_mu": D_mu,
        "R": R,
        "alpha": alpha,
        "Q": Q,
        "meff_curved": meff,
        "Dirac_curved_action": Dirac_curved_action
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
