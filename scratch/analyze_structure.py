import json

with open("scratch/raw_form_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

questions_list = raw_data[1][1]

print("Analyzing form fields from JSON data structure:\n")

for i, item in enumerate(questions_list):
    try:
        title = item[1]
        type_code = item[3]
        print(f"Index {i}: {title}")
        print(f"  Type Code: {type_code}")
        
        # Look inside item[4]
        # In Google Form public load data:
        # item[4] contains a list of input elements for the question.
        # Let's print out what is inside item[4]
        entry_list = item[4]
        print(f"  Entry List Length: {len(entry_list)}")
        for idx, entry in enumerate(entry_list):
            entry_id = entry[0]
            print(f"    Sub-entry {idx}: ID={entry_id}")
            
            # Check if there are choices/subquestions (e.g. for grid questions or checkboxes)
            if len(entry) > 1:
                # Let's see other elements
                print(f"      Choices/Metadata: {entry[1:]}")
    except Exception as e:
        print(f"  Error or No Entry details: {e}")
    print("-" * 50)
