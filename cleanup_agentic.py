"""Remove duplicate old content from agentic_assistant.py"""

# Read the file
with open("api/src/services/agentic_assistant.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Original file: {len(lines)} lines")

# Find the markers
# Start: After "from api.src.models import Agency" (should be around line 623)
# End: Before the SECOND "async def chat" that has proper parameters

start_marker_found = False
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if "from api.src.models import Agency" in line and start_idx is None:
        start_idx = i + 1  # Start deleting from next line
        print(f"Found start marker at line {i+1}: {line.strip()[:50]}")
    
    # Find the second async def chat (the correct one with full signature)
    if "async def chat(" in line and start_idx is not None:
        # Check if next few lines have proper parameters
        if i+3 < len(lines) and "message: str" in lines[i+2]:
            end_idx = i
            print(f"Found end marker at line {i+1}: {line.strip()[:50]}")
            break

if start_idx and end_idx:
    print(f"Removing lines {start_idx+1} to {end_idx}")
    print(f"Lines to remove: {end_idx - start_idx}")
    
    # Remove the duplicate content
    new_lines = lines[:start_idx] + lines[end_idx:]
    
    print(f"New file: {len(new_lines)} lines")
    print(f"Removed: {len(lines) - len(new_lines)} lines")
    
    # Write back
    with open("api/src/services/agentic_assistant.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("✅ Cleanup complete!")
else:
    print(f"❌ Could not find markers: start_idx={start_idx}, end_idx={end_idx}")
