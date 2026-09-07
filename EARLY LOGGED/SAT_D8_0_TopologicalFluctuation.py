import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O1", "O8"]
STATUS = "Experimental"

# === Symbols ===
k = sp.Symbol('k')  # mode index
T, A = sp.symbols('T A')  # tension and rigidity
Q = sp.Symbol('Q')  # topological suppression index

# === Filament Scale ===
ell_f = (2 * A / T)**(sp.Rational(1, 3))

# === Suppressed Mass ===
m0 = T / ell_f
meff = m0 / Q

# === Mode Energy ===
omega_k = sp.sqrt(k**2 + meff**2)

def get_structure():
    return {
        "ell_f": ell_f,
        "m0": m0,
        "meff": meff,
        "omega_k": omega_k
    }

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"{name} = {val}")
