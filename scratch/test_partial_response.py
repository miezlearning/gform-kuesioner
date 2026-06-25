import requests
from bs4 import BeautifulSoup
import json

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

# 1. Structure the partialResponse array for pages 1-4
# [ [ [null, entry_id, [value], 0], ... ], null, fbzx, null, null, null, email, 1 ]
email = "testpartialresponse@gmail.com"

partial_entries = [
    # Page 1
    [None, 1263102269, ["TEST PARTIAL RESPONSE NAMA"], 0],
    [None, 1052711449, ["2409106988"], 0],
    [None, 909243868, ["2024"], 0],
    
    # Page 2
    [None, 644587868, ["4"], 0],
    [None, 1204149345, ["4"], 0],
    [None, 1160960572, ["4"], 0],
    [None, 1679488464, ["4"], 0],
    [None, 1997403812, ["4"], 0],
    
    # Page 3
    [None, 81088305, ["4"], 0],
    [None, 1516128006, ["4"], 0],
    [None, 210452527, ["4"], 0],
    [None, 1304503573, ["4"], 0],
    [None, 1693152674, ["4"], 0],
    
    # Page 4
    [None, 2110136957, ["4"], 0],
    [None, 1601385990, ["4"], 0],
    [None, 1657901429, ["4"], 0],
    [None, 439233770, ["4"], 0],
    [None, 2146671926, ["4"], 0]
]

partial_response_val = json.dumps([partial_entries, None, fbzx, None, None, None, email, 1])

# 2. Build the final POST payload
payload = {
    # Page 5 questions (as top-level POST keys)
    "entry.1531373470": "4",
    "entry.1019296480": "4",
    "entry.2050442328": "4",
    "entry.1831604431": "Website sangat bermanfaat dan responsif.",
    "entry.1844992149": "Saran agar kestabilan server dipertahankan.",
    
    # Hidden validation and navigation data
    "fvv": fvv,
    "fbzx": fbzx,
    "pageHistory": "0,1,2,3,4,5",
    "partialResponse": partial_response_val
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.post(SUBMIT_URL, data=payload, headers=headers)
print("Status Code:", response.status_code)
if "Jawaban Anda telah direkam" in response.text:
    print("SUCCESS: Submitted successfully with partialResponse structure!")
else:
    print("FAILED: Submission did not succeed.")
