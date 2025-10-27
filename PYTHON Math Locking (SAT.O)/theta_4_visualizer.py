import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# =================== Adjustable Parameters ===================
wavefront_z = wavefront_zset     # Position of the time wavefront plane
helix_radius = helix_radiusset    # Radius of the helix
helix_pitch = helix_pitch     # Pitch (vertical rise per turn) of the helix
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

# Define the tangent line vector representing the angle of intersection
tangent_vector = np.array([np.sin(theta_4_rad), 0, np.cos(theta_4_rad)])

# Extend vectors both above and below the origin
extend_length = 1.0
# Positive direction (u^mu and tangent line)
ax.quiver(*origin, *u_mu, length=extend_length, color='blue', label=r'$u^\mu$ (Time-flow)', arrow_length_ratio=0.1)
ax.quiver(*origin, *tangent_vector, length=extend_length, color='black', label=r'$\theta_4$ (Intersection Line)', arrow_length_ratio=0.1)
# Negative direction (dashed lines)
ax.quiver(*origin, *-u_mu, length=extend_length, color='blue', linestyle='dashed', arrow_length_ratio=0.1)
ax.quiver(*origin, *-tangent_vector, length=extend_length, color='black', linestyle='dashed', arrow_length_ratio=0.1)

# Plot the time wavefront as a plane (XY plane at z = wavefront_z)
xx, yy = np.meshgrid(np.linspace(-1, 1, 10), np.linspace(-1, 1, 10))
zz = np.ones_like(xx) * wavefront_z
ax.plot_surface(xx, yy, zz, alpha=0.3, color='cyan')

# Plot a dot at the intersection of the tangent line with the wavefront
t_intersect = wavefront_z / tangent_vector[2]
intersection_point = origin + t_intersect * tangent_vector
ax.scatter(*intersection_point, color='black', s=50)

# Annotate theta_4 angle with value
ax.text(0.3, 0, 0.15, fr'$\theta_4={theta_4_deg:.2f}^\circ$', fontsize=14, color='black')

# Set axis labels
ax.set_xlabel('X (Spatial)')
ax.set_ylabel('Y (Spatial)')
ax.set_zlabel('Time')

# Set limits
ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])

# Add a legend
ax.legend()

# Set title
ax.set_title(r'3D Geometric Relationship: $\theta_4$ (Intersection Angle with Time Plane)')

# Show plot
plt.show()
