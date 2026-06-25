import requests

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
SUBMIT_URL = FORM_URL.replace("/viewform", "/formResponse")

# Send only emailAddress, no other fields
payload = {
    "emailAddress": "testemptyfield@gmail.com"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.post(SUBMIT_URL, data=payload, headers=headers)
print("Status Code:", response.status_code)

if "Tanggapan Anda telah direkam" in response.text or "Your response has been recorded" in response.text:
    print("SUCCESS: It accepted the empty submission!")
else:
    print("FAILED: It rejected the empty submission.")
