import requests
import json
import re

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
SUBMIT_URL = FORM_URL.replace("/viewform", "/formResponse")

# Let's mock a payload matching what the original script sent
# We will use hardcoded mapping based on the inspection
payload = {
    "entry.1263102269": "TEST NAMA LENGKAP",
    "entry.1052711449": "2409106045", # NIM
    "entry.909243868": "2024",        # Angkatan (Radio button)
    "entry.644587868": "4",           # Scale 1-5
    "entry.1204149345": "4",
    "entry.1160960572": "4",
    "entry.1679488464": "4",
    "entry.1997403812": "4",
    "entry.81088305": "4",
    "entry.1516128006": "4",
    "entry.210452527": "4",
    "entry.1304503573": "4",
    "entry.1693152674": "4",
    "entry.2110136957": "4",
    "entry.1601385990": "4",
    "entry.1657901429": "4",
    "entry.439233770": "4",
    "entry.2146671926": "4",
    "entry.1531373470": "4",
    "entry.1019296480": "4",
    "entry.2050442328": "4",
    "entry.1831604431": "Website sangat bermanfaat.", # Pendapat
    "entry.1844992149": "Saran agar loadingnya dipercepat.", # Saran
    "emailAddress": "testemail@gmail.com"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.post(SUBMIT_URL, data=payload, headers=headers)
print("Status Code:", response.status_code)
# Save response html to a file to inspect
with open("scratch/submit_response.html", "w", encoding="utf-8") as f:
    f.write(response.text)

if "Tanggapan Anda telah direkam" in response.text or "Your response has been recorded" in response.text:
    print("SUCCESS: Response was recorded!")
else:
    print("FAILED: Maybe validation errors occurred.")
    # Check if there are error messages in the HTML
    # Google Forms typically has some JS or text for validation errors
    # Let's print some snippets of the output
    if "Salah" in response.text or "Error" in response.text or "wajib" in response.text:
        print("Found keywords indicating failure/validation issues.")
