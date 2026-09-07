import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O3", "O5", "O8"]
STATUS = "Experimental"

# === Triplet Bundle ===
psi1, psi2, psi3 = sp.symbols('psi1 psi2 psi3')
Psi_triplet = sp.Matrix([psi1, psi2, psi3])

# === SU(3) Coupling and Generators ===
g_SU3 = sp.Symbol('g_SU3')
T_su3 = [sp.Symbol(f'T_su3_{a}') for a in range(8)]  # Symbolic generators
A_mu = [sp.Symbol(f'A_mu_SU3_{a}') for a in range(8)]  # Gauge field components

# === Gamma and Partial Derivatives ===
gamma = [sp.Symbol(f'gamma_{mu}') for mu in range(4)]
partial_mu = [sp.Symbol(f'partial_{mu}') for mu in range(4)]

# === Topological Mass Suppression (Q = 3) ===
m0 = sp.Symbol('m0')
Q = 3
meff = m0 / Q

# === Gauge-Covariant Derivative DμΨ = ∂μΨ + i g T·AμΨ ===
D_mu_Psi = []
for mu in range(4):
    gauge_sum = sum([T_su3[a] * A_mu[a] for a in range(8)])
    covariant_term = sp.I * g_SU3 * gauge_sum
    D_mu_Psi.append(partial_mu[mu] * Psi_triplet + covariant_term * Psi_triplet)

# === Dirac-like Action with Gauge Coupling ===
Dirac_SU3_action = sum([
    (Psi_triplet.T * gamma[mu] * D_mu_Psi[mu])[0] for mu in range(4)
]) - meff * (Psi_triplet.T * Psi_triplet)[0]

def get_structure():
    return {
        "Psi_triplet": Psi_triplet,
        "T_su3": T_su3,
        "A_mu_SU3": A_mu,
        "gamma_mu": gamma,
        "partial_mu": partial_mu,
        "g_SU3": g_SU3,
        "D_mu_Psi": D_mu_Psi,
        "meff": meff,
        "Dirac_SU3_action": Dirac_SU3_action
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
