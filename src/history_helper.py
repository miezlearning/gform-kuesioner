import os
import json
from typing import List

HISTORY_FILE = "dataset/history.json"

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
            # Pastikan folder parent ada
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"Error saving to history: {e}")

def clear_history() -> bool:
    """
    Mereset semua riwayat pengisian.
    """
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False
