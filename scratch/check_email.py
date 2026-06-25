"""Quick check: does the form HTML contain emailAddress input?"""
import requests
from bs4 import BeautifulSoup

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"

response = requests.get(FORM_URL, timeout=15)
html = response.text
soup = BeautifulSoup(html, "html.parser")

email_input = soup.find("input", {"name": "emailAddress"})
print(f"emailAddress input found: {email_input is not None}")
if email_input:
    print(f"  tag: {email_input}")
    
# Also check in raw HTML
has_in_raw = "emailAddress" in html
print(f"'emailAddress' in raw HTML: {has_in_raw}")

# Check for email collection in the FB_PUBLIC_LOAD_DATA
import re, json
match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
if match:
    raw_data = json.loads(match.group(1))
    # Check if email collection is enabled - usually in raw_data[1][10] or similar
    print(f"\nraw_data[1][0] (form title?): {raw_data[1][0]}")
    # Check array indices that might indicate email collection
    try:
        print(f"raw_data[1][10] (settings?): {raw_data[1][10]}")
    except:
        pass
    try:
        print(f"raw_data[1][8] (settings?): {raw_data[1][8]}")
    except:
        pass
