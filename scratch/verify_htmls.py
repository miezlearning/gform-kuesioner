# Let's inspect the actual text of both response HTMLs to verify success/failure
with open("scratch/submit_response.html", "r", encoding="utf-8") as f:
    success_html = f.read()

# Let's write the empty response to a file and read it too
import requests
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
SUBMIT_URL = FORM_URL.replace("/viewform", "/formResponse")
payload = {"emailAddress": "testemptyfield@gmail.com"}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
empty_response = requests.post(SUBMIT_URL, data=payload, headers=headers)

print("=== Success HTML (test_submit.py) ===")
print("Contains 'Jawaban Anda telah direkam':", "Jawaban Anda telah direkam" in success_html)
print("Contains 'Tanggapan Anda telah direkam':", "Tanggapan Anda telah direkam" in success_html)
print("Contains 'wajib':", "wajib" in success_html)

print("\n=== Empty HTML (test_empty_submit.py) ===")
print("Contains 'Jawaban Anda telah direkam':", "Jawaban Anda telah direkam" in empty_response.text)
print("Contains 'Tanggapan Anda telah direkam':", "Tanggapan Anda telah direkam" in empty_response.text)
print("Contains 'wajib':", "wajib" in empty_response.text)

# Let's print out what questions are flagged as required/error in the empty submission
from bs4 import BeautifulSoup
soup = BeautifulSoup(empty_response.text, "html.parser")
alerts = soup.find_all(attrs={"role": "alert"})
print("Alerts in empty:", len(alerts))
for i, alert in enumerate(alerts):
    print(f"Alert {i}: {alert.get_text(strip=True)}")
