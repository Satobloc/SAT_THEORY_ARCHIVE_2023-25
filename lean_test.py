import lean_dojo as ld
from tempfile import NamedTemporaryFile
import os

# Simple Lean theorem for testing
lean_code = """
theorem add_zero (n : Nat) : n + 0 = n := by
  induction n
  case zero => rfl
  case succ n ih => simp [ih]
"""

# Create a temporary Lean file
with NamedTemporaryFile(mode="w+", suffix=".lean", delete=False) as f:
    f.write(lean_code)
    filepath = f.name

# Determine the root directory (folder containing the file)
root_dir = os.path.dirname(filepath)

# Load the Lean file
lean_file = ld.LeanFile(path=filepath, root_dir=root_dir)

# Check proofs in the file
results = ld.check_proof(lean_file)

# Print results
for r in results:
    print(r)
