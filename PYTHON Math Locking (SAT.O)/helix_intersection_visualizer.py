import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# =================== USER-EDITABLE PARAMETERS ===================
helix_pitch = 0.2     # Vertical rise per turn
helix_diameter = 2.0  # Full diameter
# ================================================================

# Derived parameters
helix_radius = helix_diameter / 2.0

# Calculate angles
inverse_theta_4_rad = np.arctan(helix_pitch / (2 * np.pi * helix_radius))  # Low angle
theta_4_rad = np.pi / 2 - inverse_theta_4_rad                             # High angle
theta_4_deg = np.rad2deg(theta_4_rad)

# Helix parametrization
t = np.linspace(-6 * np.pi, 6 * np.pi, 1000)
x_helix = helix_radius * np.cos(t)
y_helix = helix_radius * np.sin(t)
z_helix = (helix_pitch / (2 * np.pi)) * t

# =================== PLOT ===================
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot the helix
ax.plot3D(x_helix, y_helix, z_helix, color='red', label='Helix')

# Plot the time sheet (xy-plane)
xx, yy = np.meshgrid(np.linspace(-2, 2, 10), np.linspace(-2, 2, 10))
zz = np.zeros_like(xx)
ax.plot_surface(xx, yy, zz, alpha=0.3, color='cyan')

# Label theta_4 at a strategic point
# Pick a point on the helix at t = 0 for simplicity
tangent_point = np.array([helix_radius, 0, 0])  # (x, y, z) at t=0

# Draw theta_4 label
arc_radius = 0.5
arc = np.linspace(0, theta_4_rad, 100)
arc_x = np.zeros_like(arc)  # Arc lies in y-z plane
arc_y = arc_radius * np.sin(arc)
arc_z = arc_radius * np.cos(arc)

ax.plot(arc_x + tangent_point[0], arc_y + tangent_point[1], arc_z + tangent_point[2],
        color='black', linestyle='--', linewidth=2)

ax.text(tangent_point[0] + 0.1,
        tangent_point[1] + arc_radius * np.sin(theta_4_rad / 2),
        tangent_point[2] + arc_radius * np.cos(theta_4_rad / 2),
        f'$\\theta_4$ = {theta_4_deg:.2f}°',
        fontsize=12, color='black', ha='left')

# Axis labels
ax.set_xlabel('X (Spatial)')
ax.set_ylabel('Y (Spatial)')
ax.set_zlabel('Time')

ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])
ax.set_zlim([-1, 1])

ax.set_title('Helix Intersection with Time Sheet\nLabeling $\\theta_4$ (Complement of Intersection Angle)')
ax.legend()
plt.show()
