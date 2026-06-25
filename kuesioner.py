import csv
import json
import re
import random
import time
import sys
import requests
from bs4 import BeautifulSoup

# Pastikan output terminal mendukung UTF-8 agar tidak terjadi crash encoding pada Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ==================== CONFIGURATION ====================
# 1. Nama file CSV database Anda
CSV_FILE_PATH = "dataset/2024.csv"

# 2. URL Google Form Anda
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform"

# 3. URL API GPT yang Anda berikan
AI_API_URL = "https://apis.prexzyvilla.site/ai/gpt-5"

# 4. Target jumlah pengisian kuesioner yang Anda inginkan kali ini
TARGET_SUBMISSIONS = 5 
# =======================================================


# Fungsi untuk mengekstrak ID pertanyaan (entry.XXXXX) secara otomatis dari Google Form
def extract_form_fields(form_url):
    print("Sedang mengambil struktur Google Form secara otomatis...")
    try:
        response = requests.get(form_url, timeout=15)
        if response.status_code != 200:
            print(f"Gagal memuat form. Kode Status: {response.status_code}")
            return None
            
        html = response.text
        # Mencari data skeleton google form di dalam tag script
        match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
        if not match:
            print("Gagal menemukan struktur data form. Pastikan link gform Anda benar.")
            return None
            
        raw_data = json.loads(match.group(1))
        questions_list = raw_data[1][1]
        
        mapped_fields = {}
        for item in questions_list:
            try:
                # item[1] adalah label/teks pertanyaan
                label = item[1].strip()
                # item[4][0][0] adalah ID input uniknya (angka entry)
                entry_id = f"entry.{item[4][0][0]}"
                mapped_fields[label] = entry_id
            except (IndexError, TypeError):
                continue
                
        # Ekstrak data session (fbzx, fvv, pageHistory) untuk validasi form
        soup = BeautifulSoup(html, "html.parser")
        
        fbzx_input = soup.find("input", {"name": "fbzx"})
        fbzx = fbzx_input.get("value") if fbzx_input else ""
        
        fvv_input = soup.find("input", {"name": "fvv"})
        fvv = fvv_input.get("value") if fvv_input else "1"
        
        # Hitung jumlah halaman secara dinamis dari section break (type code 8)
        num_pages = 0
        for item in questions_list:
            try:
                if item[3] == 8:
                    num_pages += 1
            except (IndexError, TypeError):
                continue
        if num_pages == 0:
            num_pages = 1
            
        # Cek apakah Google Form mengaktifkan pengumpulan email bawaan (Responder Input)
        # Jika ya, halaman pengisian email dipisahkan di paling awal (Halaman 0),
        # sehingga jumlah total halaman bertambah 1.
        has_email_page = soup.find("input", {"name": "emailAddress"}) is not None
        if has_email_page:
            num_pages += 1
            
        pageHistory = ",".join(str(i) for i in range(num_pages))
        
        session_data = {
            "fbzx": fbzx,
            "fvv": fvv,
            "pageHistory": pageHistory
        }
                
        print(f"Berhasil mendeteksi {len(mapped_fields)} pertanyaan dari Google Form.")
        for label, entry in mapped_fields.items():
            print(f"  - '{label}' -> {entry}")
        print("-" * 50)
        return mapped_fields, session_data
        
    except Exception as e:
        print(f"Terjadi error saat ekstraksi ID form: {e}")
        return None


# Fungsi untuk membaca data dari CSV
def load_students_from_csv(file_path):
    students = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            sample = file.read(2048)
            file.seek(0)
            delimiter = ';' if ';' in sample else ','
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row in reader:
                clean_row = {key.strip().lower(): val.strip() for key, val in row.items() if key}
                if 'nim' in clean_row and 'nama' in clean_row:
                    students.append({
                        "nim": clean_row['nim'],
                        "nama": clean_row['nama']
                    })
        return students
    except FileNotFoundError:
        print(f"Error: File '{file_path}' tidak ditemukan.")
        return []
    except Exception as e:
        print(f"Terjadi kesalahan saat membaca CSV: {e}")
        return []


# Fungsi menghasilkan nilai acak skala WebQual (1 sampai 5)
def generate_scale_answer():
    return str(random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 48, 30])[0])


# Fungsi untuk memanggil API GPT untuk mendapatkan ulasan/saran
def generate_ai_text(prompt_type):
    if prompt_type == "pendapat":
        prompt = (
            "Kamu adalah mahasiswa teknik informatika Universitas Mulawarman. "
            "Tuliskan 1 kalimat ulasan/pendapat singkat dan santai (dalam Bahasa Indonesia) "
            "tentang kegunaan website 'E-Surat 2 FT Unmul'. "
            "Berikan ulasan yang positif tapi realistis. Jangan gunakan emoji dan jangan terlalu formal."
        )
    else:  # saran
        prompt = (
            "Kamu adalah mahasiswa teknik informatika Universitas Mulawarman. "
            "Tuliskan 1 kalimat saran perbaikan yang singkat, logis, dan membangun (dalam Bahasa Indonesia) "
            "untuk website 'E-Surat 2 FT Unmul' ke depannya. Jangan gunakan emoji."
        )
        
    try:
        response = requests.get(AI_API_URL, params={"text": prompt}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            ai_text = data.get("text") or data.get("result") or data.get("response") or data.get("reply") or str(data)
            return ai_text.strip().replace('"', '').replace('\u2011', '-')
        else:
            raise Exception(f"API Error Status: {response.status_code}")
    except Exception as e:
        if prompt_type == "pendapat":
            return "Secara umum penggunaan website E-Surat ini cukup membantu urusan administrasi mahasiswa."
        else:
            return "Saran saya adalah meningkatkan kecepatan respon web agar tidak lambat saat diakses."


# Fungsi utama proses pengisian otomatis
def run_auto_fill():
    # 1. Ekstrak mapping pertanyaan dari Google Form secara otomatis
    result = extract_form_fields(FORM_URL)
    if not result:
        print("Ekstraksi ID form gagal. Proses dihentikan.")
        return
    mapped_fields, session_data = result

    # 2. Load data mahasiswa dari CSV
    all_students = load_students_from_csv(CSV_FILE_PATH)
    if not all_students:
        print("Proses dihentikan karena data mahasiswa kosong.")
        return
        
    print(f"Berhasil memuat {len(all_students)} data mahasiswa dari database CSV.")
    
    # Menentukan jumlah responden yang diambil acak
    num_to_select = min(TARGET_SUBMISSIONS, len(all_students))
    selected_students = random.sample(all_students, num_to_select)
    print(f"Memulai proses pengisian otomatis untuk {num_to_select} mahasiswa terpilih...\n")
    
    # Ubah URL dari viewform ke formResponse untuk pengiriman data
    submit_url = FORM_URL.replace("/viewform", "/formResponse")
    
    for index, student in enumerate(selected_students):
        nama = student['nama']
        nim = student['nim']
        
        # Deteksi angkatan secara dinamis dari NIM (ambil 2 digit pertama)
        try:
            prefix_tahun = str(nim)[:2]
            angkatan = f"20{prefix_tahun}"
        except Exception:
            angkatan = "2021"
            
        # Format email fiktif
        email_prefix = nama.lower().replace(' ', '')
        email = f"{email_prefix}{prefix_tahun}@gmail.com"
        
        # Ambil respon dari API GPT
        pendapat = generate_ai_text("pendapat")
        saran = generate_ai_text("saran")
        
        # Susun payload data dinamis berdasarkan hasil ekstrak otomatis
        payload = {}
        payload.update(session_data)
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
                payload[entry_id] = pendapat
            elif "saran" in lbl_lower:
                payload[entry_id] = saran
            elif "email" in lbl_lower:
                payload[entry_id] = email
                has_manual_email = True
            else:
                # Jika tidak cocok dengan kriteria di atas, diasumsikan sebagai pertanyaan skala (1-5)
                payload[entry_id] = generate_scale_answer()
                
        # Jika gform menggunakan sistem pengumpulan email bawaan (bukan pertanyaan teks biasa)
        if not has_manual_email:
            payload["emailAddress"] = email
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.post(submit_url, data=payload, headers=headers)
            if response.status_code == 200:
                print(f"[{index+1}/{num_to_select}] Sukses mengirim respon: {nama} ({nim} - {angkatan})")
                print(f"    > Pendapat: {pendapat}")
                print(f"    > Saran   : {saran}\n")
            else:
                print(f"[{index+1}/{num_to_select}] Gagal mengirim untuk {nama}. Kode Status: {response.status_code}\n")
        except Exception as e:
            print(f"[{index+1}/{num_to_select}] Error saat mengirim data {nama}: {e}\n")
            
        # Jeda pengiriman acak (3-7 detik)
        time.sleep(random.randint(3, 7))

if __name__ == "__main__":
    run_auto_fill()