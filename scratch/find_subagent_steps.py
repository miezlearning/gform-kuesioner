import json

transcript_path = "C:/Users/Miez/.gemini/antigravity-ide/brain/0a26e652-b05f-4394-9b28-776fee086bcb/.system_generated/logs/transcript_full.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines in transcript: {len(lines)}")

# We will look for step containing "BROWSER_SUBAGENT"
for idx, line in enumerate(lines):
    data = json.loads(line)
    if data.get("type") == "BROWSER_SUBAGENT":
        print(f"\nFound BROWSER_SUBAGENT at line {idx+1}")
        content = data.get("content", "")
        # Search for localStorage or capturedFormData in the content
        if "capturedFormData" in content or "__capturedFetchData" in content:
            print("Found captured data key in subagent content!")
        
        # Let's print out lines in the subagent's actions report that mention javascript execution results
        report_lines = content.split("\n")
        print(f"Report has {len(report_lines)} lines.")
        for r_idx, r_line in enumerate(report_lines):
            if "execute_browser_javascript" in r_line or "localStorage" in r_line or "History" in r_line or "history" in r_line:
                print(f"  Line {r_idx}: {r_line[:150]}")
                # Also print the next few lines if it's Javascript output
                for offset in range(1, 10):
                    if r_idx + offset < len(report_lines):
                        print(f"    +{offset}: {report_lines[r_idx+offset][:150]}")
