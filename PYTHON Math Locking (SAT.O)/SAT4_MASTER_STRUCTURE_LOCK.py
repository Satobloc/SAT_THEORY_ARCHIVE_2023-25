import sympy as sp
from sympy import LeviCivita

# SAT4D Standalone Structure-Lock Module for O1–O8

def get_O1():
    Ax, Ay, Az, kx, ky, kz, phi_x, phi_y, phi_z, lam = sp.symbols(
        'Ax Ay Az kx ky kz phi_x phi_y phi_z lam'
    )
    gamma = sp.Matrix([
        lam,
        Ax * sp.sin(kx*lam + phi_x),
        Ay * sp.sin(ky*lam + phi_y),
        Az * sp.sin(kz*lam + phi_z)
    ])
    v = sp.diff(gamma, lam)
    xi0, xi1, xi2, xi3 = sp.symbols('xi0 xi1 xi2 xi3')
    xi = sp.Matrix([xi0, xi1, xi2, xi3])
    pi0, pi1, pi2, pi3 = sp.symbols('pi0 pi1 pi2 pi3')
    pi = sp.Matrix([pi0, pi1, pi2, pi3])
    m = sp.symbols('m')
    V_tension = sp.Function('V_tension')
    H_integrand = V_tension(xi0, xi1, xi2, xi3) + (pi0**2 + pi1**2 + pi2**2 + pi3**2)/(2*m)
    return {'gamma': gamma, 'v': v, 'xi': xi, 'pi': pi, 'H_integrand': H_integrand}

def get_O2():
    x0, x1, x2, x3 = sp.symbols('x0 x1 x2 x3')
    g00, g01, g02, g03, g11, g12, g13, g22, g23, g33 = sp.symbols(
        'g00 g01 g02 g03 g11 g12 g13 g22 g23 g33'
    )
    g_tilde = sp.Matrix([
        [g00, g01, g02, g03],
        [g01, g11, g12, g13],
        [g02, g12, g22, g23],
        [g03, g13, g23, g33]
    ])
    g = g_tilde.inv()
    Gamma = sp.MutableDenseNDimArray([[[0]*4 for _ in range(4)] for __ in range(4)], (4,4,4))
    coords = (x0, x1, x2, x3)
    for lam in range(4):
        for mu in range(4):
            for nu in range(4):
                Gamma[lam, mu, nu] = sp.Rational(1,2)*sum(
                    g[lam, rho]*(
                        sp.diff(g_tilde[rho, mu], coords[nu]) +
                        sp.diff(g_tilde[rho, nu], coords[mu]) -
                        sp.diff(g_tilde[mu, nu], coords[rho])
                    )
                    for rho in range(4)
                )
    return {'g_tilde': g_tilde, 'g': g, 'Gamma': Gamma}

def get_O3():
    phi1, phi2, n, k = sp.symbols('phi1 phi2 n k', integer=True)
    binding_condition = sp.Eq(phi1 - phi2, 2*sp.pi*k/n)
    gauge_group = {1: 'U(1)', 2: 'SU(2)', 3: 'SU(3)'}
    T_u1 = sp.symbols('T_u1')
    T_su2 = sp.symbols('T_su2_0:3')
    T_su3 = sp.symbols('T_su3_0:8')
    f_su2 = sp.MutableDenseNDimArray([
        [[LeviCivita(a+1, b+1, c+1) for c in range(3)] for b in range(3)]
        for a in range(3)
    ], (3,3,3))
    f_su3 = sp.MutableDenseNDimArray([
        sp.symbols(f'f_su3_{a}{b}{c}') for a in range(8) for b in range(8) for c in range(8)
    ], (8,8,8))
    return {
        'binding_condition': binding_condition,
        'gauge_group': gauge_group,
        'T_u1': T_u1,
        'T_su2': T_su2,
        'T_su3': T_su3,
        'f_su2': f_su2,
        'f_su3': f_su3
    }

def get_O4():
    phi_i, phi_j, n, k = sp.symbols('phi_i phi_j n k', integer=True)
    binding_condition = sp.Eq(phi_i - phi_j, 2*sp.pi*k/n)
    n_max = 3
    L_wind, L_link, W_writhe = sp.symbols('L_wind L_link W_writhe')
    Q = L_wind + L_link + W_writhe
    return {'binding_condition': binding_condition, 'n_max': n_max, 'Q': Q}

def get_O5():
    rho_wind, rho_link, rho_triplet = sp.symbols('rho_wind rho_link rho_triplet')
    A, T = sp.symbols('A T')
    ell_f = (2*A/T)**(sp.Rational(1,3))
    eps_f2 = ell_f**2
    g_U1 = 1/sp.sqrt(rho_wind * eps_f2)
    g_SU2 = 1/sp.sqrt(rho_link * eps_f2)
    g_SU3 = 1/sp.sqrt(rho_triplet * eps_f2)
    ratio_SU2_U1 = sp.sqrt(rho_wind / rho_link)
    ratio_SU3_SU2 = sp.sqrt(rho_link / rho_triplet)
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

def get_O6():
    kappa, Lambda = sp.symbols('kappa Lambda')
    R = sp.symbols('R')
    F_U1, F_SU2, F_SU3 = sp.symbols('F_U1 F_SU2 F_SU3')
    g_U1, g_SU2, g_SU3 = sp.symbols('g_U1 g_SU2 g_SU3')
    L_grav = (1/(2*kappa)) * R
    L_gauge = 1/(4*g_U1**2) * F_U1**2 + 1/(4*g_SU2**2) * F_SU2**2 + 1/(4*g_SU3**2) * F_SU3**2
    L_unified = L_grav + L_gauge + Lambda
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

def get_O7():
    v0, v1, v2, v3 = sp.symbols('v0 v1 v2 v3')
    u0, u1, u2, u3 = sp.symbols('u0 u1 u2 u3')
    v = sp.Matrix([v0, v1, v2, v3])
    u = sp.Matrix([u0, u1, u2, u3])
    theta4 = sp.acos((v.dot(u)) / (sp.sqrt(v.dot(v)) * sp.sqrt(u.dot(u))))
    return {'v': v, 'u': u, 'theta4': theta4}

def get_O8():
    L_wind, L_link, W_writhe = sp.symbols('L_wind L_link W_writhe')
    Q = L_wind + L_link + W_writhe
    m0 = sp.symbols('m0')
    meff = m0 / Q
    return {'L_wind': L_wind, 'L_link': L_link, 'W_writhe': W_writhe, 'Q': Q, 'm0': m0, 'meff': meff}

def get_all_structures():
    return {
        'O1': get_O1(),
        'O2': get_O2(),
        'O3': get_O3(),
        'O4': get_O4(),
        'O5': get_O5(),
        'O6': get_O6(),
        'O7': get_O7(),
        'O8': get_O8()
    }

if __name__ == "__main__":
    all_struct = get_all_structures()
    for o, struct in all_struct.items():
        print(f"=== {o} ===")
        for key, val in struct.items():
            print(f"{key}: {val}")

