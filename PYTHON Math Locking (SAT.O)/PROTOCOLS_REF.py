
"""
PROTOCOLS_REF.py — Core Logic Protocol Definitions for SAT_O System
Authoritative static file. Invoked by SHEPARD.py and auditing tools.
This module encodes all SAT_O logic rules, enforcement protocols, and control contracts.
"""

# === PLACEHOLDER HANDLING PROTOCOL ===

PLACEHOLDER_TOKEN = "[\\PLACEHOLDER\\]"

def is_placeholder(value):
    return isinstance(value, str) and PLACEHOLDER_TOKEN in value

def handle_placeholder(value, context):
    if is_placeholder(value):
        raise RuntimeError(f"PLACEHOLDER detected in {context}. Execution must halt until resolved.")

# === CONTEXT HASH POLICY ===

import hashlib

def compute_hash_from_string(data_string):
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def compare_context_hashes(stored_hash, current_hash):
    if stored_hash != current_hash:
        raise ValueError("Context hash mismatch. Module invalidated. Must revalidate before proceeding.")

# === BLOCKER DEFINITION & ESCALATION ===

BLOCKER_CATEGORIES = {
    'CRITICAL': "Impacts foundational state. Halts full build.",
    'LOCAL': "Affects individual module only.",
    'AMBIGUITY': "Execution path unresolved — user input required."
}

def log_blocker(module_id, blocker_type, description):
    return {
        'module': module_id,
        'type': blocker_type,
        'description': description
    }

# === AMBIGUITY RESOLUTION PROTOCOL ===

def resolve_ambiguity(options, context):
    """
    Presents ambiguity options to user.
    Execution halts until a valid choice is made.
    """
    print(f"AMBIGUITY in {context}:")
    for i, opt in enumerate(options):
        print(f"[{i}] {opt}")
    print("Awaiting explicit user choice.")
    raise RuntimeError("Execution paused for ambiguity resolution.")

# === SYMBOLIC LOGIC CONSISTENCY RULES ===

LOGICAL_DEPENDENCIES = {
    # Example: 'O2': ['O1'],  # O2 requires O1 to be valid
}

def verify_logical_dependencies(module_id, completed_modules):
    required = LOGICAL_DEPENDENCIES.get(module_id, [])
    for dep in required:
        if dep not in completed_modules:
            raise RuntimeError(f"Logical dependency failure: {module_id} requires {dep}.")

# === MODULE VALIDATION CRITERIA ===

def validate_numeric_output(value, lower_bound=None, upper_bound=None, allow_inf=False):
    if value is None or isinstance(value, str):
        raise ValueError("Invalid or undefined numeric output.")
    if not allow_inf and (value == float('inf') or value == float('-inf')):
        raise ValueError("Infinite value not allowed.")
    if lower_bound is not None and value < lower_bound:
        raise ValueError(f"Output below bound: {value} < {lower_bound}")
    if upper_bound is not None and value > upper_bound:
        raise ValueError(f"Output above bound: {value} > {upper_bound}")

# === CODE/DATA CONSISTENCY POLICY ===

def enforce_naming_consistency(term_from_glossary, term_from_code):
    if term_from_glossary != term_from_code:
        raise ValueError(f"Nomenclature mismatch: glossary '{term_from_glossary}' vs code '{term_from_code}'.")

def verify_data_version(data_file_version, required_version):
    if data_file_version != required_version:
        raise RuntimeError(f"Data version mismatch. Found {data_file_version}, required {required_version}.")

# === END PROTOCOL DEFINITIONS ===
