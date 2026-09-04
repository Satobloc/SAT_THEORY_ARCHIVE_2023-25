import os

print("--- DIAGNOSTIC START ---")
folder = r"D:\__SAT26\H_UNIVERSES"
files = [f for f in os.listdir(folder) if f.startswith(("SIXTY", "RANDOM_H"))]

if not files:
    print(f"FAILED: No files found starting with 'SIXTY' or 'RANDOM_H' in {folder}")
else:
    print(f"SUCCESS: Found {len(files)} files: {files}")
    for filename in files:
        path = os.path.join(folder, filename)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(100)
            print(f"\nFile: {filename}")
            print(f"Preview (first 100 chars): {content}")
            if not content.strip():
                print("WARNING: File appears empty.")

print("\n--- DIAGNOSTIC END ---")
input("Press Enter to close...")