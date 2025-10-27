
def get_structure():
    return {
        "mass_squared_rule": "m^2 = k·(N + β·Q² - a)",
        "parameters": {
            "k": "scale factor from network tension or strain (sets overall scale)",
            "β": "topological amplification factor for Q² dependence",
            "a": "offset parameter to anchor ground state (e.g. pion mass)"
        },
        "inputs": {
            "Q": "topological charge (from O4 structure)",
            "N": "vibrational excitation number (0, 1, 2, ...)"
        },
        "outputs": {
            "m²": "inertial rest mass squared (in consistent units)"
        },
        "notes": [
            "This relation models mass spectra of bound filamentary states.",
            "Applies to stable Q ≤ 3 topologies; unstable or exotic Q > 3 not covered.",
            "Goldstone-like states arise when a = β·Q² for N = 0.",
            "This module completes the mass sector linkage in SAT from topology."
        ]
    }
