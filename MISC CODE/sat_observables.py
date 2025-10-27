#!/usr/bin/env python3
# sat_observables.py
#
# Load saved SAT field data (θ(x) arrays) from a directory (assumed .npy files),
# select one time index, compute the power spectral density and the spatial
# correlation function, and plot both.

import numpy as np
import os
import matplotlib.pyplot as plt

# Directory containing theta snapshots
SNAP_DIR = "snapshots"
TIME_INDEX = 100  # Analyze snapshot 'theta_t{TIME_INDEX}.npy'

def load_theta(time_index):
    filename = os.path.join(SNAP_DIR, f"theta_t{time_index}.npy")
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"Snapshot file not found: {filename}")
    return np.load(filename)

def compute_psd(theta_array, dx):
    N = len(theta_array)
    theta_k = np.fft.rfft(theta_array)
    psd_raw = np.abs(theta_k)**2 / N
    dk = 2 * np.pi / (N * dx)
    k_vals = dk * np.arange(len(psd_raw))
    return k_vals, psd_raw

def compute_spatial_correlation(theta_array):
    N = len(theta_array)
    theta_centered = theta_array - np.mean(theta_array)
    fft_vals = np.fft.fft(theta_centered)
    power = np.abs(fft_vals)**2
    corr_raw = np.fft.ifft(power).real / N
    corr = corr_raw[: N//2]
    corr /= corr[0]
    return corr

def main():
    theta = load_theta(TIME_INDEX)
    N = len(theta)
    L = 50.0
    dx = L / (N - 1)

    k_vals, psd_vals = compute_psd(theta, dx)

    plt.figure(figsize=(6,4))
    plt.loglog(k_vals[1:], psd_vals[1:], 'r-')
    plt.xlabel('Spatial frequency k')
    plt.ylabel('PSD(k)')
    plt.title(f'SAT Field Power Spectrum (t_index={TIME_INDEX})')
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('psd.png', dpi=150)
    plt.close()

    corr = compute_spatial_correlation(theta)
    r_vals = dx * np.arange(len(corr))

    plt.figure(figsize=(6,4))
    plt.plot(r_vals, corr, 'b-')
    plt.xlabel('Separation r')
    plt.ylabel('C(r) = ⟨θ(x)θ(x+r)⟩/⟨θ^2⟩')
    plt.title(f'SAT Field Auto‐Correlation (t_index={TIME_INDEX})')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('correlation.png', dpi=150)
    plt.close()

    print("=== SAT Observables Script ===")
    print(f"Loaded θ(x) with N = {N} points, dx = {dx:.4f}")
    print(f"Power spectrum saved to 'psd.png'; correlation saved to 'correlation.png'.")
    print(f"Maximum C(0) = 1.0 (normalized).")

if __name__ == "__main__":
    main()
