import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

# Function to create an elegant helical filament
def generate_helix(num_points, radius, pitch, turns):
    theta = np.linspace(0, 2 * np.pi * turns, num_points)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = pitch * theta / (2 * np.pi)  # Linear progression in z
    return x, y, z

# Function to plot helical paths in a visually captivating way
def plot_filaments(ax, num_filaments, num_points):
    radius = 1.0
    pitch = 0.5
    turns = 3  # Number of complete turns per filament
    colors = plt.cm.viridis(np.linspace(0, 1, num_filaments))  # Gradient along filaments

    for i, c in enumerate(colors):
        phase_shift = i * (2 * np.pi / num_filaments)  # Shift each helix slightly
        x, y, z = generate_helix(num_points, radius, pitch, turns)
        # Apply phase shift to enhance topological layering
        x_shifted = x * np.cos(phase_shift) - y * np.sin(phase_shift)
        y_shifted = x * np.sin(phase_shift) + y * np.cos(phase_shift)

        # Combine points for LineCollection
        points = np.array([x_shifted, y_shifted, z]).T
        segments = np.array([points[:-1], points[1:]]).transpose(1, 0, 2)
        
        line = LineCollection(segments, linestyle='-', linewidth=1.5, colors=[c], alpha=0.9)
        ax.add_collection3d(line)
        
        radius += 0.2  # Slightly increase radius for successive filaments

# Elegant minimalist plot setup
fig = plt.figure(figsize=(10, 10), facecolor='white')
ax = fig.add_subplot(projection='3d', frame_on=False)
ax.set_box_aspect([1, 1, 1])  # Equal aspect ratio

# Settings for elegance
ax.set_xlim([-2, 2])
ax.set_ylim([-2, 2])
ax.set_zlim([0, 4])
ax.axis('off')  # Turn off the axes for minimalist look

# Add helical filaments to represent SAT's core geometric structure
num_filaments = 7       # Symbolic: emergence of topological stability (n <= 3)
num_points = 1000       # High resolution for smooth curves
plot_filaments(ax, num_filaments, num_points)

# Highlight central axis for topological anchor
ax.plot([0, 0], [0, 0], [0, 4], color='black', linestyle='--', linewidth=0.8, alpha=0.8)

# Add radial lines to hint at projected "winding numbers"
theta_lines = np.linspace(0, 2 * np.pi, 12)
for theta in theta_lines:
    ax.plot(
        [0, 2 * np.cos(theta)], [0, 2 * np.sin(theta)], [0, 0],
        color='gray', linestyle='-', linewidth=0.4, alpha=0.5
    )

# Title for context
plt.title(r"SATO/Blockwave Theory: Minimal Geometric Structure of Reality", fontsize=14, pad=20, color='black')

# Save and show
plt.savefig("SAT_Filamentary_Manifold.png", dpi=300, bbox_inches='tight', transparent=True)
plt.show()