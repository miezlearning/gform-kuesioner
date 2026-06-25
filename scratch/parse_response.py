from bs4 import BeautifulSoup

with open("scratch/submit_response.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Find any validation error messages or alert boxes
# Google Forms usually has divs or spans with role="alert" or error class names
alerts = soup.find_all(attrs={"role": "alert"})
print("Alerts found:", len(alerts))
for i, alert in enumerate(alerts):
    print(f"Alert {i}: {alert.get_text(strip=True)}")

# Let's search for any element with class containing "error" or "warning"
for tag in soup.find_all(class_=True):
    classes = tag.get("class")
    for c in classes:
        if "error" in c.lower() or "warning" in c.lower() or "invalid" in c.lower():
            text = tag.get_text(strip=True)
            if text:
                print(f"Class: {c} | Text: {text}")

# Check if there is a main title or heading of the form response
heading = soup.find("h1") or soup.find("div", class_="freebirdFormviewerViewResponseConfirmContent")
if heading:
    print("Heading text:", heading.get_text(strip=True))

# Print first 2000 chars of visible text to get a sense of what's on the page
print("\n--- Page text (snippet) ---")
print(soup.get_text()[:1500])
