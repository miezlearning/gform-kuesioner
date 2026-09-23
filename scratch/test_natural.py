import sys
sys.path.append('.')

from src.csv_helper import load_students_from_csv

female_tokens = {
    'putri', 'nabilah', 'dewi', 'intan', 'widya', 'ayu', 'fincy', 'gloria', 
    'angelina', 'bilqis', 'azira', 'nadia', 'niky', 'jenita', 'rusdiana', 
    'azzhahra', 'ghesya', 'rhegyta', 'rahmah', 'audia', 'anggraini', 'nathasia', 
    'umami', 'nuraini', 'faradina', 'pertiwi', 'anisa', 'annisa', 'safitri', 
    'lestari', 'wulandari', 'siti', 'nur', 'indah', 'fitri', 'rahma', 'zahra', 
    'tiara', 'maharani', 'novita', 'lia', 'nia', 'ria', 'maya', 'sari', 'mega', 
    'ratna', 'shinta', 'sinta', 'amelia', 'nabila', 'salma', 'nadira', 'khansa', 
    'cantika', 'aulia', 'firda', 'mutiara', 'marwa', 'alfara', 'alika', 'renaya',
    'astuti', 'manulang', 'aisyah', 'alya', 'diana', 'hana', 'hasna', 'nurul',
    'zahira', 'fadila', 'syifa', 'amalia', 'karina', 'nadya', 'tania'
}

male_tokens = {
    'muhammad', 'mochammad', 'muh', 'mhd', 'm.', 'ahmad', 'achmad', 'akhmad', 'dwiki', 
    'tedy', 'haykal', 'makhmud', 'andi', 'fachry', 'alam', 'tengko', 'syafiq', 
    'hafizh', 'farizi', 'zeydan', 'fazle', 'mawla', 'rusdiansyah', 'ajiva', 
    'alank', 'zulfikar', 'aryawinata', 'elfin', 'sinaga', 'putra', 'ilham', 
    'rizky', 'rizki', 'bagus', 'fajar', 'dimas', 'aditya', 'yoga', 'farhan', 
    'arya', 'arief', 'arifin', 'budi', 'eko', 'agung', 'hendra', 'wahyu', 
    'bayu', 'dani', 'deni', 'faisal', 'hafiz', 'hasan', 'iqbal', 'irfan', 
    'reza', 'satria', 'taufiq', 'yusuf', 'syahrul', 'alif', 'fathur', 'tegar', 
    'bintang', 'raihan', 'faiz', 'gilang', 'pratama', 'aryanda', 'azhari', 
    'setiandra', 'aprilian', 'al-fatih', 'fatih', 'zifa', 'akbar', 'darmawan',
    'kurniawan', 'saputra', 'ramadhan', 'hidayat', 'firmansyah', 'ananda', 'syahputra'
}

def infer_gender_accurate(name: str) -> str:
    cleaned = name.lower().replace('.', ' ').replace('-', ' ')
    words = cleaned.split()
    
    # Priority for explicit prefix
    if words and words[0] in {'muhammad', 'mochammad', 'mhd', 'm', 'ahmad', 'achmad', 'akhmad'}:
        return 'Laki-Laki'
    if words and words[0] in {'siti', 'nur', 'anisa', 'annisa'}:
        return 'Perempuan'
        
    f_count = sum(1 for w in words if w in female_tokens)
    m_count = sum(1 for w in words if w in male_tokens)
    
    if f_count > m_count:
        return 'Perempuan'
    elif m_count > f_count:
        return 'Laki-Laki'
        
    # Check suffixes
    if any(w.endswith(('wati', 'putri', 'dini', 'tina', 'tini', 'liana', 'riani', 'ani')) for w in words):
        return 'Perempuan'
    if any(w.endswith(('putra', 'syah', 'jaya', 'tama', 'wibowo', 'awan')) for w in words):
        return 'Laki-Laki'
        
    return 'Perempuan' if words[-1].endswith(('a', 'i', 'ah', 'ty', 'ti')) else 'Laki-Laki'

for yr in ['2021', '2022', '2023', '2024', '2025']:
    st = load_students_from_csv(f'dataset/{yr}.csv')
    print(f"--- Angkatan {yr} (Total: {len(st)}) ---")
    for s in st[:5]:
        print(f"  {s['nama']:35s} => {infer_gender_accurate(s['nama'])}")
