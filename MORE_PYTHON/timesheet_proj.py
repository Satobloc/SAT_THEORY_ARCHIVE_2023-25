# TIMESHEET PROJECTION

#@title Guitar-string with timesheet motion: dot moves along filament (3D, lean)
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display

# -----------------------
# Parameters (edit here)
# -----------------------
n          = 3        #@param {type:"integer"}  # vibration mode (1,2,3,...)
L          = 6.0      #@param {type:"number"}   # filament length (z extent)
A_x        = 0.7     #@param {type:"number"}   # x-amplitude
A_y        = 0.218     #@param {type:"number"}   # y-amplitude
phi_xy     = 2   #@param {type:"number"}   # phase shift between x and y (~pi/2 = circular polarization)
frames     = 160      #@param {type:"integer"}  # animation frames
fps        = 24       #@param {type:"integer"}  # playback fps
dot_laps   = 1.0      #@param {type:"number"}   # how many z-laps the dot makes (0.5 = half, 1 = one full pass)
trail_len  = 240      #@param {type:"integer"}  # how many past dot points to show

# Geometry resolution (keep modest for stability)
Nz = 200
z = np.linspace(0, L, Nz)

# Build figure: left = 3D filament + moving dot; right = 2D x–y projection of dot's path
fig = plt.figure(figsize=(10,5))
gs = fig.add_gridspec(1, 2, width_ratios=[1.4, 1.0])
ax3 = fig.add_subplot(gs[0,0], projection='3d')
ax2 = fig.add_subplot(gs[0,1])

# 3D handles
fil_line, = ax3.plot([], [], [], lw=2, color='tab:blue', label='filament')
dot3d,    = ax3.plot([], [], [], 'o', ms=6, color='crimson', label='dot (moving in z)')
trail3d,  = ax3.plot([], [], [], lw=1.5, color='crimson', alpha=0.9, label='dot trail')

# Axes limits
R = 1.6*max(A_x, A_y)
ax3.set_xlim(-R, R)
ax3.set_ylim(-R, R)
ax3.set_zlim(0, L)
ax3.set_xlabel("x"); ax3.set_ylabel("y"); ax3.set_zlabel("z")
ax3.set_title("SAT filament (3D) with dot moving along z")

# 2D loop (x–y) of the *moving* dot
loop_line, = ax2.plot([], [], lw=2, color='crimson')
dot2d,     = ax2.plot([], [], 'o', ms=6, color='black')
ax2.set_aspect('equal', 'box')
ax2.set_xlim(-R, R); ax2.set_ylim(-R, R)
ax2.set_xlabel("x (dot)"); ax2.set_ylabel("y (dot)")
ax2.set_title("Dot x–y projection (timesheet trace)")

# History buffers
hx, hy, hz = [], [], []

def init():
    fil_line.set_data([], []); fil_line.set_3d_properties([])
    dot3d.set_data([], []);    dot3d.set_3d_properties([])
    trail3d.set_data([], []);  trail3d.set_3d_properties([])
    loop_line.set_data([], []); dot2d.set_data([], [])
    return fil_line, dot3d, trail3d, loop_line, dot2d

def update(frame):
    tau = 2*np.pi*frame/frames

    # Filament (straight along z) with 2D transverse oscillation
    S = np.sin(n*np.pi*z/L)
    X = A_x * S * np.cos(n*tau)
    Y = A_y * S * np.cos(n*tau + phi_xy)
    fil_line.set_data(X, Y); fil_line.set_3d_properties(z)

    # Dot position: move along z from 0 -> L (or multiple laps) while sampling the instantaneous filament displacement
    z_dot = (dot_laps * L * frame/frames) % L
    s     = np.sin(n*np.pi*z_dot/L)
    x_dot = A_x * s * np.cos(n*tau)
    y_dot = A_y * s * np.cos(n*tau + phi_xy)

    dot3d.set_data([x_dot], [y_dot]); dot3d.set_3d_properties([z_dot])

    # Trail (3D)
    hx.append(x_dot); hy.append(y_dot); hz.append(z_dot)
    if len(hx) > trail_len:
        del hx[0]; del hy[0]; del hz[0]
    trail3d.set_data(hx, hy); trail3d.set_3d_properties(hz)

    # 2D projection history
    loop_line.set_data(hx, hy)
    dot2d.set_data([x_dot], [y_dot])

    return fil_line, dot3d, trail3d, loop_line, dot2d

anim = FuncAnimation(fig, update, init_func=init, frames=frames, interval=1000/fps, blit=False)
display(HTML(anim.to_jshtml()))
plt.close(fig)