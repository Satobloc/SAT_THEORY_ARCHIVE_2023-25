import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O2", "O3", "O8"]
STATUS = "Experimental"

# === Spinor Bundle ===
psi_plus, psi_minus = sp.symbols('psi_plus psi_minus')
Psi_bundle = sp.Matrix([psi_plus, psi_minus])
Psi_conj = Psi_bundle.T  # Simple transpose for symbolic conjugate

# === Gamma Matrices ===
gamma = [sp.Symbol(f'gamma_{mu}') for mu in range(4)]

# === Conserved Current j^μ = Ψ̄ γ^μ Ψ ===
j_mu = [ (Psi_conj * gamma[mu] * Psi_bundle)[0] for mu in range(4) ]

def get_structure():
    return {
        "Psi_bundle": Psi_bundle,
        "Psi_conjugate": Psi_conj,
        "gamma_mu": gamma,
        "j_mu": j_mu
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
