import csv
import json
import re
import random
import time
import requests

# We import / use the same functions as kuesioner.py but mock the submission to print payload
CSV_FILE_PATH = "dataset/2024.csv"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"
AI_API_URL = "https://apis.prexzyvilla.site/ai/gpt-5"

def extract_form_fields(form_url):
    try:
        response = requests.get(form_url, timeout=15)
        if response.status_code != 200:
            return None
        html = response.text
        match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
        if not match:
            return None
        raw_data = json.loads(match.group(1))
        questions_list = raw_data[1][1]
        mapped_fields = {}
        for item in questions_list:
            try:
                label = item[1].strip()
                entry_id = f"entry.{item[4][0][0]}"
                mapped_fields[label] = entry_id
            except (IndexError, TypeError):
                continue
        return mapped_fields
    except Exception as e:
        return None

def load_students_from_csv(file_path):
    students = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            clean_row = {key.strip().lower(): val.strip() for key, val in row.items() if key}
            if 'nim' in clean_row and 'nama' in clean_row:
                students.append({
                    "nim": clean_row['nim'],
                    "nama": clean_row['nama']
                })
    return students

def generate_scale_answer():
    return str(random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 48, 30])[0])

def generate_ai_text(prompt_type):
    # Let's see what the actual API returns and check if there's a problem
    try:
        response = requests.get(AI_API_URL, params={"text": "hello"}, timeout=15)
        data = response.json()
        print("API JSON Response format:", json.dumps(data, indent=2))
        
        # Real code from kuesioner.py:
        ai_text = data.get("result") or data.get("response") or data.get("reply") or str(data)
        print("Resulting ai_text inside generate_ai_text:", ai_text)
        return ai_text.strip().replace('"', '')
    except Exception as e:
        print("API error:", e)
        return "fallback"

# Let's run a check
mapped_fields = extract_form_fields(FORM_URL)
print("\n--- Mapped Fields ---")
for lbl, entry in mapped_fields.items():
    print(f"'{lbl}': '{entry}'")

students = load_students_from_csv(CSV_FILE_PATH)
student = students[0]
nama = student['nama']
nim = student['nim']
prefix_tahun = str(nim)[:2]
angkatan = f"20{prefix_tahun}"
email_prefix = nama.lower().replace(' ', '')
email = f"{email_prefix}{prefix_tahun}@gmail.com"

print("\n--- Student Info ---")
print(f"Nama: {nama}, NIM: {nim}, Angkatan: {angkatan}, Email: {email}")

generate_ai_text("pendapat")

# Simulate payload creation
payload = {}
has_manual_email = False
for label, entry_id in mapped_fields.items():
    lbl_lower = label.lower()
    if "nama" in lbl_lower:
        payload[entry_id] = nama
    elif "nim" in lbl_lower:
        payload[entry_id] = nim
    elif "angkatan" in lbl_lower:
        payload[entry_id] = angkatan
    elif "pendapat" in lbl_lower:
        payload[entry_id] = "TEST PENDAPAT"
    elif "saran" in lbl_lower:
        payload[entry_id] = "TEST SARAN"
    elif "email" in lbl_lower:
        payload[entry_id] = email
        has_manual_email = True
    else:
        payload[entry_id] = generate_scale_answer()

if not has_manual_email:
    payload["emailAddress"] = email

print("\n--- Generated Payload ---")
print(json.dumps(payload, indent=2))
