import requests
from bs4 import BeautifulSoup
import re

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"

response = requests.get(FORM_URL)
soup = BeautifulSoup(response.text, "html.parser")

print("--- Printing form fields from HTML inputs ---")

# Look for inputs/textareas/selects
inputs = soup.find_all(["input", "textarea", "select"])
print(f"Found {len(inputs)} input/textarea/select tags.")

entry_names = set()
for inp in inputs:
    name = inp.get("name")
    if name:
        entry_names.add(name)
        # Try to find parent text to see the label
        parent_text = ""
        # Traverse up to find some label text
        parent = inp.parent
        for _ in range(8):
            if parent:
                # Look for data-params or label class
                text = parent.get_text(strip=True)
                if text:
                    parent_text = text[:100]
                    break
                parent = parent.parent
        print(f"Tag: {inp.name} | name: {name} | Text near: {parent_text}")

print("\nAll entry names found in HTML input tags:")
for name in sorted(list(entry_names)):
    print(f"  - {name}")

# Also check for data-params or jsmodel elements that might contain the entry IDs
print("\n--- Checking divs with entry IDs ---")
divs = soup.find_all("div", jsmodel=True)
for d in divs:
    jsdata = d.get("jsdata")
    if jsdata:
        print(f"Div with jsdata: {jsdata} | Text near: {d.get_text(strip=True)[:100]}")
