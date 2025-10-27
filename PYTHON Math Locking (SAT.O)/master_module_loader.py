"""
SAT4DCORE_MASTER_STRUCTURE_LOCK.py

Imports and aggregates the structure from SAT_O1–SAT_O8 modules.
"""

from SAT_O1_structure_lock import get_structure as get_O1
from SAT_O2_structure_lock import get_structure as get_O2
from SAT_O3_structure_lock import get_structure as get_O3
from SAT_O4_structure_lock import get_structure as get_O4
from SAT_O5_structure_lock import get_structure as get_O5
from SAT_O6_structure_lock import get_structure as get_O6
from SAT_O7_structure_lock import get_structure as get_O7
from SAT_O8_structure_lock import get_structure as get_O8

def get_all_structures():
    """Return a dict mapping module names to their locked structures."""
    return {
        'O1': get_O1(),
        'O2': get_O2(),
        'O3': get_O3(),
        'O4': get_O4(),
        'O5': get_O5(),
        'O6': get_O6(),
        'O7': get_O7(),
        'O8': get_O8(),
    }

if __name__ == "__main__":
    all_struct = get_all_structures()
    for module_name, struct in all_struct.items():
        print(f"=== {module_name} ===")
        for key, val in struct.items():
            print(f"{key}: {val}")
