import re

def test_parse(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Split by 9-digit ID
    entries = re.split(r'(?=\b\d{9}\b)', content)
    
    print(f"Total chunks found: {len(entries)}")
    # Print the first 3 chunks to see what's happening
    for i, entry in enumerate(entries[:3]):
        print(f"\n--- Chunk {i} ---")
        print(entry[:150]) # Print first 150 chars of the chunk

test_parse(r"D:\__SAT26\H_UNIVERSES\SIXTY THOUSAND UNIVERSES 5.txt")