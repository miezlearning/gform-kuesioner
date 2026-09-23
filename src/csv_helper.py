import csv
import re
from typing import List, Dict

def load_students_from_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Membaca database mahasiswa dari file CSV.
    Mendukung delimiter koma (,) atau titik koma (;) secara otomatis.
    Mengembalikan list berisi dictionary dengan semua kolom CSV (nim, nama, angkatan, prodi, dll).
    """
    students = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as file:
            sample = file.read(2048)
            file.seek(0)
            delimiter = ';' if ';' in sample else ','
            reader = csv.DictReader(file, delimiter=delimiter)
            
            for row in reader:
                clean_row = {}
                for key, val in row.items():
                    if key:
                        clean_key = re.sub(r'\s+', ' ', key.strip().lower())
                        clean_row[clean_key] = val.strip() if val else ""
                
                if 'nim' in clean_row and 'nama' in clean_row and clean_row['nim'] and clean_row['nama']:
                    # Auto-derive angkatan jika belum ada di kolom CSV
                    if 'angkatan' not in clean_row or not clean_row['angkatan']:
                        try:
                            clean_row['angkatan'] = f"20{clean_row['nim'][:2]}"
                        except Exception:
                            clean_row['angkatan'] = ""
                    
                    students.append(clean_row)
        return students
    except FileNotFoundError:
        print(f"Error: File '{file_path}' tidak ditemukan.")
        return []
    except Exception as e:
        print(f"Terjadi kesalahan saat membaca CSV: {e}")
        return []
