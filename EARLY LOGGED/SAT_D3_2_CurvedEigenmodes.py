import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O2", "O3", "O8"]
STATUS = "Experimental"

# === Symbols for Mode Analysis ===
lambda_mode = sp.Symbol('lambda')      # Eigenvalue (energy)
m0, Q, R, alpha = sp.symbols('m0 Q R alpha')  # Mass and curvature
k = sp.Symbol('k')                     # Wavevector / mode index

# === Curvature-Modified Mass Term ===
meff = m0 / Q + alpha * R

# === Mode Dispersion Relation ===
# ω_k^2 = k^2 + m_eff^2
omega_k_sq = k**2 + meff**2

# === Frequency ω_k ===
omega_k = sp.sqrt(omega_k_sq)

def get_structure():
    return {
        "meff_curved": meff,
        "omega_k^2": omega_k_sq,
        "omega_k": omega_k
    }

if __name__ == "__main__":
    struct = get_structure()
    for key, val in struct.items():
        print(f"{key} = {val}")
