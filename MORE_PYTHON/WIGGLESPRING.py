# WIGGLESPRING

#@title Closed String Oscillation in 3D (Colab-ready)
#@markdown Adjust the parameters and re-run the cell to regenerate the animation.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D
from IPython.display import HTML, display

# -----------------------
# Parameters (edit here)
# -----------------------
n = 2            #@param {type:"integer"}  # vibration mode (1,2,3,...)
R = 0.25          #@param {type:"number"}   # base radius of the closed string
eps = 0.1       #@param {type:"number"}   # radial ripple amplitude
z_span = 18.0     #@param {type:"number"}   # how far it propagates along z
frames = 200     #@param {type:"integer"}  # number of animation frames
fps = 40         #@param {type:"integer"}  # frames per second for saved GIF
leave_trail = True  #@param {type:"boolean"}  # leave a dot trail?
dot_speed = 2     #@param {type:"number"}   # revolutions per full animation (1.0 = one lap)

# -----------------------
# Build geometry
# -----------------------
sigma = np.linspace(0, 2*np.pi, 600)  # angle along the loop

fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, projection='3d')
string_line, = ax.plot([], [], [], lw=2, color='tab:blue')
dot, = ax.plot([], [], [], 'o', ms=6, color='crimson')
trail_line, = ax.plot([], [], [], lw=1.5, color='crimson')

# axes & view
lim = R + 1.5*eps
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)
ax.set_zlim(0, z_span)
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
ax.set_title(f"Closed String Mode n={n} in 3D (propagating along z)")

# store trail
trail_x, trail_y, trail_z = [], [], []

def init():
    string_line.set_data([], [])
    string_line.set_3d_properties([])

    dot.set_data([], [])
    dot.set_3d_properties([])

    trail_line.set_data([], [])
    trail_line.set_3d_properties([])

    return string_line, dot, trail_line

def update(frame):
    tau = 2*np.pi*frame/frames  # time parameter

    # Radial ripple for mode n
    r = R + eps * np.cos(n*sigma) * np.cos(n*tau)
    x = r * np.cos(sigma)
    y = r * np.sin(sigma)
    z = np.full_like(sigma, z_span * frame/frames)  # march forward in z

    # Update the loop
    string_line.set_data(x, y)
    string_line.set_3d_properties(z)

    # Dot position: move around circumference at configurable speed
    sigma_dot = (2*np.pi * dot_speed * frame/frames) % (2*np.pi)
    r_dot = R + eps * np.cos(n*sigma_dot) * np.cos(n*tau)
    x_dot = r_dot * np.cos(sigma_dot)
    y_dot = r_dot * np.sin(sigma_dot)
    z_dot = z_span * frame/frames

    dot.set_data([x_dot], [y_dot])
    dot.set_3d_properties([z_dot])

    # Trail
    if leave_trail:
        trail_x.append(x_dot)
        trail_y.append(y_dot)
        trail_z.append(z_dot)
        trail_line.set_data(trail_x, trail_y)
        trail_line.set_3d_properties(trail_z)
    else:
        trail_line.set_data([], [])
        trail_line.set_3d_properties([])

    return string_line, dot, trail_line

anim = FuncAnimation(fig, update, init_func=init, frames=frames, interval=1000/fps, blit=True)

# Save GIF to Colab filesystem
out_path = f"/content/closed_string_mode_n{n}_3D.gif"
anim.save(out_path, writer=PillowWriter(fps=fps))
plt.close(fig)

print(f"Saved GIF -> {out_path}")

# Also display inline as HTML animation (JS) for convenience
fig2 = plt.figure(figsize=(6,6))
ax2 = fig2.add_subplot(111, projection='3d')
# for inline preview, reduce resolution a bit
sigma_preview = np.linspace(0, 2*np.pi, 200)
string_line2, = ax2.plot([], [], [], lw=2, color='tab:blue')
dot2, = ax2.plot([], [], [], 'o', ms=6, color='crimson')
trail2, = ax2.plot([], [], [], lw=1.5, color='crimson')

ax2.set_xlim(-lim, lim)
ax2.set_ylim(-lim, lim)
ax2.set_zlim(0, z_span)
ax2.set_xlabel("x")
ax2.set_ylabel("y")
ax2.set_zlabel("z")
ax2.set_title(f"Closed String Mode n={n} (inline preview)")

tx, ty, tz = [], [], []

def init2():
    string_line2.set_data([], [])
    string_line2.set_3d_properties([])
    dot2.set_data([], [])
    dot2.set_3d_properties([])
    trail2.set_data([], [])
    trail2.set_3d_properties([])
    return string_line2, dot2, trail2

def update2(frame):
    tau = 2*np.pi*frame/frames
    r = R + eps * np.cos(n*sigma_preview) * np.cos(n*tau)
    x = r * np.cos(sigma_preview)
    y = r * np.sin(sigma_preview)
    z = np.full_like(sigma_preview, z_span * frame/frames)
    string_line2.set_data(x, y)
    string_line2.set_3d_properties(z)

    sigma_dot = (2*np.pi * dot_speed * frame/frames) % (2*np.pi)
    r_dot = R + eps * np.cos(n*sigma_dot) * np.cos(n*tau)
    x_dot = r_dot * np.cos(sigma_dot)
    y_dot = r_dot * np.sin(sigma_dot)
    z_dot = z_span * frame/frames
    dot2.set_data([x_dot], [y_dot])
    dot2.set_3d_properties([z_dot])

    if leave_trail:
        tx.append(x_dot); ty.append(y_dot); tz.append(z_dot)
        trail2.set_data(tx, ty)
        trail2.set_3d_properties(tz)
    else:
        trail2.set_data([], [])
        trail2.set_3d_properties([])

    return string_line2, dot2, trail2

anim2 = FuncAnimation(fig2, update2, init_func=init2, frames=frames, interval=1000/fps, blit=True)
display(HTML(anim2.to_jshtml()))
plt.close(fig2)