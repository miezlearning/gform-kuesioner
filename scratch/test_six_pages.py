import requests
from bs4 import BeautifulSoup

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
SUBMIT_URL = FORM_URL.replace("/viewform", "/formResponse")

def get_session_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    fbzx_input = soup.find("input", {"name": "fbzx"})
    fbzx = fbzx_input.get("value") if fbzx_input else ""
    fvv_input = soup.find("input", {"name": "fvv"})
    fvv = fvv_input.get("value") if fvv_input else "1"
    return fbzx, fvv

fbzx, fvv = get_session_data(FORM_URL)
print(f"Extracted session data: fbzx={fbzx}, fvv={fvv}")

# We will set pageHistory to "0,1,2,3,4,5" to signify that all 6 sections (Email + 5 question pages) were completed.
payload = {
    # Session data
    "fbzx": fbzx,
    "fvv": fvv,
    "pageHistory": "0,1,2,3,4,5",
    
    # Answers
    "entry.1263102269": "TEST PAGE HISTORY 6 PAGES",
    "entry.1052711449": "2409106991", # NIM
    "entry.909243868": "2024",        # Angkatan
    
    # Scale answers (1-5)
    "entry.644587868": "5",
    "entry.1204149345": "5",
    "entry.1160960572": "5",
    "entry.1679488464": "5",
    "entry.1997403812": "5",
    "entry.81088305": "5",
    "entry.1516128006": "5",
    "entry.210452527": "5",
    "entry.1304503573": "5",
    "entry.1693152674": "5",
    "entry.2110136957": "5",
    "entry.1601385990": "5",
    "entry.1657901429": "5",
    "entry.439233770": "5",
    "entry.2146671926": "5",
    "entry.1531373470": "5",
    "entry.1019296480": "5",
    "entry.2050442328": "5",
    
    # Text opinions/suggestions
    "entry.1831604431": "Website ini sangat berguna dan mempercepat administrasi mahasiswa.",
    "entry.1844992149": "Saran agar kecepatan aksesnya terus ditingkatkan agar lancar.",
    
    # Email
    "emailAddress": "testpagehistory6@gmail.com"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.post(SUBMIT_URL, data=payload, headers=headers)
print("Status Code:", response.status_code)
if "Jawaban Anda telah direkam" in response.text:
    print("SUCCESS: Submitted with 6 pageHistory pages!")
else:
    print("FAILED: Submission did not succeed.")
