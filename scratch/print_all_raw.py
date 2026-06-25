import json

with open("scratch/raw_form_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Let's inspect the top-level keys or structures
# Typically, raw_data has:
# raw_data[1][1] - questions list
# Let's check other elements in raw_data[1]
print("raw_data[1] length:", len(raw_data[1]))
for idx, val in enumerate(raw_data[1]):
    if val is not None:
        val_str = str(val)[:200]
        print(f"Index {idx}: {val_str}")
