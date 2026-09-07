"""Definition of the filament-ensemble averaging operator for O2."""

import sympy as sp

def ensemble_average(f_func, config_vars, H_func, T, measure):
    """
    Computes the canonical ensemble average:
      <f>_F = (1/Z) ∫ f(ξ) e^{-H(ξ)/T} dμ(ξ)
    f_func: function taking config_vars and returning an expression
    config_vars: tuple of sympy symbols (ξ₁, ξ₂, ...)
    H_func: function taking config_vars and returning Hamiltonian H(ξ)
    T: ensemble "temperature" parameter
    measure: product of differential sympy symbols, e.g. dξ₁*dξ₂*...
    """
    exponent = sp.exp(-H_func(*config_vars) / T)
    Z = sp.integrate(exponent * measure, config_vars)
    num = sp.integrate(f_func(*config_vars) * exponent * measure, config_vars)
    return sp.simplify(num / Z)
