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
    elif plane == 'yz':
        x = np.zeros_like(theta) + offset[0]
        y = radius * np.cos(theta) + offset[1]
        z = radius * np.sin(theta) + offset[2]
    elif plane == 'xz':
        x = radius * np.cos(theta) + offset[0]
        y = np.zeros_like(theta) + offset[1]
        z = radius * np.sin(theta) + offset[2]
    return x, y, z

# Setup figure
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Make Borromean rings
rings = []
planes = ['xy', 'yz', 'xz']
offsets = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
colors = ['red', 'green', 'blue']
lines = []

for plane, offset, color in zip(planes, offsets, colors):
    x, y, z = make_ring(1, offset, plane)
    line, = ax.plot([], [], [], lw=2, color=color, label=f'Filament {color.capitalize()}')
    rings.append((x, y, z))
    lines.append(line)

def init():
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_zlim(-2, 2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Stable Borromean Link (3-Filament Baryon)')
    ax.legend()
    return lines

def animate(i):
    angle = i * 2 * np.pi / 100
    for idx, (x, y, z) in enumerate(rings):
        lines[idx].set_data(x * np.cos(angle) - y * np.sin(angle),
                            x * np.sin(angle) + y * np.cos(angle))
        lines[idx].set_3d_properties(z)
    return lines

ani = animation.FuncAnimation(fig, animate, frames=100, init_func=init,
                              blit=True, interval=100, repeat=False)

plt.close(fig)

from IPython.display import HTML
HTML(ani.to_jshtml())
