# tests/test_SAT_O9_O10_integration.py

"""
Integration tests for SAT.O₉ and SAT.O₁₀ modules within the SAT.4D framework.

These tests verify that:
1. O₉ and O₁₀ are inserted into the core module list immediately after O₈.
2. The structure‐lock registry exposes the expected interfaces for O₉ and O₁₀.
3. The downstream D₃ mass‐shell derivation references the string‐derived formula.
4. The glossary includes the new key terms: varphi (Liouville), alpha_prime, and particle_geometry.
5. The directives mark O₉ and O₁₀ as interpretive Mode 2.
"""

import pytest

# 1. Core module ordering
from SAT_CORE_4D import MODULES
def test_core_module_order():
    idx_O8 = MODULES.index('O8')
    assert MODULES[idx_O8 + 1] == 'O9', "O9 should follow O8"
    assert MODULES[idx_O8 + 2] == 'O10', "O10 should follow O9"

# 2. Structure‐lock registry
from SAT_CORE_4D_structure_lock import CORE_STRUCTURE_LOCK
def test_structure_lock_exposes_O9_O10():
    assert 'O9' in CORE_STRUCTURE_LOCK, "O9 must be registered"
    assert 'O10' in CORE_STRUCTURE_LOCK, "O10 must be registered"
    iface_O9 = CORE_STRUCTURE_LOCK['O9']
    iface_O10 = CORE_STRUCTURE_LOCK['O10']
    assert callable(iface_O9.get('get_O9')), "O9 interface should expose get_O9()"
    assert callable(iface_O10.get('get_O10')), "O10 interface should expose get_O10()"

# 3. Downstream D3 derivation reference
from SAT_D3_mass import MASS_SHELL_FORMULA
def test_D3_uses_string_mass_shell():
    doc = MASS_SHELL_FORMULA.__doc__ or ""
    assert 'alpha_prime' in doc, "D3 must reference alpha_prime"
    params = MASS_SHELL_FORMULA.__code__.co_varnames
    assert 'N' in params and 'Q' in params, "Mass‐shell must take N and Q"

# 4. Glossary entries
from SAT_glossary import GLOSSARY
def test_glossary_contains_new_terms():
    for term in ('varphi', 'alpha_prime', 'particle_geometry'):
        assert term in GLOSSARY, f"Glossary must define '{term}'"

# 5. Directives mode flags
from SAT_directives import DIRECTIVES
def test_directives_mode_flags():
    assert DIRECTIVES['O9']['mode'] == 2, "O9 must be Mode 2"
    assert DIRECTIVES['O10']['mode'] == 2, "O10 must be Mode 2"
