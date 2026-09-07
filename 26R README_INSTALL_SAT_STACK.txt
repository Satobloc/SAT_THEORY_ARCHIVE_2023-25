SAT Stack Installer Scripts
===========================

Files:
- install_sat_windows_envs.ps1
- install_sat_windows_envs.bat
- install_sat_wsl_sage_fenics.sh

Recommended Windows install order
---------------------------------

After Miniforge finishes installing:

1. Open "Miniforge Prompt" from the Start menu.
2. cd to this folder.
3. Run:

install_sat_windows_envs.bat

Default installs:
- sat-core
- sat-visual
- sat-jax

Optional installs:
- sat-quantum
- sat-hep

Examples:

install_sat_windows_envs.bat -CoreOnly

install_sat_windows_envs.bat -InstallQuantum

install_sat_windows_envs.bat -InstallHEP

install_sat_windows_envs.bat -InstallQuantum -InstallHEP


What I recommend on your 168 GB SSD
-----------------------------------

First run:

install_sat_windows_envs.bat

That gets:
- sat-core
- sat-visual
- sat-jax

Then stop and check disk space.

Only add these if needed:

install_sat_windows_envs.bat -InstallQuantum
install_sat_windows_envs.bat -InstallHEP


WSL / Sage / FEniCSx
--------------------

Only do this if WSL2 works and disk space allows.

PowerShell as Administrator:

wsl --install -d Ubuntu

Then inside Ubuntu:

sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git wget

Copy install_sat_wsl_sage_fenics.sh into Ubuntu, then run:

chmod +x install_sat_wsl_sage_fenics.sh
./install_sat_wsl_sage_fenics.sh


Sanity commands
---------------

sat-core:

conda activate sat-core
python -c "import numpy, scipy, sympy, matplotlib; print('sat-core OK')"

sat-visual:

conda activate sat-visual
python -c "import pyvista, vtk, trimesh, plotly; print('sat-visual OK')"

sat-jax:

conda activate sat-jax
python -c "import jax, jax.numpy as jnp; print('sat-jax OK', jnp.array([1,2,3])**2)"


Disk cleanup
------------

mamba clean --all -y

List environments:

conda env list

Remove an environment:

mamba env remove -n sat-hep
