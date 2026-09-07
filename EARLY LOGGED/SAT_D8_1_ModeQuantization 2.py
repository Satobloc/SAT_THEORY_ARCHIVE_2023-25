import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O8"]
STATUS = "Experimental"

# === Symbols ===
n = sp.Symbol('n', integer=True)  # mode number
L = sp.Symbol('L')                # loop length or periodic domain
Q = sp.Symbol('Q')                # topological class
T, A = sp.symbols('T A')          # tension and rigidity

# === Filament Scale and Mass ===
ell_f = (2 * A / T)**(sp.Rational(1, 3))
m0 = T / ell_f
meff = m0 / Q

# === Mode Wavevector and Energy ===
k_n = 2 * sp.pi * n / L
E_n = sp.sqrt(k_n**2 + meff**2)

def get_structure():
    return {
        "k_n": k_n,
        "E_n": E_n,
        "meff": meff,
        "m0": m0,
        "ell_f": ell_f
    }

if __name__ == "__main__":
    struct = get_structure()
    for key, val in struct.items():
        print(f"{key} = {val}")
