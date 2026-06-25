import requests
from bs4 import BeautifulSoup

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"

response = requests.get(FORM_URL)
soup = BeautifulSoup(response.text, "html.parser")

fbzx_input = soup.find("input", {"name": "fbzx"})
fbzx = fbzx_input.get("value") if fbzx_input else "NOT FOUND"

fvv_input = soup.find("input", {"name": "fvv"})
fvv = fvv_input.get("value") if fvv_input else "NOT FOUND"

pageHistory_input = soup.find("input", {"name": "pageHistory"})
pageHistory = pageHistory_input.get("value") if pageHistory_input else "NOT FOUND"

print("Extracted fields:")
print(f"fbzx: {fbzx}")
print(f"fvv: {fvv}")
print(f"pageHistory: {pageHistory}")
