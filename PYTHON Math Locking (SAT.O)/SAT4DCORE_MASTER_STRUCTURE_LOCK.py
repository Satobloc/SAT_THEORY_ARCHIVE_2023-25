import sympy as sp

# Define all eight structure-lock modules with minimal contents

modules = {
    "SAT_O1_structure_lock.py": """import sympy as sp

# Filament embedding parameters
Ax, Ay, Az, kx, ky, kz, phi_x, phi_y, phi_z, lam = sp.symbols('Ax Ay Az kx ky kz phi_x phi_y phi_z lam')
gamma = sp.Matrix([
    lam,
    Ax * sp.sin(kx*lam + phi_x),
    Ay * sp.sin(ky*lam + phi_y),
    Az * sp.sin(kz*lam + phi_z)
])

# Tangent vector
v = sp.diff(gamma, lam)

# Transverse perturbations and momenta
xi0, xi1, xi2, xi3 = sp.symbols('xi0 xi1 xi2 xi3')
xi = sp.Matrix([xi0, xi1, xi2, xi3])
pi0, pi1, pi2, pi3 = sp.symbols('pi0 pi1 pi2 pi3')
pi = sp.Matrix([pi0, pi1, pi2, pi3])

# Hamiltonian integrand
m = sp.symbols('m')
V_tension = sp.Function('V_tension')
H_integrand = V_tension(xi0, xi1, xi2, xi3) + (pi0**2 + pi1**2 + pi2**2 + pi3**2)/(2*m)

def get_structure():
    return {
        'gamma': gamma,
        'v': v,
        'xi': xi,
        'pi': pi,
        'H_integrand': H_integrand
    }
""",

    "SAT_O2_structure_lock.py": """import sympy as sp

# Coordinates and co-metric symbols
x0, x1, x2, x3 = sp.symbols('x0 x1 x2 x3')
g00, g01, g02, g03, g11, g12, g13, g22, g23, g33 = sp.symbols(
    'g00 g01 g02 g03 g11 g12 g13 g22 g23 g33'
)

# Co-metric and metric
g_tilde = sp.Matrix([
    [g00, g01, g02, g03],
    [g01, g11, g12, g13],
    [g02, g12, g22, g23],
    [g03, g13, g23, g33]
])
g = g_tilde.inv()

# Christoffel symbols
Gamma = sp.MutableDenseNDimArray([[[0]*4 for _ in range(4)] for __ in range(4)], (4,4,4))
for lam in range(4):
    for mu in range(4):
        for nu in range(4):
            Gamma[lam, mu, nu] = sp.Rational(1, 2) * sum(
                g[lam, rho] * (
                    sp.diff(g_tilde[rho, mu], [x0, x1, x2, x3][nu]) +
                    sp.diff(g_tilde[rho, nu], [x0, x1, x2, x3][mu]) -
                    sp.diff(g_tilde[mu, nu], [x0, x1, x2, x3][rho])
                )
                for rho in range(4)
            )

def get_structure():
    return {
        'g_tilde': g_tilde,
        'g': g,
        'Gamma': Gamma
    }
""",

    "SAT_O3_structure_lock.py": """import sympy as sp
from sympy import LeviCivita

# Phase locking
phi1, phi2, n, k = sp.symbols('phi1 phi2 n k', integer=True)
binding_condition = sp.Eq(phi1 - phi2, 2*sp.pi*k/n)

# Gauge group mapping
gauge_group = {1: 'U(1)', 2: 'SU(2)', 3: 'SU(3)'}

# Generators
T_u1 = sp.symbols('T_u1')
T_su2 = sp.symbols('T_su2_0:3')
T_su3 = sp.symbols('T_su3_0:8')

# Structure constants
f_su2 = sp.MutableDenseNDimArray([
    [ [LeviCivita(a+1, b+1, c+1) for c in range(3)] for b in range(3) ]
    for a in range(3)
])
f_su3 = sp.MutableDenseNDimArray([
    sp.symbols(f'f_su3_{a}{b}{c}')
    for a in range(8) for b in range(8) for c in range(8)
], (8,8,8))

def get_structure():
    return {
        'binding_condition': binding_condition,
        'gauge_group': gauge_group,
        'T_u1': T_u1,
        'T_su2': T_su2,
        'T_su3': T_su3,
        'f_su2': f_su2,
        'f_su3': f_su3
    }
""",

    "SAT_O4_structure_lock.py": """import sympy as sp

# Binding condition
phi_i, phi_j, n, k = sp.symbols('phi_i phi_j n k', integer=True)
binding_condition = sp.Eq(phi_i - phi_j, 2*sp.pi*k/n)

# Stability
n_max = 3

# Topological invariant
L_wind, L_link, W_writhe = sp.symbols('L_wind L_link W_writhe')
Q = L_wind + L_link + W_writhe

def get_structure():
    return {
        'binding_condition': binding_condition,
        'n_max': n_max,
        'Q': Q
    }
""",

    "SAT_O5_structure_lock.py": """import sympy as sp

# Topological densities
rho_wind, rho_link, rho_triplet = sp.symbols('rho_wind rho_link rho_triplet')

# Filament scale
A, T = sp.symbols('A T')
ell_f = (2*A/T)**(sp.Rational(1,3))
eps_f2 = ell_f**2

# Gauge couplings
g_U1 = 1/sp.sqrt(rho_wind * eps_f2)
g_SU2 = 1/sp.sqrt(rho_link * eps_f2)
g_SU3 = 1/sp.sqrt(rho_triplet * eps_f2)

# Coupling ratios
ratio_SU2_U1 = sp.sqrt(rho_wind / rho_link)
ratio_SU3_SU2 = sp.sqrt(rho_link / rho_triplet)

def get_structure():
    return {
        'rho_wind': rho_wind,
        'rho_link': rho_link,
        'rho_triplet': rho_triplet,
        'ell_f': ell_f,
        'g_U1': g_U1,
        'g_SU2': g_SU2,
        'g_SU3': g_SU3,
        'ratio_SU2_U1': ratio_SU2_U1,
        'ratio_SU3_SU2': ratio_SU3_SU2
    }
""",

    "SAT_O6_structure_lock.py": """import sympy as sp

# Symbols
kappa, Lambda = sp.symbols('kappa Lambda')
R = sp.symbols('R')

# Field strengths and couplings
F_U1, F_SU2, F_SU3 = sp.symbols('F_U1 F_SU2 F_SU3')
g_U1, g_SU2, g_SU3 = sp.symbols('g_U1 g_SU2 g_SU3')

# Lagrangian densities
L_grav = (1/(2*kappa)) * R
L_gauge = 1/(4*g_U1**2) * F_U1**2 + 1/(4*g_SU2**2) * F_SU2**2 + 1/(4*g_SU3**2) * F_SU3**2
L_unified = L_grav + L_gauge + Lambda

def get_structure():
    return {
        'kappa': kappa,
        'Lambda': Lambda,
        'R': R,
        'F_U1': F_U1,
        'F_SU2': F_SU2,
        'F_SU3': F_SU3,
        'g_U1': g_U1,
        'g_SU2': g_SU2,
        'g_SU3': g_SU3,
        'L_grav': L_grav,
        'L_gauge': L_gauge,
        'L_unified': L_unified
    }
""",

    "SAT_O7_structure_lock.py": """import sympy as sp

# Tangent and normal vectors
v0, v1, v2, v3 = sp.symbols('v0 v1 v2 v3')
u0, u1, u2, u3 = sp.symbols('u0 u1 u2 u3')
v = sp.Matrix([v0, v1, v2, v3])
u = sp.Matrix([u0, u1, u2, u3])

# Misalignment angle
theta4 = sp.acos((v.dot(u)) / (sp.sqrt(v.dot(v)) * sp.sqrt(u.dot(u))))

def get_structure():
    return {
        'v': v,
        'u': u,
        'theta4': theta4
    }
""",

    "SAT_O8_structure_lock.py": """import sympy as sp

# Topological invariants
L_wind, L_link, W_writhe = sp.symbols('L_wind L_link W_writhe')
Q = L_wind + L_link + W_writhe

# Mass suppression
m0 = sp.symbols('m0')
meff = m0 / Q

def get_structure():
    return {
        'L_wind': L_wind,
        'L_link': L_link,
        'W_writhe': W_writhe,
        'Q': Q,
        'm0': m0,
        'meff': meff
    }
"""
}

# Write all modules to /mnt/data
for filename, content in modules.items():
    with open(f'/mnt/data/{filename}', 'w') as f:
        f.write(content)

print("All eight structure-lock modules have been rewritten and saved under /mnt/data.")
