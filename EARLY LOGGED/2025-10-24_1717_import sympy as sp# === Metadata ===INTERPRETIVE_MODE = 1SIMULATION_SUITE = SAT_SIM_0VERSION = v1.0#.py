import sympy as sp

# === Metadata ===
INTERPRETIVE_MODE = 1
SIMULATION_SUITE = "SAT_SIM_0"
VERSION = "v1.0"

# === Inputs ===
T, A = sp.symbols('T A')  # Tension, rigidity
Q = sp.Symbol('Q')        # Topological class
n = sp.Symbol('n', integer=True)  # Mode index
L = sp.Symbol('L')        # Filament length
phi = sp.Symbol('phi')    # Emergent time

# === Derived Quantities ===
ell_f = (2*A/T)**(sp.Rational(1,3))
m0 = T / ell_f
meff = m0 / Q

# === Mode Energy ===
k_n = 2 * sp.pi * n / L
E_n = sp.sqrt(k_n**2 + meff**2)

# === Cosmological Scale Factor ===
S0, Lambda = sp.symbols('S0 Lambda')
a_phi = sp.exp(sp.sqrt(S0**2 + Lambda) * phi)

# === Output Panel ===
def get_outputs():
    return {
        'ell_f': ell_f,
        'm0': m0,
        'meff': meff,
        'k_n': k_n,
        'E_n': E_n,
        'a(phi)': a_phi
    }

if __name__ == "__main__":
    outputs = get_outputs()
    for key, val in outputs.items():
        print(f"{key} = {val}")
