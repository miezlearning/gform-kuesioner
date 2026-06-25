import json
import re

transcript_path = "C:/Users/Miez/.gemini/antigravity-ide/brain/0a26e652-b05f-4394-9b28-776fee086bcb/.system_generated/logs/transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    data = json.loads(line)
    # Search for UUIDs or conversation IDs in the step data
    line_str = json.dumps(data)
    uuids = re.findall(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', line_str)
    if uuids:
        # Filter out our own conversation ID
        our_id = "0a26e652-b05f-4394-9b28-776fee086bcb"
        other_uuids = [u for u in uuids if u != our_id]
        if other_uuids:
            print(f"Line {idx+1} contains other UUIDs: {other_uuids}")
