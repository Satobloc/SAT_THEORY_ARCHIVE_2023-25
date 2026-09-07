"""Candidate tension potential forms for O1 using symbolic definitions."""

import sympy as sp

def elastic_rod_potential(xi_func, lam, kappa, a, b):
    """
    Elastic rod model potential:
      V_tension = (kappa / 2) * ∫ |d²ξ/dλ²|² dλ
    xi_func: function of lam returning a sympy Matrix
    lam: sympy symbol
    kappa: rigidity constant
    a, b: domain limits for λ
    """
    xi_dd = sp.diff(xi_func(lam), lam, 2)
    integrand = xi_dd.dot(xi_dd)
    V = (kappa/2) * sp.integrate(integrand, (lam, a, b))
    return sp.simplify(V)

def nambu_goto_like_potential(xi_func, lam, T, a, b):
    """
    Generalized Nambu–Goto string tension model:
      V_tension = T * ∫ sqrt(|dξ/dλ|²) dλ
    xi_func: function of lam returning a sympy Matrix
    lam: sympy symbol
    T: tension parameter
    a, b: domain limits for λ
    """
    xi_d = sp.diff(xi_func(lam), lam)
    integrand = sp.sqrt(xi_d.dot(xi_d))
    V = T * sp.integrate(integrand, (lam, a, b))
    return sp.simplify(V)
