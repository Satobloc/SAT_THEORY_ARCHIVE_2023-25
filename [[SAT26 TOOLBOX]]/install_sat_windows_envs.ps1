<# 
SAT Stack Installer for Windows / Miniforge

Run this AFTER Miniforge is installed.

Recommended:
  1. Open "Miniforge Prompt" from Start Menu.
  2. cd to the folder containing this script.
  3. Run:
       powershell -ExecutionPolicy Bypass -File .\install_sat_windows_envs.ps1

Default installs:
  sat-core
  sat-visual
  sat-jax

Optional:
  powershell -ExecutionPolicy Bypass -File .\install_sat_windows_envs.ps1 -InstallQuantum
  powershell -ExecutionPolicy Bypass -File .\install_sat_windows_envs.ps1 -InstallHEP
  powershell -ExecutionPolicy Bypass -File .\install_sat_windows_envs.ps1 -CoreOnly

Notes:
  - Uses mamba if available, conda otherwise.
  - Uses conda run for ipykernel registration and sanity tests.
  - Keeps environments split so heavy packages do not fight each other.
#>

param(
    [switch]$CoreOnly,
    [switch]$SkipCore,
    [switch]$SkipVisual,
    [switch]$SkipJax,
    [switch]$InstallQuantum,
    [switch]$InstallHEP
)

$ErrorActionPreference = "Stop"

function Write-Stage($msg) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $msg -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Get-Solver {
    if (Get-Command mamba -ErrorAction SilentlyContinue) {
        return "mamba"
    }
    elseif (Get-Command conda -ErrorAction SilentlyContinue) {
        return "conda"
    }
    else {
        throw "Neither mamba nor conda was found. Open Miniforge Prompt, then run this script again."
    }
}

function Run-Cmd($exe, $argList) {
    Write-Host ""
    Write-Host "> $exe $($argList -join ' ')" -ForegroundColor DarkGray
    & $exe @argList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $exe $($argList -join ' ')"
    }
}

function Env-Exists($envName) {
    $out = conda env list
    return ($out -match "^\s*$envName\s")
}

function Create-Env($solver, $envName, $packages) {
    if (Env-Exists $envName) {
        Write-Host "Environment '$envName' already exists. Skipping create." -ForegroundColor Yellow
        return
    }
    $args = @("create", "-n", $envName, "-c", "conda-forge", "-y") + $packages
    Run-Cmd $solver $args
}

function Register-Kernel($envName, $displayName) {
    Run-Cmd "conda" @("run", "-n", $envName, "python", "-m", "ipykernel", "install", "--user", "--name", $envName, "--display-name", $displayName)
}

function Sanity-Test($envName, $code) {
    Run-Cmd "conda" @("run", "-n", $envName, "python", "-c", $code)
}

Write-Stage "SAT Stack Installer — Windows / Miniforge"

$solver = Get-Solver
Write-Host "Using solver: $solver" -ForegroundColor Green

Write-Stage "Configuring conda-forge"
Run-Cmd "conda" @("config", "--add", "channels", "conda-forge")
Run-Cmd "conda" @("config", "--set", "channel_priority", "strict")

if (-not $SkipCore) {
    Write-Stage "Installing sat-core"
    $satCore = @(
        "python=3.12",
        "numpy", "scipy", "sympy", "mpmath", "matplotlib", "pandas",
        "scikit-image", "scikit-learn", "numba", "networkx",
        "jupyterlab", "ipykernel", "tqdm", "pillow", "imageio", "pyyaml"
    )
    Create-Env $solver "sat-core" $satCore
    Register-Kernel "sat-core" "Python (SAT Core)"
    Sanity-Test "sat-core" "import numpy, scipy, sympy, matplotlib, skimage, sklearn, numba, networkx; print('sat-core OK')"
}

if (-not $CoreOnly -and -not $SkipVisual) {
    Write-Stage "Installing sat-visual"
    $satVisual = @(
        "python=3.12",
        "numpy", "scipy", "sympy", "matplotlib",
        "pyvista", "vtk", "trimesh", "meshio", "plotly", "ipywidgets",
        "jupyterlab", "ipykernel", "pillow", "imageio", "pyyaml"
    )
    Create-Env $solver "sat-visual" $satVisual
    Register-Kernel "sat-visual" "Python (SAT Visual)"
    Sanity-Test "sat-visual" "import pyvista, vtk, trimesh, plotly; print('sat-visual OK')"
}

if (-not $CoreOnly -and -not $SkipJax) {
    Write-Stage "Installing sat-jax"
    $satJax = @(
        "python=3.12",
        "numpy", "scipy", "matplotlib", "sympy",
        "jupyterlab", "ipykernel", "tqdm", "pip"
    )
    Create-Env $solver "sat-jax" $satJax
    Run-Cmd "conda" @("run", "-n", "sat-jax", "python", "-m", "pip", "install", "-U", "jax[cpu]")
    Register-Kernel "sat-jax" "Python (SAT JAX)"
    Sanity-Test "sat-jax" "import jax, jax.numpy as jnp; print('sat-jax OK', jnp.array([1,2,3])**2)"
}

if ($InstallQuantum) {
    Write-Stage "Installing sat-quantum"
    $satQuantum = @(
        "python=3.12",
        "numpy", "scipy", "sympy", "matplotlib", "qutip", "sparse",
        "jupyterlab", "ipykernel", "tqdm"
    )
    Create-Env $solver "sat-quantum" $satQuantum
    Register-Kernel "sat-quantum" "Python (SAT Quantum)"
    Sanity-Test "sat-quantum" "import qutip; print('sat-quantum OK')"
}

if ($InstallHEP) {
    Write-Stage "Installing sat-hep"
    $satHEP = @(
        "python=3.12",
        "numpy", "scipy", "sympy", "matplotlib", "pandas",
        "awkward", "uproot", "vector", "hist", "boost-histogram", "particle", "hepunits",
        "jupyterlab", "ipykernel", "tqdm"
    )
    Create-Env $solver "sat-hep" $satHEP
    Register-Kernel "sat-hep" "Python (SAT HEP)"
    Sanity-Test "sat-hep" "import awkward, uproot, vector, hist, particle; print('sat-hep OK')"
}

Write-Stage "Cleaning package caches"
Run-Cmd $solver @("clean", "--all", "-y")

Write-Stage "Installed environments"
Run-Cmd "conda" @("env", "list")

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Use examples:" -ForegroundColor Green
Write-Host "  conda activate sat-core"
Write-Host "  python equation_true_curve_surface_projection_polar_nopandas.py"
Write-Host ""
Write-Host "Jupyter kernels installed:"
Write-Host "  Python (SAT Core)"
Write-Host "  Python (SAT Visual)"
Write-Host "  Python (SAT JAX)"
Write-Host "  plus optional Quantum/HEP if selected"
