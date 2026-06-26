import csv
from typing import List, Dict

def load_students_from_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Membaca database mahasiswa dari file CSV.
    Mendukung delimiter koma (,) atau titik koma (;) secara otomatis.
    Mengembalikan list berisi dictionary dengan key 'nim' dan 'nama'.
    """
    students = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            # Baca sampel untuk deteksi delimiter otomatis
            sample = file.read(2048)
            file.seek(0)
            delimiter = ';' if ';' in sample else ','
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row in reader:
                # Bersihkan nama kolom dan nilai dari whitespace
                clean_row = {
                    key.strip().lower(): val.strip() 
                    for key, val in row.items() 
                    if key
                }
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
