#!/usr/bin/env python3
# sat_geometry.py
#
# Construct a 2D triangular mesh on [0, Lx]×[0, Ly], define a toy displacement field
# u(x,y) = (alpha * x * exp(-beta*(x^2+y^2)), alpha * y * exp(-beta*(x^2+y^2)))
# Compute strain tensor u_{ij} = 0.5*(∂_i u_j + ∂_j u_i) on each triangle centroid,
# then compute action density L = 0.5 * lambda_ * (trace u)^2 + mu * u_{ij} u^{ij},
# and numerically integrate to get the total action S.

import numpy as np

# Lamé parameters (choose some representative values)
LAMBDA = 1.0   # λ
MU     = 0.5   # μ

# Domain size
Lx = 5.0
Ly = 5.0

# Number of divisions in x and y (must be even if you want symmetric)
Nx = 50
Ny = 50

# Parameterizing the toy displacement field
alpha = 0.8
beta  = 0.2

def displacement_field(x, y):
    # Toy displacement: radial “bulge” that decays away from the center.
    # u_x = alpha * x * exp(-beta * (x^2 + y^2))
    # u_y = alpha * y * exp(-beta * (x^2 + y^2))
    factor = np.exp(-beta * (x**2 + y**2))
    u_x = alpha * x * factor
    u_y = alpha * y * factor
    return u_x, u_y

def compute_strain_tensor(xc, yc, dx=1e-3):
    # Numerically compute symmetric strain tensor u_{ij} at point (xc, yc)
    # by finite differences on the toy displacement field.
    # Returns a 2×2 numpy array u.
    ux_plus, uy_plus = displacement_field(xc + dx, yc)
    ux_minus, uy_minus = displacement_field(xc - dx, yc)
    ux_x = (ux_plus - ux_minus) / (2 * dx)  # ∂_x u_x
    uy_x = (uy_plus - uy_minus) / (2 * dx)  # ∂_x u_y

    ux_plus, uy_plus = displacement_field(xc, yc + dx)
    ux_minus, uy_minus = displacement_field(xc, yc - dx)
    ux_y = (ux_plus - ux_minus) / (2 * dx)  # ∂_y u_x
    uy_y = (uy_plus - uy_minus) / (2 * dx)  # ∂_y u_y

    # Strain components: u_{ij} = 0.5 * (∂_i u_j + ∂_j u_i)
    u_xx = 0.5 * (ux_x + ux_x)
    u_yy = 0.5 * (uy_y + uy_y)
    u_xy = 0.5 * (ux_y + uy_x)
    u_yx = u_xy  # symmetric

    strain = np.array([[u_xx, u_xy],
                       [u_yx, u_yy]])
    return strain

def action_density(strain_tensor):
    # Given 2×2 strain tensor u_{ij}, compute L = 1/2 λ (trace u)^2 + μ u_{ij} u^{ij}.
    trace_u = np.trace(strain_tensor)
    contracted = np.sum(strain_tensor * strain_tensor)  # u_{ij} u_{ij}
    L = 0.5 * LAMBDA * (trace_u**2) + MU * contracted
    return L

def main():
    # Build a rectangular grid
    x_edges = np.linspace(-Lx/2, Lx/2, Nx+1)
    y_edges = np.linspace(-Ly/2, Ly/2, Ny+1)

    total_action = 0.0
    total_area = 0.0

    # Loop over each cell (i,j) -> split into two triangles
    for i in range(Nx):
        for j in range(Ny):
            x0, x1 = x_edges[i],   x_edges[i+1]
            y0, y1 = y_edges[j],   y_edges[j+1]

            triangles = [
                [(x0, y0), (x1, y0), (x1, y1)],
                [(x0, y0), (x1, y1), (x0, y1)]
            ]
            for tri in triangles:
                xs = [vertex[0] for vertex in tri]
                ys = [vertex[1] for vertex in tri]
                xc = sum(xs) / 3.0
                yc = sum(ys) / 3.0

                xA, yA = tri[0]
                xB, yB = tri[1]
                xC, yC = tri[2]
                area = abs(
                    (xA*(yB - yC) + xB*(yC - yA) + xC*(yA - yB))
                ) / 2.0

                strain = compute_strain_tensor(xc, yc)
                L_val = action_density(strain)

                total_action += L_val * area
                total_area   += area

    print("=== SAT Geometry Script ===")
    print(f"Grid: {Nx}×{Ny} cells, domain = [{-Lx/2}, {Lx/2}]×[{-Ly/2}, {Ly/2}]")
    print(f"Total triangles: {2 * Nx * Ny}")
    print(f"Integrated area (should ≈ {Lx * Ly:.4f}): {total_area:.4f}")
    print(f"Total action S ≈ {total_action:.6f}")

if __name__ == "__main__":
    main()
