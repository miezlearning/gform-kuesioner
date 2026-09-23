import sys
sys.path.append('.')
from src.csv_helper import load_students_from_csv

students = load_students_from_csv('dataset/2024.csv')

female_keywords = {
    'putri', 'nabilah', 'dewi', 'intan', 'widya', 'ayu', 'fincy', 'gloria', 
    'angelina', 'bilqis', 'azira', 'nadia', 'niky', 'jenita', 'rusdiana', 
    'azzhahra', 'ghesya', 'rhegyta', 'rahmah', 'audia', 'anggraini', 'nathasia', 
    'umami', 'nuraini', 'faradina', 'pertiwi', 'anisa', 'annisa', 'safitri', 
    'lestari', 'wulandari', 'siti', 'nur', 'indah', 'fitri', 'rahma', 'zahra', 
    'tiara', 'maharani', 'novita', 'lia', 'nia', 'ria', 'maya', 'sari', 'mega', 
    'ratna', 'shinta', 'sinta', 'amelia', 'nabila', 'salma', 'nadira', 'khansa', 
    'cantika', 'aulia', 'firda', 'mutiara', 'marwa', 'alfara', 'alika', 'renaya',
    'astuti', 'manulang'
}

male_keywords = {
    'muhammad', 'mochammad', 'muh', 'mhd', 'm.', 'ahmad', 'achmad', 'dwiki', 
    'tedy', 'haykal', 'makhmud', 'andi', 'fachry', 'alam', 'tengko', 'syafiq', 
    'hafizh', 'farizi', 'zeydan', 'fazle', 'mawla', 'rusdiansyah', 'ajiva', 
    'alank', 'zulfikar', 'aryawinata', 'elfin', 'sinaga', 'putra', 'ilham', 
    'rizky', 'rizki', 'bagus', 'fajar', 'dimas', 'aditya', 'yoga', 'farhan', 
    'arya', 'arief', 'arifin', 'budi', 'eko', 'agung', 'hendra', 'wahyu', 
    'bayu', 'dani', 'deni', 'faisal', 'hafiz', 'hasan', 'iqbal', 'irfan', 
    'reza', 'satria', 'taufiq', 'yusuf', 'syahrul', 'alif', 'fathur', 'tegar', 
    'bintang', 'raihan', 'faiz', 'gilang', 'pratama', 'aryanda', 'azhari', 
    'setiandra', 'aprilian'
}

def infer_gender(name):
    tokens = set(name.lower().replace('.', ' ').split())
    f_score = len(tokens & female_keywords)
    m_score = len(tokens & male_keywords)
    if f_score > m_score:
        return 'Perempuan'
    elif m_score > f_score:
        return 'Laki-Laki'
    return 'Perempuan' if any(w.endswith(('a', 'i', 'ah', 'ty', 'ti')) for w in tokens) else 'Laki-Laki'

for s in students[:25]:
    name = s['nama']
    g = infer_gender(name)
    print(f"{name:40s} => {g}")
