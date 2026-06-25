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


# Set untuk menyimpan ulasan/saran yang sudah digunakan agar tidak terjadi duplikat
used_pendapat = set()
used_saran = set()

def generate_dynamic_fallback_pendapat():
    part1 = [
        "Secara keseluruhan, website E-Surat FT",
        "Layanan e-surat Unmul ini",
        "Sistem surat digital fakultas",
        "Website E-Surat 2 FT",
        "Menurut saya, aplikasi e-surat ini",
        "Fitur pengajuan surat digital ini",
        "Proses pengurusan surat lewat web ini",
    ]
    part2 = [
        "sudah sangat membantu mahasiswa,",
        "cukup praktis dan efisien untuk digunakan,",
        "memiliki antarmuka yang mudah dipahami,",
        "sangat mempermudah alur administrasi,",
        "cukup responsif saat diakses dari HP,",
        "menawarkan proses yang lebih cepat,",
        "cukup memotong birokrasi manual,"
    ]
    part3 = [
        "sehingga tidak perlu mengantre lama di loket.",
        "membuat pengajuan berkas jadi lebih ringkas.",
        "serta sangat menghemat waktu mahasiswa.",
        "meskipun tampilannya masih perlu sedikit adaptasi.",
        "karena fiturnya langsung tepat sasaran.",
        "sehingga prosesnya transparan dari awal sampai akhir.",
        "dan memudahkan pemantauan dokumen dari mana saja."
    ]
    
    p1 = random.choice(part1)
    p2 = random.choice(part2)
    p3 = random.choice(part3)
    
    direct = [
        "Sistemnya sangat membantu mahasiswa dalam mengurus persuratan tanpa harus ke kampus.",
        "Tampilan web cukup bersih dan alur pengajuannya mudah dipahami bagi pengguna baru.",
        "Proses pengajuan surat jadi lebih praktis dan tidak memakan waktu lama.",
        "Akses website cukup lancar dan responsif saat dibuka menggunakan smartphone.",
        "Instruksi pengisian form sudah cukup jelas sehingga meminimalisir kesalahan data.",
        "Fitur yang disediakan sudah sangat fungsional untuk kebutuhan administrasi mahasiswa.",
        "Secara umum, website ini mempermudah urusan administrasi persuratan mahasiswa.",
        "Sangat menghemat waktu karena seluruh prosesnya dilakukan secara digital."
    ]
    
    if random.random() < 0.5:
        return f"{p1} {p2} {p3}"
    else:
        return random.choice(direct)

def generate_dynamic_fallback_saran():
    part1 = [
        "Mungkin kedepannya",
        "Alangkah baiknya jika",
        "Saran saya,",
        "Sebagai saran perbaikan,",
        "Untuk pengembangan selanjutnya,",
        "Harapannya,"
    ]
    part2 = [
        "kecepatan loading website bisa lebih dioptimalkan",
        "tampilan tata letak menu dibuat lebih ringkas dan simpel",
        "ditambahin notifikasi status surat via email",
        "panduan atau petunjuk pengisian di halaman utama lebih diperjelas",
        "desain antarmuka pengguna dibuat lebih modern",
        "keamanan data saat unggah dokumen lebih ditingkatkan",
        "tampilan versi mobile dibuat lebih ramah pengguna",
        "disediakan kolom FAQ untuk kendala teknis"
    ]
    part3 = [
        "agar mahasiswa tidak menunggu lama saat mengakses.",
        "supaya navigasi pencarian menu surat lebih cepat.",
        "agar mahasiswa bisa memantau proses tanpa harus terus login.",
        "khususnya bagi mahasiswa baru yang pertama kali menggunakan.",
        "agar terkesan lebih menarik dan kekinian.",
        "demi kenyamanan bersama dalam bertransaksi data.",
        "sehingga nyaman saat diakses melalui smartphone.",
        "untuk membantu mahasiswa yang mengalami kesulitan input."
    ]
    
    p1 = random.choice(part1)
    p2 = random.choice(part2)
    p3 = random.choice(part3)
    
    direct = [
        "Mohon kecepatan akses website ditingkatkan terutama saat jam sibuk pengisian.",
        "Sebaiknya ditambahkan fitur tracking status surat yang lebih detail agar mudah dipantau.",
        "Tampilan navigasi menu mungkin bisa dibuat lebih sederhana lagi agar mudah dipahami.",
        "Disarankan untuk mengoptimalkan tampilan mobile agar lebih responsif di berbagai perangkat.",
        "Mungkin bisa ditambahkan panduan singkat atau petunjuk pengisian di setiap formulir.",
        "Kecepatan respon website saat mengunggah lampiran dokumen perlu sedikit diperbaiki.",
        "Harapannya ada integrasi notifikasi otomatis agar mahasiswa tahu jika surat sudah selesai diproses.",
        "Desain halaman utama bisa dibuat lebih modern agar terlihat lebih profesional."
    ]
    
    if random.random() < 0.5:
        return f"{p1} {p2} {p3}"
    else:
        return random.choice(direct)

def generate_varied_email(nama, nim):
    # Bersihkan nama dari spasi ganda, karakter aneh, dsb.
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', nama).lower()
    parts = [p for p in clean_name.split() if p]
    if not parts:
        parts = ["user"]
        
    prefix_tahun = str(nim)[:2] if nim else str(random.randint(15, 25))
    
    # Nickname keywords/elements
    game_prefixes = ["shadow", "neon", "vortex", "cyber", "hyper", "zen", "el", "king", "lord", "pro", "racer", "hunter", "toxic", "phantom", "alpha", "omega", "silent", "dark", "frost"]
    game_suffixes = ["gg", "pro", "gaming", "ml", "ff", "pubg", "boy", "girl", "xd", "god", "z", "xz", "99", "88", "123", "404", "lol"]
    
    email_types = [
        # 1. Standard name variation (e.g. rian.mhd24, mhd_rian)
        lambda: f"{'.'.join(parts)}{prefix_tahun}",
        lambda: f"{'_'.join(parts)}{random.choice(['', prefix_tahun])}",
        lambda: f"{parts[-1]}.{parts[0]}{prefix_tahun}",
        # 2. Nickname style prefix (e.g. shadow.rian, neon_rian24)
        lambda: f"{random.choice(game_prefixes)}{random.choice(['.', '_'])}{parts[0]}{random.choice(['', prefix_tahun])}",
        # 3. Nickname style suffix (e.g. rian_gaming, rian_ml99)
        lambda: f"{parts[0]}{random.choice(['.', '_'])}{random.choice(game_suffixes)}",
        # 4. Mix of both (e.g. shadow_rian_gg)
        lambda: f"{random.choice(game_prefixes)}_{parts[0]}_{random.choice(game_suffixes)}",
        # 5. Cool abbreviations (e.g. mr24_gaming, etc.)
        lambda: f"{''.join([p[0] for p in parts])}{prefix_tahun}_{random.choice(game_suffixes)}",
        # 6. Random gamer style tag
        lambda: f"{parts[0]}{random.choice(['x', 'z', '_tzy', '_sanz', '_sky'])}{random.choice(['', prefix_tahun])}"
    ]
    
    email_prefix = random.choice(email_types)()
    email_prefix = re.sub(r'[._]{2,}', '_', email_prefix)
    email_prefix = email_prefix.strip('._')
    
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "ymail.com"]
    domain = random.choice(domains)
    
    return f"{email_prefix}@{domain}"

# Fungsi untuk memanggil API GPT untuk mendapatkan ulasan/saran
def generate_ai_text(prompt_type, max_retries=5):
    # Kumpulan aspek acak agar jawaban bervariasi dan tidak template
    aspek_list = [
        "kemudahan mencari menu surat",
        "kecepatan loading atau respon website",
        "tampilan visual yang rapi dan modern",
        "kejelasan instruksi pengisian form",
        "proses pengajuan surat yang praktis",
        "aksesibilitas saat dibuka di handphone",
        "kenyamanan antarmuka pengguna",
    ]
    
    target_set = used_pendapat if prompt_type == "pendapat" else used_saran
    
    for attempt in range(max_retries):
        aspek = random.choice(aspek_list)
        
        if prompt_type == "pendapat":
            prompt = (
                "Kamu adalah mahasiswa Universitas Mulawarman. "
                "Tuliskan 1 kalimat ulasan/pendapat singkat yang santai namun tetap sopan dan wajar (semi-formal/standar mahasiswa) "
                "tentang kegunaan website 'E-Surat 2 FT Unmul'. "
                f"Fokuskan ulasan pada aspek: {aspek}. "
                "Hindari bahasa yang terlalu formal/kaku, namun JANGAN menggunakan kata slang/alay yang berlebihan (seperti 'sat set', 'no debat', 'gacor', 'gokil', 'parah', dll). "
                "Hindari awalan monoton seperti 'Website ini...', 'Menurut saya...'. "
                "Pastikan kalimatnya unik, orisinal, dan bervariasi. "
                "Tuliskan teks polos saja, TANPA tanda bintang (*), tebal, miring, atau format markdown lainnya."
            )
        else:  # saran
            prompt = (
                "Kamu adalah mahasiswa Universitas Mulawarman. "
                "Tuliskan 1 kalimat saran perbaikan yang singkat, membangun, dan menggunakan gaya bahasa mahasiswa yang santai namun sopan (semi-formal) "
                "untuk website 'E-Surat 2 FT Unmul' ke depannya. "
                f"Fokuskan saran pada aspek: {aspek}. "
                "Hindari bahasa yang terlalu formal/kaku, namun JANGAN menggunakan kata slang/alay yang berlebihan (seperti 'sat set', 'biar ga lemot', dll). "
                "Hindari kata pembuka kaku seperti 'Saran saya...', 'Sebaiknya...', 'Diharapkan...'. "
                "Pastikan kalimatnya unik, orisinal, dan bervariasi. "
                "Tuliskan teks polos saja, TANPA tanda bintang (*), tebal, miring, atau format markdown lainnya."
            )
            
        try:
            response = requests.get(AI_API_URL, params={"text": prompt}, timeout=15)
            if response.status_code == 200:
                data = response.json()
                ai_text = data.get("text") or data.get("result") or data.get("response") or data.get("reply") or str(data)
                ai_text = ai_text.strip().replace('"', '').replace('\u2011', '-')
                ai_text = re.sub(r'[*_#`~]', '', ai_text)
                ai_text = ai_text.strip()
                
                if ai_text and ai_text not in target_set:
                    target_set.add(ai_text)
                    return ai_text
            else:
                pass
        except Exception:
            pass
            
    # Fallback jika API gagal/hasilnya duplikat terus menerus
    for _ in range(20):
        if prompt_type == "pendapat":
            val = generate_dynamic_fallback_pendapat()
        else:
            val = generate_dynamic_fallback_saran()
            
        if val not in target_set:
            target_set.add(val)
            return val
            
    # Absolute fallback
    val = (generate_dynamic_fallback_pendapat() if prompt_type == "pendapat" else generate_dynamic_fallback_saran()) + f" {random.randint(10, 99)}"
    target_set.add(val)
    return val


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
            
        # Format email fiktif bervariasi (nickname game, inisial, dll)
        email = generate_varied_email(nama, nim)
        
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