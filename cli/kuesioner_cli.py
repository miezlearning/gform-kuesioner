import time
import random
import sys
import os
from typing import Dict, Any
import argparse

# Menambahkan parent directory ke sys.path secara dinamis agar bisa
# mengimpor modul dari package 'src' yang berada di luar folder 'cli'.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    CSV_FILE_PATH,
    FORM_URL,
    TARGET_SUBMISSIONS,
    SUBMISSION_DELAY_MIN,
    SUBMISSION_DELAY_MAX
)
from src.csv_helper import load_students_from_csv
from src.form_handler import GoogleFormHandler
from src.generators import (
    format_natural_name,
    generate_varied_email,
    generate_scale_answer
)
from src.ai_handler import AITextGenerator

# Pastikan output terminal mendukung UTF-8 agar tidak terjadi crash encoding pada Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def generate_field_value(
    field: Dict[str, Any], 
    nama: str, 
    nim: str, 
    angkatan: str, 
    pendapat: str, 
    saran: str, 
    email: str, 
    profile: str
) -> str:
    """Menentukan nilai untuk setiap field berdasarkan label dan tipe pertanyaan."""
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
        # Pertanyaan skala rating (Type 5 = linear scale, Type 2 = radio)
        return generate_scale_answer(profile)


def run_auto_fill_cli(args):
    """Fungsi utama pengisian otomatis yang menggunakan parameter input dari CLI."""
    # 1. Inisialisasi handler Form & generator teks AI
    form_handler = GoogleFormHandler(args.url)
    ai_generator = AITextGenerator()

    # 2. Ekstrak struktur lengkap Google Form
    form_data = form_handler.extract_structure()
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
        return

    # 3. Load data mahasiswa dari file CSV yang ditentukan CLI
    all_students = load_students_from_csv(args.csv)
    if not all_students:
        print("Proses dihentikan karena data mahasiswa kosong.")
        return
        
    print(f"Berhasil memuat {len(all_students)} data mahasiswa dari database CSV.")
    
    # Menentukan jumlah responden secara acak
    num_to_select = min(args.target, len(all_students))
    selected_students = random.sample(all_students, num_to_select)
    print(f"Memulai proses pengisian otomatis untuk {num_to_select} mahasiswa terpilih...\n")
    
    # 4. Loop pengisian untuk setiap mahasiswa terpilih
    for index, student in enumerate(selected_students):
        nama_raw = student['nama']
        nama = format_natural_name(nama_raw)
        nim = student['nim']
        
        # Tentukan profil kepuasan responden secara acak agar nilai skala bervariasi secara natural
        profile = random.choices(
            ["sangat_puas", "puas_rata_rata", "kritis"],
            weights=[35, 55, 10]
        )[0]
        
        # Deteksi angkatan secara dinamis dari NIM (2 digit pertama)
        try:
            prefix_tahun = str(nim)[:2]
            angkatan = f"20{prefix_tahun}"
        except Exception:
            angkatan = "2021"
            
        # Format email fiktif dan dapatkan pendapat/saran dari AI
        email = generate_varied_email(nama, nim)
        pendapat = ai_generator.generate_text("pendapat")
        saran = ai_generator.generate_text("saran")
        
        # ============================================================
        # STEP 1: Generate nilai jawaban untuk seluruh halaman form
        # ============================================================
        all_page_values = []
        for page in pages:
            page_values = []
            for field in page:
                value = generate_field_value(field, nama, nim, angkatan, pendapat, saran, email, profile)
                page_values.append({
                    "entry_id": field["entry_id"],
                    "value": value,
                    "label": field["label"]
                })
            all_page_values.append(page_values)
        
        # ============================================================
        # STEP 2: Bangun parameter partialResponse dari halaman 1 s/d N-1
        # ============================================================
        partial_entries = []
        for page_values in all_page_values[:-1]:
            for field_val in page_values:
                partial_entries.append((field_val["entry_id"], field_val["value"]))
        
        partial_response_json = form_handler.build_partial_response(partial_entries, fbzx, email)
        
        # ============================================================
        # STEP 3: Bangun top-level payload dari halaman TERAKHIR
        # ============================================================
        last_page = all_page_values[-1]
        payload = {}
        for field_val in last_page:
            entry_key = f"entry.{field_val['entry_id']}"
            payload[entry_key] = field_val["value"]
            
            # Google Forms memerlukan marker field kosong untuk pertanyaan bertipe linear scale (Type 5)
            for field in pages[-1]:
                if field["entry_id"] == field_val["entry_id"] and field["type"] == 5:
                    payload[f"{entry_key}_sentinel"] = ""
                    break
        
        # Tambahkan parameter session, token, dan riwayat halaman
        payload["fvv"] = fvv
        payload["partialResponse"] = partial_response_json
        payload["pageHistory"] = page_history
        payload["fbzx"] = fbzx
        payload["submissionTimestamp"] = str(int(time.time() * 1000))
        
        # Jika form meminta input email bawaan di halaman awal
        if has_email_page:
            payload["emailAddress"] = email
            
        # 5. Kirim payload respon kuesioner ke Google Form
        success, message = form_handler.submit(payload, referer_url=form_handler.submit_url)
        
        status_symbol = "✓" if success else "✗"
        print(f"[{index+1}/{num_to_select}] {status_symbol} {message}: {nama} ({nim} - {angkatan})")
        print(f"    > Pendapat: {pendapat}")
        print(f"    > Saran   : {saran}\n")
            
        # Jeda pengiriman acak untuk menghindari rate-limiting/deteksi bot
        if index < num_to_select - 1:
            delay = random.randint(args.min_delay, args.max_delay)
            time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="Script Pengisi Kuesioner Google Form Otomatis berbasis CLI."
    )
    parser.add_argument(
        "-u", "--url", 
        type=str, 
        default=FORM_URL,
        help=f"URL Google Form (default: {FORM_URL})"
    )
    parser.add_argument(
        "-c", "--csv", 
        type=str, 
        default=CSV_FILE_PATH,
        help=f"Path ke database CSV mahasiswa (default: {CSV_FILE_PATH})"
    )
    parser.add_argument(
        "-t", "--target", 
        type=int, 
        default=TARGET_SUBMISSIONS,
        help=f"Target jumlah pengisian kuesioner (default: {TARGET_SUBMISSIONS})"
    )
    parser.add_argument(
        "-dmin", "--min-delay", 
        type=int, 
        default=SUBMISSION_DELAY_MIN,
        help=f"Waktu tunggu minimum (detik) antar pengisian (default: {SUBMISSION_DELAY_MIN})"
    )
    parser.add_argument(
        "-dmax", "--max-delay", 
        type=int, 
        default=SUBMISSION_DELAY_MAX,
        help=f"Waktu tunggu maksimum (detik) antar pengisian (default: {SUBMISSION_DELAY_MAX})"
    )
    
    args = parser.parse_args()
    
    # Validasi input sederhana
    if args.min_delay < 0 or args.max_delay < 0:
        print("Error: Delay tidak boleh bernilai negatif.")
        sys.exit(1)
    if args.min_delay > args.max_delay:
        print("Error: Jeda minimum tidak boleh lebih besar dari jeda maksimum.")
        sys.exit(1)
    if args.target <= 0:
        print("Error: Target pengisian harus lebih besar dari 0.")
        sys.exit(1)

    print("=" * 60)
    print("           KUESIONER AUTO CLI RUNNER")
    print("=" * 60)
    print(f"Target   : {args.target} pengisian")
    print(f"CSV Path : {args.csv}")
    print(f"Gform URL: {args.url}")
    print(f"Delay    : {args.min_delay} - {args.max_delay} detik")
    print("=" * 60)
    
    run_auto_fill_cli(args)


if __name__ == "__main__":
    main()
