import os
import json
from typing import List

HISTORY_FILE = "dataset/history.json"

SUBMISSIONS_FILE = "dataset/submissions_log.json"

def load_history() -> List[str]:
    """
    Membaca daftar NIM mahasiswa yang sudah pernah dikirim kuesionernya.
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(nim) for nim in data]
            return []
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def save_to_history(nim: str) -> None:
    """
    Menambahkan NIM ke daftar riwayat yang sudah diisi.
    """
    history = load_history()
    nim_str = str(nim).strip()
    if nim_str not in history:
        history.append(nim_str)
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"Error saving to history: {e}")

def load_submission_records() -> List[dict]:
    """
    Membaca daftar detail submisi yang tersimpan.
    """
    if not os.path.exists(SUBMISSIONS_FILE):
        return []
    try:
        with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading submission records: {e}")
        return []

def save_submission_record(record: dict) -> None:
    """
    Menyimpan rincian lengkap jawaban responden yang sukses disubmit.
    """
    records = load_submission_records()
    records.append(record)
    try:
        os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)
        with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving submission record: {e}")

def clear_history() -> bool:
    """
    Mereset semua riwayat pengisian dan log detail submisi.
    """
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        if os.path.exists(SUBMISSIONS_FILE):
            os.remove(SUBMISSIONS_FILE)
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False
