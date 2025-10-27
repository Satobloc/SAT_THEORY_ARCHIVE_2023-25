import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation

# 4D Helix Parameters
R = 1.0          # Radius in XY
A = 0.5          # Amplitude in Z
omega = 2.0      # Frequency for XY rotation
nu = 3.0         # Frequency for Z oscillation

# Time parameters
t_max = 10
dt = 0.05
times = np.arange(0, t_max, dt)

# 4D Helix Equations
X = R * np.cos(omega * times)
Y = R * np.sin(omega * times)
Z = A * np.sin(nu * times)
T = times  # Fourth dimension: time itself

# Set up the 3D figure
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
trace_line, = ax.plot([], [], [], lw=2, color='blue')

def init():
    ax.set_xlim(-R*1.5, R*1.5)
    ax.set_ylim(-R*1.5, R*1.5)
    ax.set_zlim(-A*1.5, A*1.5)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Simple 4D Helix Projection (X, Y, Z)')
    return trace_line,

def animate(i):
    trace_line.set_data(X[:i], Y[:i])
    trace_line.set_3d_properties(Z[:i])
    return trace_line,

ani = animation.FuncAnimation(fig, animate, frames=len(times), init_func=init,
                              blit=True, interval=50, repeat=False)

plt.close(fig)

from IPython.display import HTML
HTML(ani.to_jshtml())
