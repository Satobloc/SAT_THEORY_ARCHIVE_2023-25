"""Mapping of SAT parameters to physical constants."""

def map_parameters(T, A, alpha_shape):
    """
    Maps SAT filament parameters to physical scales:
      - planck_mass    ~ sqrt(T)
      - string_length  ~ sqrt(A)
      - alpha_em_deviation = alpha_shape
    T: filament tension
    A: filament rigidity/area parameter
    alpha_shape: diagnostic shape parameter
    """
    planck_mass = T**0.5
    string_length = A**0.5
    alpha_em_deviation = alpha_shape
    return {
        'planck_mass': planck_mass,
        'string_length': string_length,
        'alpha_em_deviation': alpha_em_deviation
    }
