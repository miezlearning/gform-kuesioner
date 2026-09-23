import sys
sys.path.append('.')

from src.form_handler import GoogleFormHandler
from src.csv_helper import load_students_from_csv
from src.answer_resolver import AnswerResolver

test_url = "https://docs.google.com/forms/d/e/1FAIpQLSfx5v4xjqh9RE8UorAssOwZFcEqZZBYNir4aQynkW0xs4-yUg/viewform"

handler = GoogleFormHandler(test_url)
structure = handler.extract_structure()
resolver = AnswerResolver()

sample_students = []
for yr in ['2024', '2023', '2022', '2021']:
    st = load_students_from_csv(f'dataset/{yr}.csv')
    if st:
        sample_students.append(st[0])
        if len(st) > 1:
            sample_students.append(st[1])

print(f"\nUJI KESINKRONAN DATA DENGAN PDDIKTI PADA {len(sample_students)} MAHASISWA:\n")

for i, student in enumerate(sample_students[:4]):
    print(f"{'='*60}")
    print(f"Responden #{i+1}: {student['nama']} ({student['nim']}) - Angkatan {student['angkatan']}")
    print(f"{'='*60}")
    
    pages_ans = resolver.resolve_all_pages(structure['pages'], student, profile="sangat_puas")
    
    # Cetak hanya pertanyaan identitas & beberapa skala
    for p_idx, page in enumerate(pages_ans):
        if p_idx <= 1:  # Halaman 1 & 2 (Informed consent & Identitas)
            for item in page:
                print(f"  {item['label'][:35]:35s} => {item['value']}")
        elif p_idx == 2:
            print(f"  [Contoh Skala Halaman 3]             => {page[0]['value']}")
    print()
