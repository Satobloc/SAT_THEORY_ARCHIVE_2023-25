import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O2", "O8"]
STATUS = "Experimental"

# === Symbols and Functions ===
phi = sp.Symbol('phi')
a = sp.Function('a')(phi)
Lambda = sp.Symbol('Lambda')
S0 = sp.Symbol('S0')  # Constant shear

# === Model: Constant S(φ) = S0 ===
S_phi = S0

# === Friedmann Equation ===
a_dot = sp.diff(a, phi)
H_sq = (a_dot / a)**2
Friedmann_eq = sp.Eq(H_sq, S_phi**2 + Lambda)

# === Solve for a(φ) ===
# Take square root and integrate
H = sp.sqrt(S_phi**2 + Lambda)
a_sol = sp.exp(H * phi)

def get_structure():
    return {
        "S_phi": S_phi,
        "Friedmann_eq": Friedmann_eq,
        "a(phi)_solution": a_sol
    }

if __name__ == "__main__":
    struct = get_structure()
    print("--- Friedmann Equation ---")
    print(struct["Friedmann_eq"])
    print("--- Solution a(φ) ---")
    print(struct["a(phi)_solution"])
