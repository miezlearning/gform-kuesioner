import json

with open("scratch/raw_form_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

questions = raw_data[1][1]

page_index = -1  # Start at -1, will become 0 when first section header is found
# But page 0 is email page (built-in), so actual form pages start at 1

print("Full form structure with entry IDs:\n")
print("=== PAGE 0: Email (built-in) ===")
print("  emailAddress\n")

for i, item in enumerate(questions):
    title = item[1]
    type_code = item[3]
    
    if type_code == 8:
        page_index += 1
        print(f"\n=== PAGE {page_index + 1}: {title} ===")
    else:
        try:
            entry_id = item[4][0][0]
            print(f"  entry.{entry_id} -> {title} (Type: {type_code})")
        except (IndexError, TypeError):
            print(f"  [no entry ID] -> {title} (Type: {type_code})")
