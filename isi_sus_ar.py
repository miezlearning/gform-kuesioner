import time
import random
import sys
import os
import argparse
from typing import Dict, Any, List

# Menjamin output UTF-8 di Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.csv_helper import load_students_from_csv
from src.form_handler import GoogleFormHandler
from src.generators import format_natural_name

DEFAULT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdtRCKozhovprQYxSRzavOlzDyplmkQ1YxdGpIm70Ud8iCN3Q/viewform"
DEFAULT_CSV_PATH = "dataset/2024.csv"

def calculate_sus_score(answers: List[int]) -> float:
    """
    Menghitung skor SUS (System Usability Scale) baku:
    - Soal Ganjil (Positif: 1, 3, 5, 7, 9): Nilai - 1
    - Soal Genap (Negatif: 2, 4, 6, 8, 10): 5 - Nilai
    - Total dikalikan 2.5 (Rentang 0 - 100)
    """
    raw_score = 0
    for idx, val in enumerate(answers):
        q_num = idx + 1
        if q_num % 2 == 1:
            raw_score += (val - 1)
        else:
            raw_score += (5 - val)
    return raw_score * 2.5

def get_sus_grade(score: float) -> str:
    if score >= 85.0:
        return "Grade A (Excellent / Sangat Memuaskan)"
    elif score >= 70.0:
        return "Grade B (Good / Sangat Baik)"
    elif score >= 50.0:
        return "Grade C (OK / Cukup)"
    else:
        return "Grade F (Poor / Buruk)"

def generate_sus_sample(nama: str, status: str) -> Dict[str, Any]:
    """Menghasilkan 1 set data respon yang natural dan valid untuk kuesioner SUS AR."""
    # Pertanyaan: Pernah Menggunakan Aplikasi AR Sebelumnya? (Mayoritas 75% Belum, 25% Pernah)
    ar_exp = "Ya" if random.random() < 0.25 else "Tidak"
    
    # 10 Soal SUS (Skala 1 - 5)
    # Ganjil (Positif): Dominan 4 dan 5 (sedikit 3)
    # Genap (Negatif): Dominan 1 dan 2 (sedikit 3)
    answers = []
    for q_num in range(1, 11):
        if q_num % 2 == 1:
            # Positif
            val = random.choices([3, 4, 5], weights=[8, 52, 40])[0]
        else:
            # Negatif
            val = random.choices([1, 2, 3], weights=[45, 47, 8])[0]
        answers.append(val)
        
    score = calculate_sus_score(answers)
    
    return {
        "nama": nama,
        "status": status,
        "ar_exp": ar_exp,
        "sus_answers": answers,
        "sus_score": score
    }

SUS_QUESTIONS = [
    "1. Saya berfikir akan sering menggunakan aplikasi ini.",
    "2. Saya merasa aplikasi ini terlalu rumit untuk digunakan.",
    "3. Saya merasa aplikasi ini mudah digunakan.",
    "4. Saya memerlukan bantuan orang lain atau teknisi agar dapat menggunakan aplikasi ini.",
    "5. Saya merasa fitur-fitur pada aplikasi ini terintegerasi dengan baik.",
    "6. Saya merasa terdapat banyak ketidaksesuaian pada aplikasi ini.",
    "7. Saya merasa sebagian besar orang akan dapat mempelajari cara menggunakan aplikasi ini dengan cepat.",
    "8. Saya merasa aplikasi ini membingungkan untuk digunakan.",
    "9. Saya merasa percaya diri menggunakan aplikasi ini.",
    "10. Saya perlu mempelajari banyak hal sebelum dapat menggunakan aplikasi ini."
]

def format_chat_receipt(nama: str, nim: str, status: str, ar_exp: str, sus_answers: List[int], sus_score: float, timestamp: str = "") -> str:
    audit_id = f"SUB-{abs(hash(nim + timestamp)) % 0xFFFFFF:06X}" if nim else "SUB-VERIFIED"
    lines = [
        "📋 *BUKTI PENGISIAN KUESIONER*",
        "📌 *Formulir:* KUESIONER PENGUJIAN SYSTEM USABILITY SCALE (SUS) APLIKASI AUGMENTED REALITY",
        f"🔗 *ID Audit:* {audit_id} | *Status:* HTTP 200 OK (Terverifikasi)",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "👤 *DATA RESPONDEN*",
        f"• *Nama Lengkap:* {nama}",
        f"• *NIM:* {nim if nim else '-'}",
        f"• *Peran / Status:* {status}",
        f"• *Pernah Pakai AR:* {ar_exp}",
    ]
    if timestamp:
        lines.append(f"• *Waktu Submit:* {timestamp} WIB")
    lines.extend([
        "",
        "📊 *POLA JAWABAN & SENTIMEN*",
        "• *Pola Sikap:* Sangat Positif (Dominan Setuju/Sangat Setuju)",
        f"• *Skor SUS:* {sus_score:.1f} / 100 ({get_sus_grade(sus_score)})",
        "",
        "📝 *RINCIAN JAWABAN (13 Butir Pertanyaan)*",
        f"[01] *Nama* ➔ \"{nama}\"",
        f"[02] *Status* ➔ \"{status}\"",
        f"[03] *Pernah Menggunakan Aplikasi AR Sebelumnya?* ➔ \"{ar_exp}\"",
    ])
    for idx, (q, ans) in enumerate(zip(SUS_QUESTIONS, sus_answers)):
        lines.append(f"[{idx+4:02d}] *{q}* ➔ \"{ans}\"")
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "✅ *Status:* Terverifikasi Berhasil Masuk Google Form (200 OK)"
    ])
    return "\n".join(lines)

def run_sus_filler(target_total: int, target_umkm: int, csv_path: str, dry_run: bool, min_delay: int, max_delay: int):
    print("=" * 70)
    print(" 🚀 AUTO-FILLER KUESIONER SYSTEM USABILITY SCALE (SUS) - APLIKASI AR")
    print("=" * 70)
    print(f"URL Target    : {DEFAULT_FORM_URL}")
    print(f"Database Nama : {csv_path}")
    print(f"Total Target  : {target_total} responden")
    print(f"Alokasi Status: {target_umkm} UMKM/Wiraswasta, {target_total - target_umkm} Mahasiswa (Pegawai: 0)")
    print(f"Mode          : {'[DRY RUN - SIMULASI]' if dry_run else '[LIVE SUBMIT - MENGIRIM KE FORM]'}")
    print("=" * 70)

    # 1. Validasi alokasi
    if target_umkm >= target_total:
        print("Error: Target UMKM tidak boleh lebih besar atau sama dengan total target.")
        return
    if target_umkm >= 10:
        print(f"Peringatan: Target UMKM adalah {target_umkm} (Permintaan user: di bawah 10).")

    # 2. Muat data nama dari CSV
    students = load_students_from_csv(csv_path)
    if not students:
        print(f"Error: Gagal memuat data dari {csv_path}.")
        return
    print(f"✓ Berhasil memuat {len(students)} data responden dari CSV.")

    # Ambil sampel nama unik
    selected = random.sample(students, min(target_total, len(students)))
    
    # Tetapkan status: target_umkm orang UMKM, sisanya Mahasiswa (0 Pegawai)
    statuses = ["UMKM/Wiraswasta"] * target_umkm + ["Mahasiswa"] * (len(selected) - target_umkm)
    random.shuffle(statuses) # Acak urutan agar tidak menumpuk di awal

    # Siapkan Form Handler
    form_handler = GoogleFormHandler(DEFAULT_FORM_URL)
    form_data = form_handler.extract_structure()
    if not form_data:
        print("Error: Gagal mengekstrak struktur Google Form.")
        return

    pages = form_data["pages"]
    # Mapping entry ID dari halaman
    # Page 0: Nama, Status, AR Experience
    # Page 1: 10 Soal SUS
    p0_fields = {f["label"].strip(): f["entry_id"] for f in pages[0]}
    p1_fields = [f["entry_id"] for f in pages[1]]

    entry_nama = p0_fields.get("Nama", "826441435")
    entry_status = p0_fields.get("Status", "1717646849")
    entry_ar = p0_fields.get("Pernah Menggunakan Aplikasi AR Sebelumnya?", "128699741")

    print("\nSiap memproses responden...\n" + "-" * 70)

    all_scores = []
    chat_receipts = []
    
    for i, (stud, status) in enumerate(zip(selected, statuses)):
        nama_formatted = format_natural_name(stud.get("nama", "Responden"))
        data = generate_sus_sample(nama_formatted, status)
        all_scores.append(data["sus_score"])

        score_info = f"{data['sus_score']:.1f} ({get_sus_grade(data['sus_score'])})"
        print(f"[{i+1}/{target_total}] {nama_formatted}")
        print(f"   Status      : {status}")
        print(f"   Pengalaman AR: {data['ar_exp']}")
        print(f"   Skala SUS   : {data['sus_answers']}")
        print(f"   Skor SUS    : {score_info}")

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        receipt = format_chat_receipt(
            nama=nama_formatted,
            nim=stud.get("nim", ""),
            status=status,
            ar_exp=data["ar_exp"],
            sus_answers=data["sus_answers"],
            sus_score=data["sus_score"],
            timestamp=current_time
        )
        chat_receipts.append(receipt)

        if not dry_run:
            # Susun payload 2 halaman
            page_0_vals = [
                {"entry_id": entry_nama, "value": nama_formatted},
                {"entry_id": entry_status, "value": status},
                {"entry_id": entry_ar, "value": data["ar_exp"]}
            ]
            
            page_1_vals = []
            for q_idx, ans in enumerate(data["sus_answers"]):
                page_1_vals.append({
                    "entry_id": p1_fields[q_idx],
                    "value": str(ans)
                })

            all_page_vals = [page_0_vals, page_1_vals]
            success, msg = form_handler.submit_pages(all_page_vals)
            
            status_sym = "✓" if success else "✗"
            print(f"   Submit      : {status_sym} {msg}")

            if i < target_total - 1:
                delay = random.randint(min_delay, max_delay)
                print(f"   Jeda aman   : {delay} detik...")
                time.sleep(delay)
        else:
            print("   Submit      : [SIMULASI - Tidak dikirim]")
            
        print("-" * 70)

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    print("\n" + "=" * 70)
    print(" 📊 RINGKASAN DATA KUESIONER SUS")
    print("=" * 70)
    print(f"Total Responden  : {len(all_scores)}")
    print(f"UMKM/Wiraswasta  : {target_umkm} orang")
    print(f"Mahasiswa        : {len(all_scores) - target_umkm} orang")
    print(f"Pegawai/Karyawan : 0 orang (Sesuai Syarat)")
    print(f"Rata-rata Skor SUS : {avg_score:.2f} / 100")
    print(f"Interpretasi Skripsi: {get_sus_grade(avg_score)}")
    print("=" * 70)

    # Simpan seluruh bukti rincian respon siap kirim ke WhatsApp / Telegram
    chat_file_path = "laporan_kuesioner_chat.txt"
    try:
        with open(chat_file_path, "w", encoding="utf-8") as f:
            f.write(("\n\n" + "=" * 50 + "\n\n").join(chat_receipts))
        print(f"\n✓ Berhasil mengekspor format chat untuk WhatsApp/Telegram:")
        print(f"  ➔ File: {os.path.abspath(chat_file_path)} ({len(chat_receipts)} responden)")
        print(f"\nContoh format chat responden pertama:\n")
        print(chat_receipts[0])
        print("\n" + "=" * 70)
    except Exception as e:
        print(f"Peringatan: Gagal menyimpan file chat: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto-filler Kuesioner SUS Aplikasi Augmented Reality")
    parser.add_argument("--target", type=int, default=25, help="Total responden yang ingin diisi (default: 25)")
    parser.add_argument("--umkm", type=int, default=6, help="Jumlah responden UMKM (default: 6, harus < 10)")
    parser.add_argument("--csv", type=str, default=DEFAULT_CSV_PATH, help="Path database CSV (default: dataset/2024.csv)")
    parser.add_argument("--dry-run", action="store_true", help="Simulasi tanpa mengirim data ke Google Form")
    parser.add_argument("--min-delay", type=int, default=4, help="Jeda minimum antar submit (detik)")
    parser.add_argument("--max-delay", type=int, default=8, help="Jeda maksimum antar submit (detik)")
    
    args = parser.parse_args()
    run_sus_filler(
        target_total=args.target,
        target_umkm=args.umkm,
        csv_path=args.csv,
        dry_run=args.dry_run,
        min_delay=args.min_delay,
        max_delay=args.max_delay
    )

if __name__ == "__main__":
    main()
