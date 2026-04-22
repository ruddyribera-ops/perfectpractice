"""
PHASE 1.3 REAL CHECK — Check actual tryit format from seed file directly
"""
import re, os

seed_path = "/app/seed/curriculum_seed.py"
if os.path.exists(seed_path):
    with open(seed_path, "r", encoding="utf-8") as f:
        content = f.read()

# Find actual tryit blocks with their raw format
# Look for the SUMA LLEVANDO lesson (has steps with | inside)
lines = content.split("\n")
in_tryit = False
tryit_buffer = ""
tryit_start = 0

for i, line in enumerate(lines):
    if ":::tryit:" in line:
        in_tryit = True
        tryit_buffer = line
        tryit_start = i
    elif in_tryit:
        tryit_buffer += "\n" + line
        if ":::" in line and ":::tryit:" not in line:
            in_tryit = False
            # show first 5
            if "Sumamos" in tryit_buffer or "18 + 7" in tryit_buffer:
                print(f"\nLines {tryit_start+1}-{i+1}:")
                print(tryit_buffer[:300])

print("\n\n--- Sample tryit blocks from seed ---")
# Show 5 example tryit blocks from the seed
count = 0
for i, line in enumerate(lines):
    if ":::tryit:" in line:
        # find the matching :::
        end = i
        while end < len(lines) and ":::" not in lines[end]:
            end += 1
        block = "\n".join(lines[i:end+1])
        print(f"\nL{i+1}: {block[:200]}")
        count += 1
        if count >= 5:
            break