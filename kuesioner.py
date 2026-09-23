import time
import random
import sys
from typing import Dict, Any

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


def run_auto_fill():
    print("=" * 60)
    print("      GOOGLE FORMS QUESTIONNAIRE AUTO-FILLER")
    print("=" * 60)
    
    # Input interaktif untuk URL Google Form (Tekan Enter untuk gunakan default)
    user_url_input = input(f"Masukkan URL Google Form [ENTER untuk default]: ").strip()
    form_url = user_url_input if user_url_input else FORM_URL
    print(f"Menggunakan URL: {form_url}\n")
    
    # 1. Inisialisasi handler Form & generator teks AI
    form_handler = GoogleFormHandler(form_url)
    ai_generator = AITextGenerator()
    resolver = AnswerResolver(ai_generator)

    # 2. Ekstrak struktur lengkap Google Form
    form_data = form_handler.extract_structure()
    if not form_data:
        print("Ekstraksi struktur form gagal. Periksa koneksi internet atau link form Anda.")
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

    # 3. Load data mahasiswa dari file CSV
    all_students = load_students_from_csv(CSV_FILE_PATH)
    if not all_students:
        print("Proses dihentikan karena data mahasiswa CSV kosong.")
        return
        
    print(f"Berhasil memuat {len(all_students)} data mahasiswa dari database CSV.")
    
    # Menentukan jumlah responden secara acak
    num_to_select = min(TARGET_SUBMISSIONS, len(all_students))
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
        
        # Bangun parameter partialResponse dari halaman 1 s/d N-1 (jika form multi-page)
        partial_entries = []
        if len(all_page_values) > 1:
            for page_values in all_page_values[:-1]:
                for field_val in page_values:
                    partial_entries.append((field_val["entry_id"], field_val["value"]))
            partial_response_json = form_handler.build_partial_response(partial_entries, fbzx, email)
        else:
            partial_response_json = ""
        
        # Bangun top-level payload dari halaman TERAKHIR
        last_page = all_page_values[-1]
        payload = {}
        for field_val in last_page:
            entry_key = f"entry.{field_val['entry_id']}"
            val = field_val["value"]
            if isinstance(val, list):
                payload[entry_key] = val
            else:
                payload[entry_key] = str(val)
            
            # Google Forms memerlukan marker field kosong untuk pertanyaan linear scale (Type 5)
            for field in pages[-1]:
                if str(field["entry_id"]) == str(field_val["entry_id"]) and field.get("type") == 5:
                    payload[f"{entry_key}_sentinel"] = ""
                    break
        
        payload["fvv"] = fvv
        if partial_response_json:
            payload["partialResponse"] = partial_response_json
        payload["pageHistory"] = page_history
        payload["fbzx"] = fbzx
        payload["submissionTimestamp"] = str(int(time.time() * 1000))
        
        if has_email_page:
            payload["emailAddress"] = email
            
        # 5. Kirim payload respon kuesioner ke Google Form
        success, message = form_handler.submit(payload, referer_url=form_handler.submit_url)
        
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
            delay = random.randint(SUBMISSION_DELAY_MIN, SUBMISSION_DELAY_MAX)
            print(f"Menunggu {delay} detik...")
            time.sleep(delay)


if __name__ == "__main__":
    run_auto_fill()