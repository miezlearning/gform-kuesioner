"""
Debug script: compare the exact payload our Python code generates
vs the captured Playwright payload that was known to work.
"""
import json
import time
import random
from urllib.parse import urlencode, parse_qs, unquote

# ============================================================
# 1. Reconstruct the EXACT Playwright payload (known working)
# ============================================================
with open("scratch/captured_payload.json", "r", encoding="utf-8") as f:
    captured = json.load(f)

playwright_raw = captured["post_data"]
playwright_parsed = parse_qs(playwright_raw)

print("=" * 70)
print("PLAYWRIGHT PAYLOAD (known working)")
print("=" * 70)
for key in sorted(playwright_parsed.keys()):
    val = playwright_parsed[key][0]
    if key == "partialResponse":
        pr = json.loads(val)
        print(f"  {key} = (JSON, {len(json.dumps(pr))} chars)")
        # Print the structure
        entries = pr[0]
        print(f"    -> {len(entries)} entries in partialResponse[0]")
        print(f"    -> fbzx in partialResponse: {pr[2]}")
        print(f"    -> email in partialResponse: {pr[6]}")
        print(f"    -> flag in partialResponse: {pr[7]}")
    elif len(val) > 80:
        print(f"  {key} = {val[:80]}...")
    else:
        print(f"  {key} = {val}")

# Check which top-level entry keys are present
playwright_entry_keys = sorted([k for k in playwright_parsed if k.startswith("entry.")])
print(f"\nTop-level entry keys ({len(playwright_entry_keys)}):")
for k in playwright_entry_keys:
    print(f"  {k} = {playwright_parsed[k][0]}")

# Check for emailAddress
print(f"\n'emailAddress' in top-level: {'emailAddress' in playwright_parsed}")

print("\n")

# ============================================================
# 2. Generate what our Python kuesioner.py code would produce
# ============================================================
import sys
sys.path.insert(0, ".")
import kuesioner

form_data = kuesioner.extract_form_structure(kuesioner.FORM_URL)
pages = form_data["pages"]
fbzx = form_data["fbzx"]
fvv = form_data["fvv"]
has_email_page = form_data["has_email_page"]
page_history = form_data["page_history"]

# Use fixed test values
nama = "TEST DEBUG USER"
nim = "2409106099"
angkatan = "2024"
email = "testdebug24@gmail.com"
pendapat = "Test pendapat."
saran = "Test saran."

# Generate all page values
all_page_values = []
for page in pages:
    page_values = []
    for field in page:
        value = kuesioner.generate_field_value(field, nama, nim, angkatan, pendapat, saran, email)
        page_values.append({
            "entry_id": field["entry_id"],
            "value": value,
            "label": field["label"]
        })
    all_page_values.append(page_values)

# Build partialResponse
partial_entries = []
for page_values in all_page_values[:-1]:
    for field_val in page_values:
        partial_entries.append((field_val["entry_id"], field_val["value"]))

partial_response_json = kuesioner.build_partial_response(partial_entries, fbzx, email)

# Build top-level payload
payload = {}
last_page = all_page_values[-1]
for field_val in last_page:
    entry_key = f"entry.{field_val['entry_id']}"
    payload[entry_key] = field_val["value"]
    for field in pages[-1]:
        if field["entry_id"] == field_val["entry_id"] and field["type"] == 5:
            payload[f"{entry_key}_sentinel"] = ""
            break

payload["fvv"] = fvv
payload["partialResponse"] = partial_response_json
payload["pageHistory"] = page_history
payload["fbzx"] = fbzx
payload["submissionTimestamp"] = str(int(time.time() * 1000))

if has_email_page:
    payload["emailAddress"] = email

print("=" * 70)
print("PYTHON KUESIONER.PY PAYLOAD (our code)")
print("=" * 70)
for key in payload:
    val = str(payload[key])
    if key == "partialResponse":
        pr = json.loads(val)
        print(f"  {key} = (JSON, {len(val)} chars)")
        entries = pr[0]
        print(f"    -> {len(entries)} entries in partialResponse[0]")
        print(f"    -> fbzx in partialResponse: {pr[2]}")
        print(f"    -> email in partialResponse: {pr[6]}")
        print(f"    -> flag in partialResponse: {pr[7]}")
    elif len(val) > 80:
        print(f"  {key} = {val[:80]}...")
    else:
        print(f"  {key} = {val}")

python_entry_keys = sorted([k for k in payload if k.startswith("entry.")])
print(f"\nTop-level entry keys ({len(python_entry_keys)}):")
for k in python_entry_keys:
    print(f"  {k} = {payload[k]}")

print(f"\n'emailAddress' in top-level: {'emailAddress' in payload}")

# ============================================================
# 3. KEY DIFFERENCES
# ============================================================
print("\n" + "=" * 70)
print("KEY DIFFERENCES")
print("=" * 70)

# Playwright has no emailAddress at top level
print(f"1. Playwright has 'emailAddress' at top level: {'emailAddress' in playwright_parsed}")
print(f"   Python has 'emailAddress' at top level: {'emailAddress' in payload}")

# Compare entry key sets  
pw_entries = set(k for k in playwright_parsed if k.startswith("entry."))
py_entries = set(k for k in payload if k.startswith("entry."))
print(f"\n2. Playwright top-level entry keys: {sorted(pw_entries)}")
print(f"   Python top-level entry keys: {sorted(py_entries)}")

# Compare key order
pw_keys = list(parse_qs(playwright_raw, keep_blank_values=True).keys())
py_encoded = urlencode(payload, doseq=False)
py_keys = list(parse_qs(py_encoded, keep_blank_values=True).keys())
print(f"\n3. Playwright key order: {pw_keys}")
print(f"   Python key order: {py_keys}")

# Compare partialResponse structure
pw_pr = json.loads(playwright_parsed["partialResponse"][0])
py_pr = json.loads(payload["partialResponse"])
print(f"\n4. Playwright partialResponse entry count: {len(pw_pr[0])}")
print(f"   Python partialResponse entry count: {len(py_pr[0])}")
print(f"\n5. Playwright partialResponse structure: [entries, {pw_pr[1]}, fbzx, {pw_pr[3]}, {pw_pr[4]}, {pw_pr[5]}, email, {pw_pr[7]}]")
print(f"   Python partialResponse structure: [entries, {py_pr[1]}, fbzx, {py_pr[3]}, {py_pr[4]}, {py_pr[5]}, email, {py_pr[7]}]")
