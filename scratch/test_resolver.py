from src.form_handler import GoogleFormHandler
from src.csv_helper import load_students_from_csv
from src.answer_resolver import AnswerResolver

h = GoogleFormHandler('https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform')
data = h.extract_structure()
students = load_students_from_csv('dataset/2024.csv')
resolver = AnswerResolver()

test_student = students[0]
res = resolver.resolve_all_pages(data['pages'], test_student, 'sangat_puas')
print("Student:", test_student['nama'], "-", test_student['nim'])
for pi, page in enumerate(res):
    print(f"--- Page {pi+1} ---")
    for item in page:
        lbl = item['label'][:35]
        print(f"  entry.{item['entry_id']} ({lbl}) => {item['value']}")
