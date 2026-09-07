import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O3"]
STATUS = "Experimental"

# === SU(3) Generators and Structure Constants ===
T = [sp.Symbol(f'T_su3_{a}') for a in range(8)]
f = sp.MutableDenseNDimArray(
    [sp.Symbol(f'f_su3_{a}{b}{c}') for a in range(8) for b in range(8) for c in range(8)],
    (8, 8, 8)
)

# === Commutator Definition: [T^a, T^b] = i f^{abc} T^c ===
# Symbolically express the RHS of each commutator
commutators = {}
for a in range(8):
    for b in range(8):
        rhs = sum([sp.I * f[a, b, c] * T[c] for c in range(8)])
        commutators[f"[T^{a}, T^{b}]"] = rhs

def get_structure():
    return {
        "T_su3": T,
        "f_su3": f,
        "commutators": commutators
    }

if __name__ == "__main__":
    struct = get_structure()
    for k, v in struct["commutators"].items():
        print(f"{k} = {v}")
