import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O3", "O5"]
STATUS = "Experimental"

# === Symbols and Field Strength Components ===
g_SU3 = sp.Symbol('g_SU3')
F = {}
for a in range(8):
    for mu in range(4):
        for nu in range(4):
            key = f'F^{a}_{{{mu}{nu}}}'
            F[key] = sp.Symbol(key)

# === Yang–Mills Lagrangian: L = -1/4g² * Σ F^a_{μν} F^{aμν} ===
YM_Lagrangian = -1/(4 * g_SU3**2) * sum(F[key]**2 for key in F)

def get_structure():
    return {
        "F_components": F,
        "g_SU3": g_SU3,
        "L_YM_SU3": YM_Lagrangian
    }

if __name__ == "__main__":
    print(f"L_YM_SU3 = {YM_Lagrangian}")
