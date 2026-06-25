import requests
import json
import re

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"

response = requests.get(FORM_URL)
html = response.text
match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
if match:
    raw_data = json.loads(match.group(1))
    # Let's save the raw_data or print its fields
    with open("scratch/raw_form_data.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)
    
    questions_list = raw_data[1][1]
    print(f"Total question items in list: {len(questions_list)}")
    for i, item in enumerate(questions_list):
        print(f"Item {i}:")
        try:
            print(f"  Title: {item[1]}")
            print(f"  Type code: {item[3]}")
            # print details of item[4]
            entry_info = item[4]
            print(f"  Entry Info: {entry_info}")
        except Exception as e:
            print(f"  Error: {e}")
else:
    print("Could not find FB_PUBLIC_LOAD_DATA_")
