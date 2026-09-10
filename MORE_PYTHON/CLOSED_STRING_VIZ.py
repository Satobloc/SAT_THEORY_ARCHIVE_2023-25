# CLOSED STRING VISUALIZER

#@title Closed String Oscillation in 3D (lean & Colab-friendly)
# This version avoids blit (which often hangs in 3D), reduces points/frames,
# and uses inline JS for playback. Optional MP4 save is provided.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display

# -----------------------
# Parameters (edit here)
# -----------------------
n       = 2      #@param {type:"integer"}  # mode number
R       = 0.1    #@param {type:"number"}   # base radius
eps     = 1   #@param {type:"number"}   # ripple amplitude
z_span  = 0.1    #@param {type:"number"}   # total z travel
frames  = 120    #@param {type:"integer"}  # animation frames (lower = lighter)
fps     = 24     #@param {type:"integer"}  # display FPS
dot_speed = 2.0  #@param {type:"number"}   # revolutions per full animation (1.0 = 1 lap)
leave_trail = True  #@param {type:"boolean"}

# Geometry resolution (keep small for Colab stability)
N_sigma = 200   # angular samples along the loop
sigma = np.linspace(0, 2*np.pi, N_sigma)

# --- Figure & axes ---
fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(111, projection='3d')

# handles
string_line, = ax.plot([], [], [], lw=2, color='tab:blue')
dot,         = ax.plot([], [], [], 'o', ms=6, color='crimson')
trail_line,  = ax.plot([], [], [], lw=1.5, color='crimson')

# axes limits
lim = R + 1.5*eps
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)
ax.set_zlim(0, z_span)
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
ax.set_title(f"Closed String Mode n={n} (3D, lean)")

# trail storage
tx, ty, tz = [], [], []

def init():
    string_line.set_data([], [])
    string_line.set_3d_properties([])
    dot.set_data([], [])
    dot.set_3d_properties([])
    trail_line.set_data([], [])
    trail_line.set_3d_properties([])
    return string_line, dot, trail_line

def update(frame):
    tau = 2*np.pi*frame/frames

    # loop shape at this time
    r = R + eps * np.cos(n*sigma) * np.cos(n*tau)
    x = r * np.cos(sigma)
    y = r * np.sin(sigma)
    z = np.full_like(sigma, z_span * frame/frames)

    string_line.set_data(x, y)
    string_line.set_3d_properties(z)

    # moving dot
    sdot = (2*np.pi * dot_speed * frame/frames) % (2*np.pi)
    rdot = R + eps * np.cos(n*sdot) * np.cos(n*tau)
    xdot = rdot * np.cos(sdot)
    ydot = rdot * np.sin(sdot)
    zdot = z_span * frame/frames

    dot.set_data([xdot], [ydot])
    dot.set_3d_properties([zdot])

    # optional trail
    if leave_trail:
        tx.append(xdot); ty.append(ydot); tz.append(zdot)
        trail_line.set_data(tx, ty)
        trail_line.set_3d_properties(tz)
    else:
        trail_line.set_data([], [])
        trail_line.set_3d_properties([])

    return string_line, dot, trail_line

# IMPORTANT: blit=False for 3D (blitting often hangs in Colab)
anim = FuncAnimation(fig, update, init_func=init, frames=frames, interval=1000/fps, blit=False)

# Inline JS animation (lighter than GIF writer)
display(HTML(anim.to_jshtml()))
plt.close(fig)

# --- Optional: Save MP4 via ffmpeg (more reliable than GIF in Colab) ---
save_mp4 = False  #@param {type:"boolean"}
if save_mp4:
    from matplotlib.animation import FFMpegWriter
    fig2 = plt.figure(figsize=(6,6))
    ax2 = fig2.add_subplot(111, projection='3d')
    string2, = ax2.plot([], [], [], lw=2, color='tab:blue')
    dot2,    = ax2.plot([], [], [], 'o', ms=6, color='crimson')
    trail2,  = ax2.plot([], [], [], lw=1.5, color='crimson')
    ax2.set_xlim(-lim, lim); ax2.set_ylim(-lim, lim); ax2.set_zlim(0, z_span)
    ax2.set_xlabel("x"); ax2.set_ylabel("y"); ax2.set_zlabel("z")
    ax2.set_title(f"Closed String Mode n={n} (MP4 export)")

    tx2, ty2, tz2 = [], [], []
    def upd2(frame):
        tau = 2*np.pi*frame/frames
        r = R + eps * np.cos(n*sigma) * np.cos(n*tau)
        x = r * np.cos(sigma); y = r * np.sin(sigma)
        z = np.full_like(sigma, z_span * frame/frames)
        string2.set_data(x, y); string2.set_3d_properties(z)
        sdot = (2*np.pi * dot_speed * frame/frames) % (2*np.pi)
        rdot = R + eps * np.cos(n*sdot) * np.cos(n*tau)
        xdot = rdot * np.cos(sdot); ydot = rdot * np.sin(sdot); zdot = z_span * frame/frames
        dot2.set_data([xdot], [ydot]); dot2.set_3d_properties([zdot])
        if leave_trail:
            tx2.append(xdot); ty2.append(ydot); tz2.append(zdot)
            trail2.set_data(tx2, ty2); trail2.set_3d_properties(tz2)
        else:
            trail2.set_data([], []); trail2.set_3d_properties([])
        return string2, dot2, trail2

    writer = FFMpegWriter(fps=fps, bitrate=1800)
    anim2 = FuncAnimation(fig2, upd2, frames=frames, interval=1000/fps, blit=False)
    out_path = f"/content/closed_string_mode_n{n}_3D.mp4"
    anim2.save(out_path, writer=writer)
    plt.close(fig2)
    print(f"Saved MP4 -> {out_path}")