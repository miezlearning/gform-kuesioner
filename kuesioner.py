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


def extract_form_structure(form_url):
    """
    Mengekstrak struktur lengkap Google Form termasuk:
    - Pertanyaan per halaman (page) beserta entry ID-nya
    - Data session (fbzx, fvv)
    - Mendeteksi apakah ada halaman email bawaan Google
    
    Google Forms multi-page mengirim data dengan format khusus:
    - Halaman-halaman SEBELUM halaman terakhir -> dikirim via parameter 'partialResponse' (JSON)
    - Halaman TERAKHIR -> dikirim sebagai top-level entry.XXXX fields biasa
    """
    print("Sedang mengambil struktur Google Form secara otomatis...")
    try:
        response = requests.get(form_url, timeout=15)
        if response.status_code != 200:
            print(f"Gagal memuat form. Kode Status: {response.status_code}")
            return None
            
        html = response.text
        match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
        if not match:
            print("Gagal menemukan struktur data form. Pastikan link gform Anda benar.")
            return None
            
        raw_data = json.loads(match.group(1))
        questions_list = raw_data[1][1]
        
        # Kelompokkan pertanyaan per halaman (page)
        # type_code 8 = Section Header (page break)
        pages = []
        current_page_fields = []
        
        for item in questions_list:
            try:
                type_code = item[3]
                if type_code == 8:
                    # Section header = mulai halaman baru
                    # Simpan halaman sebelumnya (jika ada field)
                    if current_page_fields:
                        pages.append(current_page_fields)
                    current_page_fields = []
                else:
                    label = item[1].strip()
                    entry_id = item[4][0][0]  # Numeric ID tanpa prefix "entry."
                    current_page_fields.append({
                        "label": label,
                        "entry_id": entry_id,
                        "type": type_code  # 0=text, 1=textarea, 2=radio, 5=scale
                    })
            except (IndexError, TypeError):
                continue
        
        # Jangan lupa simpan halaman terakhir
        if current_page_fields:
            pages.append(current_page_fields)
        
        # Ekstrak data session (fbzx, fvv)
        soup = BeautifulSoup(html, "html.parser")
        
        fbzx_input = soup.find("input", {"name": "fbzx"})
        fbzx = fbzx_input.get("value") if fbzx_input else ""
        
        fvv_input = soup.find("input", {"name": "fvv"})
        fvv = fvv_input.get("value") if fvv_input else "1"
        
        # Deteksi halaman email bawaan Google
        # CATATAN: requests.get() hanya mengambil HTML statis (tanpa JS rendering),
        # sehingga input emailAddress TIDAK akan ditemukan di HTML.
        # Cara yang benar: deteksi dari FB_PUBLIC_LOAD_DATA_ metadata.
        # raw_data[1][10][3] != None menandakan email collection aktif.
        has_email_page = False
        try:
            email_setting = raw_data[1][10][3]
            has_email_page = email_setting is not None and email_setting > 0
        except (IndexError, TypeError):
            # Fallback: cek HTML (mungkin berhasil di beberapa versi form)
            has_email_page = soup.find("input", {"name": "emailAddress"}) is not None
        
        # Hitung total halaman (termasuk halaman email jika ada)
        num_pages = len(pages)
        if has_email_page:
            num_pages += 1  # Halaman email dihitung sebagai Page 0
            
        page_history = ",".join(str(i) for i in range(num_pages))
        
        # Print struktur untuk debugging
        total_fields = sum(len(p) for p in pages)
        print(f"Berhasil mendeteksi {total_fields} pertanyaan dalam {len(pages)} halaman.")
        if has_email_page:
            print(f"  Page 0: Email (bawaan Google Forms)")
        for pi, page in enumerate(pages):
            page_num = pi + 1 if has_email_page else pi
            print(f"  Page {page_num}: {len(page)} pertanyaan")
            for field in page:
                print(f"    - entry.{field['entry_id']} -> '{field['label']}' (type={field['type']})")
        print("-" * 50)
        
        return {
            "pages": pages,
            "fbzx": fbzx,
            "fvv": fvv,
            "has_email_page": has_email_page,
            "page_history": page_history,
        }
        
    except Exception as e:
        print(f"Terjadi error saat ekstraksi struktur form: {e}")
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


def generate_field_value(field, nama, nim, angkatan, pendapat, saran, email):
    """
    Menentukan nilai untuk setiap field berdasarkan label dan tipe pertanyaan.
    """
    lbl_lower = field["label"].lower()
    
    if "nama" in lbl_lower:
        return nama
    elif "nim" in lbl_lower:
        return nim
    elif "angkatan" in lbl_lower:
        return angkatan
    elif "pendapat" in lbl_lower:
        return pendapat
    elif "saran" in lbl_lower:
        return saran
    elif "email" in lbl_lower:
        return email
    else:
        # Pertanyaan skala (Type 5 = linear scale, Type 2 = radio)
        return generate_scale_answer()


def build_partial_response(pages_data, fbzx, email):
    """
    Membangun parameter 'partialResponse' untuk Google Forms multi-page.
    
    Format partialResponse (JSON string):
    [
      [
        [null, entryId1, ["value1"], 0],
        [null, entryId2, ["value2"], 0],
        ...
      ],
      null,
      "fbzx_value",
      null,
      null,
      null,
      "email@address.com",
      1
    ]
    
    pages_data = list of (entry_id, value) tuples untuk semua halaman SEBELUM halaman terakhir
    """
    entries = []
    for entry_id, value in pages_data:
        entries.append([None, entry_id, [str(value)], 0])
    
    partial = [
        entries,
        None,
        fbzx,
        None,
        None,
        None,
        email,
        1
    ]
    
    return json.dumps(partial, separators=(',', ':'))


# Fungsi utama proses pengisian otomatis
def run_auto_fill():
    # 1. Ekstrak struktur lengkap Google Form
    form_data = extract_form_structure(FORM_URL)
    if not form_data:
        print("Ekstraksi struktur form gagal. Proses dihentikan.")
        return
    
    pages = form_data["pages"]
    fbzx = form_data["fbzx"]
    fvv = form_data["fvv"]
    has_email_page = form_data["has_email_page"]
    page_history = form_data["page_history"]
    
    if len(pages) < 2:
        print("Form hanya memiliki 1 halaman. Menggunakan mode submit biasa.")
        # Fallback untuk form 1 halaman (tanpa partialResponse)
        # ... (tidak diperlukan untuk form ini)
        return

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
        
        # ============================================================
        # STEP 1: Generate values untuk SEMUA halaman
        # ============================================================
        all_page_values = []  # List of lists: [[{entry_id, value}, ...], ...]
        
        for page in pages:
            page_values = []
            for field in page:
                value = generate_field_value(field, nama, nim, angkatan, pendapat, saran, email)
                page_values.append({
                    "entry_id": field["entry_id"],
                    "value": value,
                    "label": field["label"]
                })
            all_page_values.append(page_values)
        
        # ============================================================
        # STEP 2: Build partialResponse dari halaman 1 s/d N-1
        #         (semua halaman KECUALI halaman terakhir)
        # ============================================================
        partial_entries = []
        for page_values in all_page_values[:-1]:  # Semua halaman kecuali terakhir
            for field_val in page_values:
                partial_entries.append((field_val["entry_id"], field_val["value"]))
        
        partial_response_json = build_partial_response(partial_entries, fbzx, email)
        
        # ============================================================
        # STEP 3: Build top-level payload dari halaman TERAKHIR saja
        # ============================================================
        last_page = all_page_values[-1]
        
        payload = {}
        for field_val in last_page:
            entry_key = f"entry.{field_val['entry_id']}"
            payload[entry_key] = field_val["value"]
            
            # Untuk pertanyaan tipe scale (Type 5), Google Forms juga mengirim sentinel field
            # Sentinel field dikirim dengan value kosong sebagai marker
            # Cari type dari field asli di pages
            for field in pages[-1]:
                if field["entry_id"] == field_val["entry_id"] and field["type"] == 5:
                    payload[f"{entry_key}_sentinel"] = ""
                    break
        
        # Tambahkan parameter session dan partialResponse
        payload["fvv"] = fvv
        payload["partialResponse"] = partial_response_json
        payload["pageHistory"] = page_history
        payload["fbzx"] = fbzx
        payload["submissionTimestamp"] = str(int(time.time() * 1000))
        
        # Jika gform menggunakan email bawaan
        if has_email_page:
            payload["emailAddress"] = email
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://docs.google.com",
            "Referer": f"{FORM_URL.replace('/viewform', '/formResponse')}",
        }
        
        try:
            response = requests.post(submit_url, data=payload, headers=headers)
            if response.status_code == 200:
                # Verifikasi bahwa respon benar-benar berhasil (bukan error page)
                success = "freebirdFormviewerViewResponseConfirmationMessage" in response.text or \
                          "Jawaban Anda telah direkam" in response.text
                if success:
                    print(f"[{index+1}/{num_to_select}] ✓ Sukses mengirim respon: {nama} ({nim} - {angkatan})")
                else:
                    print(f"[{index+1}/{num_to_select}] ⚠ Dikirim tapi mungkin ada validasi error: {nama}")
                print(f"    > Pendapat: {pendapat}")
                print(f"    > Saran   : {saran}\n")
            else:
                print(f"[{index+1}/{num_to_select}] ✗ Gagal mengirim untuk {nama}. Kode Status: {response.status_code}\n")
        except Exception as e:
            print(f"[{index+1}/{num_to_select}] ✗ Error saat mengirim data {nama}: {e}\n")
            
        # Jeda pengiriman acak (3-7 detik)
        time.sleep(random.randint(3, 7))

if __name__ == "__main__":
    run_auto_fill()