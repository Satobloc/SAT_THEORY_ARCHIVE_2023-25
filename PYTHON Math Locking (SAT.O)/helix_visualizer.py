import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation

# Helix Parameters
A = 1.0        # Amplitude (radius) in X-Y
omega = 2.0    # Angular frequency for the helix rotation
Z_amp = 0.5    # Amplitude for Z oscillation (optional complexity)

# Time parameters
t_max = 10
dt = 0.05
times = np.arange(0, t_max, dt)

# Define the phase shifts for R, G, B (0°, 120°, 240°) and coordinate shifts
phase_shifts = {
    'R': 0,
    'G': 2 * np.pi / 3,
    'B': 4 * np.pi / 3
}

coordinate_shifts = {
    'R': (0.01, 0.0, 0.0),  # Shift X by 0.01 for Red
    'G': (0.0, 0.01, 0.0),  # Shift Y by 0.01 for Green
    'B': (0.0, 0.0, 0.01)   # Shift Z by 0.01 for Blue
}

colors = {
    'R': 'red',
    'G': 'green',
    'B': 'blue'
}

# Set up the figure
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
trace_lines = {}

# Initialize plot lines for each color
for color_key in phase_shifts.keys():
    trace_lines[color_key], = ax.plot([], [], [], lw=2, color=colors[color_key])

# Storage for traces
traces = {key: {'x': [], 'y': [], 'z': []} for key in phase_shifts.keys()}

def init():
    ax.set_xlim(-1.5 * A, 1.5 * A)
    ax.set_ylim(-1.5 * A, 1.5 * A)
    ax.set_zlim(-1.5 * Z_amp, 1.5 * Z_amp)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Three 4D Helices with Phase Shifts and Coordinate Offsets (R, G, B)')
    return list(trace_lines.values())

def animate(i):
    t = times[i]
    for key, phi in phase_shifts.items():
        shift_x, shift_y, shift_z = coordinate_shifts[key]
        x_t = A * np.sin(omega * t + phi) + shift_x
        y_t = A * np.cos(omega * t + phi) + shift_y
        z_t = Z_amp * np.sin(3 * t) + shift_z  # Optional complexity in Z

        traces[key]['x'].append(x_t)
        traces[key]['y'].append(y_t)
        traces[key]['z'].append(z_t)

        trace_lines[key].set_data(traces[key]['x'], traces[key]['y'])
        trace_lines[key].set_3d_properties(traces[key]['z'])

    return list(trace_lines.values())

ani = animation.FuncAnimation(fig, animate, frames=len(times), init_func=init,
                              blit=True, interval=50, repeat=False)

plt.close(fig)

from IPython.display import HTML
HTML(ani.to_jshtml())

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# =================== Adjustable Parameters ===================
wavefront_z = wavefront_zset   # Position of the time wavefront plane
helix_radius = helix_radiusset  # Radius of the helix
helix_pitch = helix_pitchset   # Pitch (vertical rise per turn) of the helix
# ===============================================================

# Calculate theta_4 based on pitch and radius
theta_4_rad = np.arctan(helix_pitch / (2 * np.pi * helix_radius))
theta_4_deg = np.rad2deg(theta_4_rad)

# Create figure and 3D axis
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Define the stationary origin
origin = np.array([0, 0, 0])

# Define the u^mu vector (time-flow vector)
u_mu = np.array([0, 0, 1])

# Create a helix along the z-axis
t = np.linspace(-6 * np.pi, 6 * np.pi, 1000)  # Extend above and below
x_helix = helix_radius * np.cos(t)
y_helix = helix_radius * np.sin(t)
z_helix = helix_pitch * t / (2 * np.pi)

# Translate helix to origin
helix_points = np.vstack((x_helix, y_helix, z_helix))

# Plot the helix
ax.plot3D(helix_points[0], helix_points[1], helix_points[2], color='red', label=r'$\varphi$ (Filament as Helix)')

# Plot the u^mu vector (vertical)
extend_length = 1.0
ax.quiver(*origin, *u_mu, length=extend_length, color='blue', label=r'$u^\mu$ (Time-flow)', arrow_length_ratio=0.1)
# Negative direction
ax.quiver(*origin, *-u_mu, length=extend_length, color='blue', arrow_length_ratio=0.1, linestyle='dashed')

# Plot the time wavefront as a plane (XY plane at z = wavefront_z)
xx, yy = np.meshgrid(np.linspace(-2, 2, 20), np.linspace(-2, 2, 20))
zz = np.ones_like(xx) * wavefront_z
ax.plot_surface(xx, yy, zz, alpha=0.3, color='cyan')

# Plot a dot at the intersection of the helix with the wavefront
z_cross_indices = np.where(np.diff(np.sign(helix_points[2] - wavefront_z)))[0]
if z_cross_indices.size > 0:
    idx = z_cross_indices[0]
    ax.scatter(helix_points[0, idx], helix_points[1, idx], helix_points[2, idx], color='black', s=50)

# Draw an arc to indicate theta_4 at the origin
#arc = np.linspace(0, theta_4_rad, 100)
#arc_radius = 0.5
#arc_x = arc_radius * np.sin(arc)
#arc_y = np.zeros_like(arc)
#arc_z = arc_radius * np.cos(arc)
#ax.plot(arc_x, arc_y, arc_z, color='black')

# Annotate theta_4 angle with calculated value
ax.text(0.5, 0, 0.2, fr'$\theta_4={theta_4_deg:.2f}^\circ$', fontsize=14, color='black')

# Set axis labels
ax.set_xlabel('X (Spatial)')
ax.set_ylabel('Y (Spatial)')
ax.set_zlabel('Time')

# Set limits
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])
ax.set_zlim([-2, 2])

# Add a legend
ax.legend()

# Set title
ax.set_title(r'3D Geometric Relationship: $\theta_4$ (Helix Intersection Angle with Time Plane)')

# Show plot
plt.show()
