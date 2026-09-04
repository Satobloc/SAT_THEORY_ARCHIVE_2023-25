import yaml
import sys

class SATCoreValidator:
    def __init__(self, ledger_path):
        self.ledger_path = ledger_path
        self.ledger = self.load_ledger()
        self.errors = []
        self.stats = {"checked": 0, "skipped": 0}

    def load_ledger(self):
        try:
            with open(self.ledger_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to load ledger: {e}")
            sys.exit(1)

    def validate_arithmetic(self):
        """Verify expressions and ensure transparency in coverage [Source 9, 13]"""
        print("--- PHASE 1: Arithmetic Audit ---")
        for constant in self.ledger.get('constants', []):
            expr = constant.get('expression_ascii')
            val = constant.get('value')
            status = constant.get('status')
            
            if expr:
                try:
                    computed = eval(expr)
                    if abs(computed - val) > 1e-12:
                        self.errors.append(f"ARITHMETIC ERROR in {constant['id']}: '{expr}' = {computed}, expected {val}")
                    else:
                        self.stats["checked"] += 1
                except Exception as e:
                    self.errors.append(f"EXECUTION ERROR in {constant['id']}: {e}")
            else:
                if status == 'accepted_core':
                    self.errors.append(f"VERIFICATION FAILURE: {constant['id']} marked 'accepted_core' but lacks checkable expression_ascii.")
                self.stats["skipped"] += 1
        
        print(f"Audit Summary: {self.stats['checked']} verified, {self.stats['skipped']} skipped.")

    def run_audit(self):
        self.validate_arithmetic()
        if self.errors:
            print("\nAUDIT FAILED:")
            for err in self.errors:
                print(f"  - {err}")
            return False
        else:
            print("\nAUDIT PASSED: Internal arithmetic is self-consistent and transparent.")
            return True

if __name__ == "__main__":
    # Updated to handle underscores consistently with file naming [Source 10]
    validator = SATCoreValidator('SAT_CORE_EQUATIONS_v0_1_0.yaml')
    validator.run_audit()