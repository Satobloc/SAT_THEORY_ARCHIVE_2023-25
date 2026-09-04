# SPHERES3

import yaml
import sys
import hashlib

class SATCoreValidator:
    def __init__(self, ledger_path):
        self.ledger_path = ledger_path
        self.ledger = self.load_ledger()
        self.reserved_symbols = {}
        self.errors = []

    def load_ledger(self):
        try:
            with open(self.ledger_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to load ledger at {self.ledger_path}: {e}")
            sys.exit(1)

    def validate_namespace(self):
        """Enforce Namespace Management and Disambiguation [Source 1, 16]"""
        print("--- PHASE 1: Namespace Audit ---")
        for constant in self.ledger.get('constants', []):
            symbol_list = constant.get('symbols', [])
            const_id = constant.get('id')
            for sym in symbol_list:
                if sym in self.reserved_symbols:
                    self.errors.append(f"NOTATIONAL COLLISION: Symbol '{sym}' in {const_id} is already reserved by {self.reserved_symbols[sym]}.")
                self.reserved_symbols[sym] = const_id
        
        if not self.errors:
            print("SUCCESS: No notational collisions detected.")

    def validate_dimensional_integrity(self):
        """Check for dimensional consistency in core anchors [Source 3, 16]"""
        print("\n--- PHASE 2: Dimensional Audit ---")
        # Example check: Ensuring ALPHA_PIN_GEO remains dimensionless
        for constant in self.ledger.get('constants', []):
            if constant['id'] == 'ALPHA_PIN_GEO' and constant['dimensions'] != 'dimensionless':
                self.errors.append("DIMENSIONAL ERROR: ALPHA_PIN_GEO must be dimensionless (Interaction Efficiency).")
        
        if not self.errors:
            print("SUCCESS: Dimensional anchors are consistent.")

    def generate_sha256_baseline(self):
        """Generate the SHA-256 hash to lock the theory foundation [Source 14]"""
        content = yaml.dump(self.ledger, sort_keys=True).encode('utf-8')
        ledger_hash = hashlib.sha256(content).hexdigest()
        print(f"\n--- PHASE 3: SHA-256 Integrity Lock ---")
        print(f"SHA-256 Baseline: {ledger_hash}")
        return ledger_hash

    def run_audit(self):
        self.validate_namespace()
        self.validate_dimensional_integrity()
        
        if self.errors:
            print("\nAUDIT FAILED:")
            for err in self.errors:
                print(f"  - {err}")
            return False
        else:
            self.generate_sha256_baseline()
            print("\nAUDIT PASSED: Core Equation Ledger is stabilized.")
            return True

if __name__ == "__main__":
    validator = SATCoreValidator('SAT_CORE_EQUATIONS_v0_1_0.yaml')
    validator.run_audit()