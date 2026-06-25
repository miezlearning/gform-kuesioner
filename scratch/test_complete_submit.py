import requests
from bs4 import BeautifulSoup
import json
import random

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
SUBMIT_URL = FORM_URL.replace("/viewform", "/formResponse")

def get_session_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    fbzx_input = soup.find("input", {"name": "fbzx"})
    fbzx = fbzx_input.get("value") if fbzx_input else ""
    fvv_input = soup.find("input", {"name": "fvv"})
    fvv = fvv_input.get("value") if fvv_input else "1"
    pageHistory_input = soup.find("input", {"name": "pageHistory"})
    pageHistory = pageHistory_input.get("value") if pageHistory_input else "0"
    return fbzx, fvv, pageHistory

fbzx, fvv, pageHistory = get_session_data(FORM_URL)
print(f"Extracted session data: fbzx={fbzx}, fvv={fvv}, pageHistory={pageHistory}")

payload = {
    # Session data
    "fbzx": fbzx,
    "fvv": fvv,
    "pageHistory": pageHistory,
    
    # Answers
    "entry.1263102269": "ANTIGRAVITY TEST NAME",
    "entry.1052711449": "2409106099", # NIM
    "entry.909243868": "2024",        # Angkatan
    
    # Scale answers
    "entry.644587868": "4",
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
    
    # Text opinions/suggestions
    "entry.1831604431": "Website ini sangat memudahkan mahasiswa dalam urusan administrasi secara online.",
    "entry.1844992149": "Saran agar antarmuka terus diperbarui dan performa server ditingkatkan.",
    
    # Email
    "emailAddress": "antigravitytest@gmail.com"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.post(SUBMIT_URL, data=payload, headers=headers)
print("Status Code:", response.status_code)
if "Jawaban Anda telah direkam" in response.text:
    print("SUCCESS: Form submitted with session data!")
else:
    print("FAILED: Submission did not succeed.")
