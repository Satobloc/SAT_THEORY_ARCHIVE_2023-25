import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O2", "O3", "O8"]
STATUS = "Experimental"

# === Spinor Field and Conjugate ===
psi_plus, psi_minus = sp.symbols('psi_plus psi_minus', cls=sp.Function)
x = sp.Symbol('x')
psi_plus = psi_plus(x)
psi_minus = psi_minus(x)
Psi_bundle = sp.Matrix([psi_plus, psi_minus])
Psi_conj = Psi_bundle.T

# === Gamma Matrices and Covariant Derivatives ===
gamma = [sp.Symbol(f'gamma_{mu}') for mu in range(4)]
D_mu = [sp.Symbol(f'D_{mu}') for mu in range(4)]

# === Mass Suppression with Curvature ===
m0, Q, R, alpha = sp.symbols('m0 Q R alpha')
meff = m0 / Q + alpha * R

# === Curved Dirac Action ===
Dirac_action = sum([
    (Psi_conj * gamma[mu] * D_mu[mu] * Psi_bundle)[0] for mu in range(4)
]) - meff * (Psi_conj * Psi_bundle)[0]

# === Variational Derivative Placeholder ===
# In full generality this would require functional variation, but symbolically we can define:
variation_psi = sp.diff(Dirac_action, psi_plus)
variation_conj = sp.diff(Dirac_action, psi_minus)

def get_structure():
    return {
        "Psi_bundle": Psi_bundle,
        "meff_curved": meff,
        "Dirac_action": Dirac_action,
        "variation_wrt_psi_plus": variation_psi,
        "variation_wrt_psi_minus": variation_conj
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
