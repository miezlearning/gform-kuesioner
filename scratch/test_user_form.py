import sys
import json
sys.path.append('.')

from src.form_handler import GoogleFormHandler
from src.csv_helper import load_students_from_csv
from src.answer_resolver import AnswerResolver

test_url = "https://docs.google.com/forms/d/e/1FAIpQLSfx5v4xjqh9RE8UorAssOwZFcEqZZBYNir4aQynkW0xs4-yUg/viewform"

print("==================================================")
print("1. MEMERIKSA DAN MENGEKSTRAK STRUKTUR GOOGLE FORM")
print("==================================================")
handler = GoogleFormHandler(test_url)
structure = handler.extract_structure()

if not structure:
    print("Gagal mengekstrak struktur Google Form. Periksa link form.")
    sys.exit(1)

print(f"Judul Form       : {structure.get('form_title')}")
print(f"Deskripsi Form   : {structure.get('form_description')[:80]}...")
print(f"Total Halaman    : {structure.get('num_pages')}")
print(f"Halaman Email    : {structure.get('has_email_page')}")
print(f"Total Pertanyaan : {len(structure.get('questions', []))}")
print("-" * 50)

print("\n==================================================")
print("2. DAFTAR PERTANYAAN & OPSI YANG TERBACA")
print("==================================================")
for idx, q in enumerate(structure.get('questions', [])):
    req_mark = "*" if q.get("required") else ""
    print(f"[{idx+1}] [{q.get('type_name')}] {q.get('label')}{req_mark} (entry.{q.get('entry_id')})")
    print(f"    Bagian/Section : {q.get('section_title')} (Halaman {q.get('page_index')+1})")
    if q.get("options"):
        print(f"    Pilihan Opsi   : {q.get('options')}")
    if q.get("scale_bounds"):
        sb = q.get("scale_bounds")
        print(f"    Rentang Skala  : {sb.get('min')} ({sb.get('min_label')}) s/d {sb.get('max')} ({sb.get('max_label')})")
    print(f"    Saran Aturan   : {q.get('suggested_rule')}")
    print()

print("\n==================================================")
print("3. SIMULASI RESOLUSI JAWABAN (TANPA SUBMIT)")
print("==================================================")
students = load_students_from_csv('dataset/2024.csv')
if not students:
    students = [{"nama": "Budi Santoso", "nim": "2409106099", "angkatan": "2024"}]

test_student = students[0]
print(f"Sampel Responden : {test_student.get('nama')} ({test_student.get('nim')} - Angkatan {test_student.get('angkatan')})")
print(f"Profil Kepuasan  : Sangat Puas\n")

resolver = AnswerResolver()
simulated_answers = resolver.resolve_all_pages(structure['pages'], test_student, profile="sangat_puas")

for page_idx, page in enumerate(simulated_answers):
    print(f"--- HALAMAN {page_idx + 1} ---")
    for item in page:
        print(f"  entry.{item['entry_id']} -> [{item['label'][:40]}]")
        print(f"     => Jawaban: {item['value']}")
    print()

print("==================================================")
print("TEST SELESAI. TIDAK ADA DATA YANG DI-SUBMIT KE GOOGLE.")
print("==================================================")
