import requests
from bs4 import BeautifulSoup

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"

response = requests.get(FORM_URL)
print("Final URL:", response.url)
print("Status Code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")
title = soup.find("title")
if title:
    print("Page Title:", title.get_text(strip=True))
else:
    print("No Title found")

# Let's print some of the HTML body
body_text = soup.body.get_text(strip=True) if soup.body else ""
print("Body length:", len(body_text))
print("Body snippet:", body_text[:500])
