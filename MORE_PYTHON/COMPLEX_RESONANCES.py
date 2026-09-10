# COMPLEX RESONANCES

#@title Filament with multi-harmonic slice loops (petals & complex “string traces”)
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, display
from collections import deque

# ====== Controls ======
# Spatial mode along z:
n              = 3        #@param {type:"integer"}    # nodes along z (avoid placing fixed slice at nodes)
L              = 6.0      #@param {type:"number"}
A_x            = 0.45     #@param {type:"number"}     # filament transverse amp in x
A_y            = 0.30     #@param {type:"number"}     # filament transverse amp in y

# --- Time content (harmonics) for loops at a slice ---
# Base harmonic integers on x and y (different -> Lissajous petals)
m1_x           = 3        #@param {type:"integer"}    # try 3
m1_y           = 2        #@param {type:"integer"}    # try 2 (3:2 Lissajous gives 3-lobed look)
phi1_over_pi   = 0.5      #@param {type:"number"}     # phase between x and y base terms (0.5 -> π/2)

# Optional overtone (second harmonic component) to enrich the loop
use_overtone   = True     #@param {type:"boolean"}
Ax2            = 0.12     #@param {type:"number"}     # overtone amp in x (fraction of A_x*slice)
Ay2            = 0.10     #@param {type:"number"}     # overtone amp in y
m2_x           = 1        #@param {type:"integer"}    # e.g., 1
m2_y           = 1        #@param {type:"integer"}    # e.g., 1
phi2_over_pi   = 0.0      #@param {type:"number"}     # extra phase for overtone between x and y

# Animation
frames         = 220      #@param {type:"integer"}
fps            = 24       #@param {type:"integer"}

# Dots & trails
dot_laps       = 1.0      #@param {type:"number"}     # moving dot: z-laps per animation
trail_len_mv3d = 260      #@param {type:"integer"}    # moving dot 3D trail length
trail_len_mv2d = 420      #@param {type:"integer"}    # moving dot 2D trail length
z_fixed_frac   = 0.42     #@param {type:"number"}     # fixed slice (0..1), avoid ~k/n
trail_len_fx2d = 1200     #@param {type:"integer"}    # fixed dot 2D trail (the ST “string trace”)
show_fx3d_trail = True    #@param {type:"boolean"}

# ====== Derived ======
phi1 = phi1_over_pi * np.pi
phi2 = phi2_over_pi * np.pi
z_fixed = float(z_fixed_frac) * L

# Geometry
Nz = 200
z = np.linspace(0, L, Nz)

# Figure
fig = plt.figure(figsize=(11,5))
gs = fig.add_gridspec(1, 2, width_ratios=[1.4, 1.0])
ax3 = fig.add_subplot(gs[0,0], projection='3d')
ax2 = fig.add_subplot(gs[0,1])

# 3D artists
fil_line,      = ax3.plot([], [], [], lw=2,   color='tab:blue')
dot_mv3d,      = ax3.plot([], [], [], 'o', ms=6, color='crimson')
trail_mv3d,    = ax3.plot([], [], [], lw=1.5, color='crimson', alpha=0.9)
dot_fx3d,      = ax3.plot([], [], [], 'o', ms=6, color='tab:green')
trail_fx3d,    = ax3.plot([], [], [], lw=1.5, color='tab:green', alpha=0.9) if show_fx3d_trail else (None,)

R3 = 1.6*max(A_x, A_y)
ax3.set_xlim(-R3, R3); ax3.set_ylim(-R3, R3); ax3.set_zlim(0, L)
ax3.set_xlabel("x"); ax3.set_ylabel("y"); ax3.set_zlabel("z")
ax3.set_title("Filament (3D): moving dot + fixed dot (multi-harmonic slice)")

# 2D traces
loop_mv,  = ax2.plot([], [], lw=2.0, color='crimson',   label='moving dot x–y')
loop_fx,  = ax2.plot([], [], lw=2.4, color='tab:green', label='fixed dot x–y (ST trace)')
dot2d_mv, = ax2.plot([], [], 'o', ms=6, color='crimson')
dot2d_fx, = ax2.plot([], [], 'o', ms=6, color='tab:green')
ax2.set_aspect('equal', 'box')
ax2.set_xlabel("x"); ax2.set_ylabel("y")
ax2.set_title("x–y traces (right panel)")
ax2.legend(loc='upper right')

# Histories
hx_mv3d = deque(maxlen=trail_len_mv3d); hy_mv3d = deque(maxlen=trail_len_mv3d); hz_mv3d = deque(maxlen=trail_len_mv3d)
hx_mv2d = deque(maxlen=trail_len_mv2d); hy_mv2d = deque(maxlen=trail_len_mv2d)
hx_fx2d = deque(maxlen=trail_len_fx2d); hy_fx2d = deque(maxlen=trail_len_fx2d)
if show_fx3d_trail:
    hx_fx3d = deque(maxlen=trail_len_fx2d); hy_fx3d = deque(maxlen=trail_len_fx2d); hz_fx3d = deque(maxlen=trail_len_fx2d)

# Right-panel autoscale based on slice amplitude (use base spatial factor)
s_fx_amp = abs(np.sin(n*np.pi*z_fixed/L))
min_R2 = 0.08*max(A_x, A_y)
def set_right_limits():
    R2 = 1.6 * max(A_x, A_y) * max(s_fx_amp, 0.15)
    R2 = max(R2, min_R2)
    ax2.set_xlim(-R2, R2); ax2.set_ylim(-R2, R2)

def init():
    fil_line.set_data([], []); fil_line.set_3d_properties([])
    dot_mv3d.set_data([], []); dot_mv3d.set_3d_properties([])
    dot_fx3d.set_data([], []); dot_fx3d.set_3d_properties([])
    trail_mv3d.set_data([], []); trail_mv3d.set_3d_properties([])
    if show_fx3d_trail and trail_fx3d is not None:
        trail_fx3d.set_data([], []); trail_fx3d.set_3d_properties([])
    loop_mv.set_data([], []); dot2d_mv.set_data([], [])
    loop_fx.set_data([], []); dot2d_fx.set_data([], [])
    set_right_limits()
    return fil_line, dot_mv3d, dot_fx3d, trail_mv3d, loop_mv, dot2d_mv, loop_fx, dot2d_fx

def update(frame):
    tau = 2*np.pi*frame/frames

    # Filament (single spatial mode n; base time frequency = m1_x, m1_y just rotate phase in XY)
    S = np.sin(n*np.pi*z/L)
    # For the 3D filament line, it’s fine to show the base harmonic (keeps the ribbon readable)
    X = A_x * S * np.cos(m1_x * tau)
    Y = A_y * S * np.cos(m1_y * tau + phi1)
    fil_line.set_data(X, Y); fil_line.set_3d_properties(z)

    # Moving dot (sweeps along z)
    z_mv = (dot_laps * L * frame/frames) % L
    s_mv = np.sin(n*np.pi*z_mv/L)
    # Same time content as slice (so moving & fixed agree in instantaneous phase)
    x_mv = s_mv * (A_x * np.cos(m1_x * tau) + (Ax2 * np.cos(m2_x * tau + phi2) if use_overtone else 0.0))
    y_mv = s_mv * (A_y * np.cos(m1_y * tau + phi1) + (Ay2 * np.cos(m2_y * tau + phi2 + phi1) if use_overtone else 0.0))
    dot_mv3d.set_data([x_mv], [y_mv]); dot_mv3d.set_3d_properties([z_mv])

    hx_mv3d.append(x_mv); hy_mv3d.append(y_mv); hz_mv3d.append(z_mv)
    trail_mv3d.set_data(np.array(hx_mv3d), np.array(hy_mv3d)); trail_mv3d.set_3d_properties(np.array(hz_mv3d))
    hx_mv2d.append(x_mv);  hy_mv2d.append(y_mv)
    loop_mv.set_data(np.array(hx_mv2d), np.array(hy_mv2d)); dot2d_mv.set_data([x_mv], [y_mv])

    # Fixed dot (the ST “string trace” at the slice)
    s_fx = np.sin(n*np.pi*z_fixed/L)
    x_fx = s_fx * (A_x * np.cos(m1_x * tau) + (Ax2 * np.cos(m2_x * tau + phi2) if use_overtone else 0.0))
    y_fx = s_fx * (A_y * np.cos(m1_y * tau + phi1) + (Ay2 * np.cos(m2_y * tau + phi2 + phi1) if use_overtone else 0.0))
    dot_fx3d.set_data([x_fx], [y_fx]); dot_fx3d.set_3d_properties([z_fixed])

    hx_fx2d.append(x_fx); hy_fx2d.append(y_fx)
    loop_fx.set_data(np.array(hx_fx2d), np.array(hy_fx2d)); dot2d_fx.set_data([x_fx], [y_fx])

    if show_fx3d_trail and trail_fx3d is not None:
        hx_fx3d.append(x_fx); hy_fx3d.append(y_fx); hz_fx3d.append(z_fixed)
        trail_fx3d.set_data(np.array(hx_fx3d), np.array(hy_fx3d)); trail_fx3d.set_3d_properties(np.array(hz_fx3d))

    return fil_line, dot_mv3d, dot_fx3d, trail_mv3d, loop_mv, dot2d_mv, loop_fx, dot2d_fx

anim = FuncAnimation(fig, update, init_func=init, frames=frames, interval=1000/fps, blit=False)
display(HTML(anim.to_jshtml()))
plt.close(fig)