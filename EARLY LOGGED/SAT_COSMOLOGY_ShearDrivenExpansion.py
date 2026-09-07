import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
STATUS = "Validated"

# === Symbols ===
phi = sp.Symbol('phi')
S0, beta, Lambda = sp.symbols('S0 beta Lambda')

# === Shear Model ===
S_phi = S0 + beta * phi

# === Friedmann-Like Equation ===
H_phi = sp.sqrt(S_phi**2 + Lambda)
a_phi = sp.exp(sp.integrate(H_phi, phi))

def get_structure():
    return {
        "S(phi)": S_phi,
        "H(phi)": H_phi,
        "a(phi)": a_phi
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {name} ---")
        print(val)
