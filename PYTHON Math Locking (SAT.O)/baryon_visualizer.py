# SAT SU(3) Quark Binding — Clean Visualization (Colab)
import numpy as np, matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from IPython.display import HTML

# Parameters
A, Z_amp, omega = 1.0, 0.5, 2.0
dt, t_max = 0.1, 20
t_vals = np.arange(0, t_max, dt)

# SU(3) phase-locked triplet: R, G, B
phases = {'R': 0, 'G': 2*np.pi/3, 'B': 4*np.pi/3}
shifts = {'R': (0.05,0,0), 'G': (0,0.05,0), 'B': (0,0,0.05)}
colors = {'R': 'red', 'G': 'green', 'B': 'blue'}

# Plot setup
fig = plt.figure(figsize=(10,8))
ax = fig.add_subplot(111, projection='3d')
lines = {k: ax.plot([], [], [], lw=2, color=colors[k])[0] for k in phases}
traces = {k: {'x': [], 'y': [], 'z': []} for k in phases}

def init():
    ax.set(xlim=(-1.5*A,1.5*A), ylim=(-1.5*A,1.5*A), zlim=(-1.5*Z_amp,1.5*Z_amp),
           xlabel='X', ylabel='Y', zlabel='Z (Σₜ)',
           title='SAT SU(3) Triplet — Baryon Binding (Q=3)')
    [ax.plot([],[],[], color=colors[k], label=f'{k}-filament') for k in phases]
    ax.legend()
    return list(lines.values())

def animate(i):
    t = t_vals[i]
    for k, phi in phases.items():
        dx,dy,dz = shifts[k]
        x = A * np.sin(omega*t + phi) + dx
        y = A * np.cos(omega*t + phi) + dy
        z = Z_amp * np.sin(3*t) + dz
        traces[k]['x'].append(x)
        traces[k]['y'].append(y)
        traces[k]['z'].append(z)
        lines[k].set_data(traces[k]['x'], traces[k]['y'])
        lines[k].set_3d_properties(traces[k]['z'])
    return list(lines.values())

ani = FuncAnimation(fig, animate, frames=len(t_vals), init_func=init,
                    blit=True, interval=50, repeat=False)
plt.close(fig)
HTML(ani.to_jshtml())
