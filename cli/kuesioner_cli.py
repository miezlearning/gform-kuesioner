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
from src.answer_resolver import AnswerResolver
from src.ai_handler import AITextGenerator
from src.generators import format_natural_name, generate_varied_email

# Pastikan output terminal mendukung UTF-8 agar tidak terjadi crash encoding pada Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def run_auto_fill_cli(args):
    """Fungsi utama pengisian otomatis yang menggunakan parameter input dari CLI."""
    # 1. Inisialisasi handler Form & generator teks AI
    form_handler = GoogleFormHandler(args.url)
    ai_generator = AITextGenerator()
    resolver = AnswerResolver(ai_generator)

    # 2. Ekstrak struktur lengkap Google Form
    form_data = form_handler.extract_structure()
    if not form_data:
        print("Ekstraksi struktur form gagal. Periksa link form atau koneksi internet Anda.")
        return
    
    pages = form_data["pages"]
    fbzx = form_data["fbzx"]
    fvv = form_data["fvv"]
    has_email_page = form_data["has_email_page"]
    page_history = form_data["page_history"]
    form_title = form_data.get("form_title", "Google Form")
    
    print(f"Berhasil membaca form: '{form_title}'")
    print(f"Total Halaman : {len(pages)}")
    print(f"Total Pertanyaan: {len(form_data.get('questions', []))}\n")

    # 3. Load data mahasiswa dari file CSV yang ditentukan CLI
    all_students = load_students_from_csv(args.csv)
    if not all_students:
        print("Proses dihentikan karena data mahasiswa CSV kosong.")
        return
        
    print(f"Berhasil memuat {len(all_students)} data mahasiswa dari database CSV.")
    
    # Menentukan jumlah responden secara acak
    num_to_select = min(args.target, len(all_students))
    selected_students = random.sample(all_students, num_to_select)
    print(f"Memulai proses pengisian otomatis untuk {num_to_select} mahasiswa terpilih...\n")
    
    # 4. Loop pengisian untuk setiap mahasiswa terpilih
    for index, student in enumerate(selected_students):
        nama = format_natural_name(student.get('nama', 'Mahasiswa'))
        nim = student.get('nim', '')
        angkatan = student.get('angkatan', f"20{nim[:2]}" if nim else "2024")
        
        # Tentukan profil kepuasan responden secara acak agar nilai skala bervariasi secara natural
        profile = random.choices(
            ["sangat_puas", "puas_rata_rata", "kritis"],
            weights=[35, 55, 10]
        )[0]
        
        email = generate_varied_email(nama, nim)
        
        # Selesaikan seluruh nilai jawaban menggunakan AnswerResolver
        all_page_values = resolver.resolve_all_pages(pages, student, profile)
        
        # Kirim form secara multi-halaman sempurna
        success, message = form_handler.submit_pages(
            all_page_values, 
            email=email if has_email_page else ""
        )
        
        status_symbol = "✓" if success else "✗"
        print(f"[{index+1}/{num_to_select}] {status_symbol} {message}: {nama} ({nim} - Angkatan {angkatan})")
        
        # Cetak ulasan sampel jika ada
        for p in all_page_values:
            for item in p:
                if any(k in item['label'].lower() for k in ["pendapat", "saran", "masukan", "ulasan"]):
                    print(f"    > {item['label'][:30]}: \"{item['value']}\"")
        print()
            
        # Jeda pengiriman acak untuk menghindari rate-limiting/deteksi bot
        if index < num_to_select - 1:
            delay = random.randint(args.min_delay, args.max_delay)
            print(f"Menunggu {delay} detik...")
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
