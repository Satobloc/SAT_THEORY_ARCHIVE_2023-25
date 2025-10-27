#!/usr/bin/env python3
# sat_data_pipeline.py
#
# Automate running sat_dynamics.py, collecting snapshots, extracting kink centers,
# and producing a CSV plus a heatmap image of θ(x,t).

import numpy as np
import os
import subprocess
import glob
import pandas as pd
import matplotlib.pyplot as plt

# Parameters
DYNAMICS_SCRIPT = "sat_dynamics.py"  # should be in same directory
SNAP_DIR = "snapshots"
CENTER_CSV = "kink_centers.csv"
HEATMAP_PNG = "theta_heatmap.png"

def run_simulation():
    # Invoke sat_dynamics.py via subprocess, assuming it saves .npy snapshots under SNAP_DIR.
    print("Running sat_dynamics.py ... this may take a while.")
    os.makedirs(SNAP_DIR, exist_ok=True)
    result = subprocess.run(["python3", DYNAMICS_SCRIPT], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running sat_dynamics.py:")
        print(result.stderr)
        raise SystemExit("Simulation failed.")
    print(result.stdout)

def analyze_centers():
    data = []
    files = sorted(glob.glob(os.path.join(SNAP_DIR, "theta_t*.npy")))

    def find_center(theta, dx):
        idx = np.where(np.diff(np.sign(theta)) != 0)[0]
        if len(idx) == 0:
            return np.nan
        i0 = idx[0]
        t0, t1 = theta[i0], theta[i0+1]
        if (t1 - t0) == 0:
            return i0 * dx
        return (i0 * dx) - t0 * (dx / (t1 - t0))

    first_theta = np.load(files[0])
    N = len(first_theta)
    L = 50.0
    dx = L / (N - 1)

    for fname in files:
        base = os.path.basename(fname)
        idx = int(base.replace("theta_t", "").replace(".npy", ""))
        theta = np.load(fname)
        center = find_center(theta, dx)
        t_val = idx * 0.01
        data.append((t_val, center))
    df = pd.DataFrame(data, columns=["time", "center_x"])
    df.to_csv(CENTER_CSV, index=False)
    print(f"Kink centers saved to {CENTER_CSV}")

def plot_heatmap():
    files = sorted(glob.glob(os.path.join(SNAP_DIR, "theta_t*.npy")))
    snapshots = [np.load(f) for f in files]
    data_matrix = np.vstack(snapshots)
    plt.figure(figsize=(6,5))
    plt.imshow(data_matrix, aspect='auto', origin='lower', 
               extent=[0, 50.0, 0, data_matrix.shape[0]*0.01])
    plt.colorbar(label='θ(x,t)')
    plt.xlabel('x')
    plt.ylabel('t')
    plt.title('SAT Field Evolution: θ(x,t) Heatmap')
    plt.tight_layout()
    plt.savefig(HEATMAP_PNG, dpi=150)
    plt.close()
    print(f"Heatmap saved to {HEATMAP_PNG}")

def main():
    run_simulation()
    analyze_centers()
    plot_heatmap()

if __name__ == "__main__":
    main()
