#!/usr/bin/env python3
# sat_dynamics.py
#
# Simulate 1D SAT-like field θ(x,t) with a φ^4-type potential V(θ) = 1/4 (θ^2 - 1)^2.
# Use a leapfrog integrator on a uniform grid x ∈ [0, L]. Initialize a kink at x = L/2,
# zero velocity, and track evolution, printing out the kink center vs. time.

import numpy as np
import matplotlib.pyplot as plt

# Physical parameters
L = 50.0           # Domain length
N = 500            # Number of spatial grid points
dx = L / (N - 1)   # Spatial resolution
c = 1.0            # "Wave speed" parameter

# Time-stepping parameters
dt = 0.01          # Time resolution (must satisfy CFL: c*dt/dx < 1)
T_final = 50.0     # Final simulation time
n_steps = int(T_final / dt)

# Kink parameters
theta0 = 1.0
kappa = 0.2

def initial_profile(x):
    # Kink initial condition: θ(x,0) = θ0 * tanh[kappa * (x - L/2)]
    return theta0 * np.tanh(kappa * (x - L/2.0))

def potential_derivative(theta):
    # V'(θ) for V(θ) = 1/4 (θ^2 - 1)^2 => V'(θ) = θ (θ^2 - 1)
    return theta * (theta**2 - 1.0)

def main():
    x = np.linspace(0, L, N)

    theta = initial_profile(x)
    theta_old = theta.copy()

    centers = []
    times = []

    def find_center(theta_array):
        idx = np.where(np.diff(np.sign(theta_array)) != 0)[0]
        if len(idx) == 0:
            return None
        i0 = idx[0]
        t0, t1 = theta_array[i0], theta_array[i0+1]
        if t1 - t0 == 0:
            return x[i0]
        return x[i0] - t0 * (dx / (t1 - t0))

    for n in range(n_steps):
        theta_right = np.roll(theta, -1)
        theta_left  = np.roll(theta, +1)
        theta_xx = (theta_right - 2*theta + theta_left) / (dx**2)

        laplacian_term = c**2 * theta_xx
        potential_term = - potential_derivative(theta)
        accel = laplacian_term + potential_term

        theta_new = 2.0 * theta - theta_old + (dt**2) * accel

        theta_old = theta.copy()
        theta = theta_new.copy()

        if n % 100 == 0:
            t_current = n * dt
            center_pos = find_center(theta)
            centers.append(center_pos)
            times.append(t_current)

    plt.figure(figsize=(6,4))
    plt.plot(times, centers, 'b.-')
    plt.xlabel('Time t')
    plt.ylabel('Kink center x(t)')
    plt.title('SAT Kink Propagation')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('kink_center_vs_time.png', dpi=150)
    plt.close()

    print("=== SAT Dynamics Script ===")
    print(f"Domain: x ∈ [0, {L}], grid points: {N}, dx = {dx:.3f}, dt = {dt}")
    print(f"Total time steps: {n_steps}, recorded {len(times)} center positions.")
    print("Output plot: kink_center_vs_time.png")

if __name__ == "__main__":
    main()
