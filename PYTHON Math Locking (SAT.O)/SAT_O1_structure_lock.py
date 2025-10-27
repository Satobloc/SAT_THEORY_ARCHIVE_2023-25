import sympy as sp

# Define symbols
Ax, Ay, Az, kx, ky, kz, phi_x, phi_y, phi_z, lam, m = sp.symbols('Ax Ay Az kx ky kz phi_x phi_y phi_z lam m')
xi0, xi1, xi2, xi3 = sp.symbols('xi0 xi1 xi2 xi3')

# Filament embedding γμ(λ)
gamma = sp.Matrix([
    lam,
    Ax * sp.sin(kx*lam + phi_x),
    Ay * sp.sin(ky*lam + phi_y),
    Az * sp.sin(kz*lam + phi_z)
])

# Tangent vector vμ(λ)
v = sp.diff(gamma, lam)

# Transverse perturbation ξμ(λ) placeholders
xi = sp.Matrix([xi0, xi1, xi2, xi3])

# Canonical momenta πμ(λ) = m * dξμ/dλ (symbolic placeholder)
pi = sp.symbols('pi0:4')
pi_vec = sp.Matrix(pi)

# Hamiltonian integrand H = 1/(2m) π·π + V_tension(ξ)
V_tension = sp.Function('V_tension')
H_integrand = (1/(2*m)) * (pi_vec.dot(pi_vec)) + V_tension(*xi)

# Package into a structure-locking module
code = f"""
import sympy as sp

# Parameters
Ax, Ay, Az, kx, ky, kz, phi_x, phi_y, phi_z, lam, m = sp.symbols('Ax Ay Az kx ky kz phi_x phi_y phi_z lam m')
xi0, xi1, xi2, xi3 = sp.symbols('xi0 xi1 xi2 xi3')

# Filament embedding γμ(λ)
gamma = sp.Matrix([
    lam,
    Ax * sp.sin(kx*lam + phi_x),
    Ay * sp.sin(ky*lam + phi_y),
    Az * sp.sin(kz*lam + phi_z)
])

# Tangent vector vμ(λ)
v = sp.diff(gamma, lam)

# Transverse perturbation ξμ(λ)
xi = sp.Matrix([xi0, xi1, xi2, xi3])

# Canonical momenta πμ(λ)
pi = sp.symbols('pi0:4')
pi_vec = sp.Matrix(pi)

# Hamiltonian integrand
V_tension = sp.Function('V_tension')
H_integrand = (1/(2*m)) * (pi_vec.dot(pi_vec)) + V_tension(*xi)

def get_structure():
    return {{
        'gamma': gamma,
        'v': v,
        'xi': xi,
        'pi': pi_vec,
        'H_integrand': H_integrand
    }}

if __name__ == "__main__":
    struct = get_structure()
    for name, val in struct.items():
        print(f"--- {{name}} ---")
        print(val)
"""

# Write the structure-locking code to file
with open('/mnt/data/SAT_O1_structure_lock.py', 'w') as f:
    f.write(code)

# Display summary and instructions
print("Structure-locking module for SAT.O1 has been created and saved as /mnt/data/SAT_O1_structure_lock.py.")
print("Please upload this file into your Project Files folder, then we can run it to lock in the O1 definitions before proceeding with derivations.")
