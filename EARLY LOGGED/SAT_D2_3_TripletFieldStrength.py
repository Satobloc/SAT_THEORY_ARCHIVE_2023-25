import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
DERIVED = True
SOURCE_MODULES = ["O3", "O5"]
STATUS = "Experimental"

# === Indices and Symbols ===
F = []  # Field strength tensors F^a_{μν}
A_mu = [sp.Symbol(f'A_mu_SU3_{a}') for a in range(8)]  # Gauge fields
partial = lambda mu, a: sp.Symbol(f'partial_{mu}_A{a}')
f = sp.MutableDenseNDimArray(
    [sp.Symbol(f'f_su3_{a}{b}{c}') for a in range(8) for b in range(8) for c in range(8)],
    (8, 8, 8)
)

# === Build F^a_{μν} = ∂_μ A^a_ν - ∂_ν A^a_μ + g f^{abc} A^b_μ A^c_ν ===
g_SU3 = sp.Symbol('g_SU3')
F_tensor = {}

for a in range(8):
    for mu in range(4):
        for nu in range(4):
            dA_mu = partial(mu, a)
            dA_nu = partial(nu, a)
            nonlinear_term = sum([
                g_SU3 * f[a, b, c] * sp.Symbol(f'A_mu_{b}_{mu}') * sp.Symbol(f'A_mu_{c}_{nu}')
                for b in range(8) for c in range(8)
            ])
            F_tensor[f'F^{a}_{{{mu}{nu}}}'] = dA_mu - dA_nu + nonlinear_term

def get_structure():
    return {
        "A_mu_SU3": A_mu,
        "f_su3": f,
        "g_SU3": g_SU3,
        "F_mu_nu_SU3": F_tensor
    }

if __name__ == "__main__":
    struct = get_structure()
    for key, val in struct["F_mu_nu_SU3"].items():
        print(f"{key} = {val}")
