import json

with open("scratch/raw_form_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# The form structure is inside raw_data[1][1]
questions = raw_data[1][1]

page_index = 0
page_items = {}

print("Form layout analysis by page:\n")

for i, item in enumerate(questions):
    title = item[1]
    type_code = item[3]
    
    # In Google Forms, page breaks (Section Headers) have type_code 8.
    # But wait, does every type_code 8 create a new page, or is there a specific page break type?
    # Let's inspect the item array elements.
    # Usually, a page break is represented by type_code 8. Let's see if we can confirm this.
    if type_code == 8:
        print(f"\n--- PAGE {page_index} --- (Section Header: {title})")
        page_index += 1
    else:
        print(f"  Item {i}: {title} (Type: {type_code})")

print(f"\nTotal pages detected by Section Headers: {page_index}")
