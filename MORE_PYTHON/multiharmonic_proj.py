# MULTIHARMONIC PROJECTIONS

#@title Filament with Projection Over Time + Fixed-Time, both with trails (3D + 2D)
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display

# -----------------------
# Parameters (edit here)
# -----------------------
n            = 3        #@param {type:"integer"}     # vibration mode along z (1,2,3,...)
L            = 6.0      #@param {type:"number"}      # filament length (z extent)
A_x          = 0.45     #@param {type:"number"}      # x-amplitude
A_y          = 0.30     #@param {type:"number"}      # y-amplitude
phi_over_pi  = 0.5      #@param {type:"number"}      # phase = phi_over_pi * π (e.g., 0.5 => π/2)
frames       = 180      #@param {type:"integer"}     # animation frames
fps          = 24       #@param {type:"integer"}     # playback fps

# dot controls
dot_laps       = 1.0      #@param {type:"number"}    # moving dot: how many z-laps per animation
trail_len_mv3d = 240      #@param {type:"integer"}   # moving-dot 3D trail length
trail_len_mv2d = 400      #@param {type:"integer"}   # moving-dot 2D (x–y) trail length
z_fixed_frac   = 0.5      #@param {type:"number"}    # fixed dot: z_fixed = z_fixed_frac * L (0..1)
trail_len_fx2d = 800      #@param {type:"integer"}   # fixed-dot 2D (x–y) trail length (ST string trace)

# -----------------------
# Derived quantities
# -----------------------
phi_xy = phi_over_pi * np.pi
z_fixed = float(z_fixed_frac) * L

# Geometry resolution (moderate for stability)
Nz = 200
z = np.linspace(0, L, Nz)

# Figure: left (3D filament + both dots + moving-dot 3D trail), right (2D traces for both dots)
fig = plt.figure(figsize=(11,5))
gs = fig.add_gridspec(1, 2, width_ratios=[1.4, 1.0])
ax3 = fig.add_subplot(gs[0,0], projection='3d')
ax2 = fig.add_subplot(gs[0,1])

# 3D handles
fil_line,    = ax3.plot([], [], [], lw=2,   color='tab:blue',  label='filament')
dot_mv3d,    = ax3.plot([], [], [], 'o', ms=6, color='crimson',   label='moving dot (timesheet)')
dot_fx3d,    = ax3.plot([], [], [], 'o', ms=6, color='tab:green', label='fixed dot (time-slice)')
trail_mv3d,  = ax3.plot([], [], [], lw=1.5, color='crimson', alpha=0.9, label='moving dot trail (3D)')

R = 1.6*max(A_x, A_y)
ax3.set_xlim(-R, R); ax3.set_ylim(-R, R); ax3.set_zlim(0, L)
ax3.set_xlabel("x"); ax3.set_ylabel("y"); ax3.set_zlabel("z")
ax3.set_title("Filament (3D): moving-4d trace + fixed-time proj")
ax3.legend(loc='upper right')

# 2D traces (x–y) for both dots
loop_mv,  = ax2.plot([], [], lw=2,   color='crimson',   label='moving dot x–y')
loop_fx,  = ax2.plot([], [], lw=2.2, color='tab:green', label='fixed dot x–y (ST string trace)')
dot2d_mv, = ax2.plot([], [], 'o', ms=6, color='crimson')
dot2d_fx, = ax2.plot([], [], 'o', ms=6, color='tab:green')

ax2.set_aspect('equal', 'box')
ax2.set_xlim(-R, R); ax2.set_ylim(-R, R)
ax2.set_xlabel("x"); ax2.set_ylabel("y")
ax2.set_title("x–y traces (right panel)")
ax2.legend(loc='upper right')

# Histories
hx_mv3d, hy_mv3d, hz_mv3d = [], [], []   # moving dot 3D trail
hx_mv2d, hy_mv2d          = [], []       # moving dot 2D x–y trail
hx_fx2d, hy_fx2d          = [], []       # fixed dot 2D x–y trail (the ST string trace)

def init():
    fil_line.set_data([], []); fil_line.set_3d_properties([])
    dot_mv3d.set_data([], []); dot_mv3d.set_3d_properties([])
    dot_fx3d.set_data([], []); dot_fx3d.set_3d_properties([])
    trail_mv3d.set_data([], []); trail_mv3d.set_3d_properties([])
    loop_mv.set_data([], []);  dot2d_mv.set_data([], [])
    loop_fx.set_data([], []);  dot2d_fx.set_data([], [])
    return fil_line, dot_mv3d, dot_fx3d, trail_mv3d, loop_mv, dot2d_mv, loop_fx, dot2d_fx

def update(frame):
    tau = 2*np.pi*frame/frames

    # Filament transverse displacement
    S = np.sin(n*np.pi*z/L)
    X = A_x * S * np.cos(n*tau)
    Y = A_y * S * np.cos(n*tau + phi_xy)
    fil_line.set_data(X, Y)
    fil_line.set_3d_properties(z)

    # --- Projection Over Time (sweeps along z) ---
    z_mv = (dot_laps * L * frame/frames) % L
    s_mv = np.sin(n*np.pi*z_mv/L)
    x_mv = A_x * s_mv * np.cos(n*tau)
    y_mv = A_y * s_mv * np.cos(n*tau + phi_xy)

    dot_mv3d.set_data([x_mv], [y_mv]); dot_mv3d.set_3d_properties([z_mv])

    # 3D trail for moving dot
    hx_mv3d.append(x_mv); hy_mv3d.append(y_mv); hz_mv3d.append(z_mv)
    if len(hx_mv3d) > trail_len_mv3d:
        del hx_mv3d[0]; del hy_mv3d[0]; del hz_mv3d[0]
    trail_mv3d.set_data(hx_mv3d, hy_mv3d); trail_mv3d.set_3d_properties(hz_mv3d)

    # 2D trail for moving dot
    hx_mv2d.append(x_mv); hy_mv2d.append(y_mv)
    if len(hx_mv2d) > trail_len_mv2d:
        del hx_mv2d[0]; del hy_mv2d[0]
    loop_mv.set_data(hx_mv2d, hy_mv2d)
    dot2d_mv.set_data([x_mv], [y_mv])

    # --- Fixed-Time (constant z slice) ---
    s_fx = np.sin(n*np.pi*z_fixed/L)
    x_fx = A_x * s_fx * np.cos(n*tau)
    y_fx = A_y * s_fx * np.cos(n*tau + phi_xy)

    dot_fx3d.set_data([x_fx], [y_fx]); dot_fx3d.set_3d_properties([z_fixed])

    # 2D trail for fixed dot — this is the ST string loop trace
    hx_fx2d.append(x_fx); hy_fx2d.append(y_fx)
    if len(hx_fx2d) > trail_len_fx2d:
        del hx_fx2d[0]; del hy_fx2d[0]
    loop_fx.set_data(hx_fx2d, hy_fx2d)
    dot2d_fx.set_data([x_fx], [y_fx])

    return fil_line, dot_mv3d, dot_fx3d, trail_mv3d, loop_mv, dot2d_mv, loop_fx, dot2d_fx

anim = FuncAnimation(fig, update, init_func=init, frames=frames, interval=1000/fps, blit=False)
display(HTML(anim.to_jshtml()))
plt.close(fig)