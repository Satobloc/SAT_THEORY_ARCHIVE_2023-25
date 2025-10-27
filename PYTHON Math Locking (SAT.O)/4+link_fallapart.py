import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation

def make_ring(radius, offset, plane='xy', n_points=200):
    theta = np.linspace(0, 2 * np.pi, n_points)
    if plane == 'xy':
        x = radius * np.cos(theta) + offset[0]
        y = radius * np.sin(theta) + offset[1]
        z = np.zeros_like(theta) + offset[2]
    else:
        x = radius * np.cos(theta) + offset[0]
        y = radius * np.sin(theta) + offset[1]
        z = radius * np.sin(theta) + offset[2]
    return x, y, z

# Setup figure
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Make 4 loose rings
offsets = [(-2, 0, 0), (0, -2, 0), (0, 0, -2), (2, 2, 2)]
colors = ['magenta', 'cyan', 'yellow', 'orange']
rings = []
lines = []

for offset, color in zip(offsets, colors):
    x, y, z = make_ring(1, offset, 'xy')
    line, = ax.plot([], [], [], lw=2, color=color, label=f'Filament {color.capitalize()}')
    rings.append((x, y, z))
    lines.append(line)

move_vectors = [(0.02, 0, 0), (0, 0.02, 0), (0, 0, 0.02), (-0.02, -0.02, 0)]

def init():
    ax.set_xlim(-4, 4)
    ax.set_ylim(-4, 4)
    ax.set_zlim(-4, 4)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Unstable 4-Link (Tetraquark Analog)')
    ax.legend()
    return lines

def animate(i):
    for idx, (x, y, z) in enumerate(rings):
        shift = move_vectors[idx]
        lines[idx].set_data(x + shift[0] * i, y + shift[1] * i)
        lines[idx].set_3d_properties(z + shift[2] * i)
    return lines

ani = animation.FuncAnimation(fig, animate, frames=100, init_func=init,
                              blit=True, interval=100, repeat=False)

plt.close(fig)

from IPython.display import HTML
HTML(ani.to_jshtml())
