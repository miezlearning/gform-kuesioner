import os
import json
import time
from typing import Dict, Any, List, Optional

SAVED_FORMS_FILE = os.path.join("dataset", "saved_forms.json")

DEFAULT_FORMS_SEED = [
    {
        "id": "sus_augmented_reality",
        "url": "https://docs.google.com/forms/d/e/1FAIpQLSdtRCKozhovprQYxSRzavOlzDyplmkQ1YxdGpIm70Ud8iCN3Q/viewform",
        "original_url": "https://forms.gle/Jrk8fysRGdGf69Pq9",
        "title": "KUESIONER PENGUJIAN SYSTEM USABILITY SCALE (SUS) APLIKASI AUGMENTED REALITY",
        "description": "Kuesioner evaluasi kegunaan sistem SUS untuk pengujian aplikasi Augmented Reality.",
        "num_pages": 4,
        "questions_count": 13,
        "has_email_page": True,
        "last_used": "2026-10-24 20:30:00",
        "question_rules": {
            "0": {"type": "identitas_nama"},
            "1": {"type": "pilihan_tetap", "value": "Mahasiswa", "target_umkm": 3},
            "2": {"type": "identitas_prodi"},
            "3": {"type": "sus_ganjil_positif"},
            "4": {"type": "sus_genap_negatif"},
            "5": {"type": "sus_ganjil_positif"},
            "6": {"type": "sus_genap_negatif"},
            "7": {"type": "sus_ganjil_positif"},
            "8": {"type": "sus_genap_negatif"},
            "9": {"type": "sus_ganjil_positif"},
            "10": {"type": "sus_genap_negatif"},
            "11": {"type": "sus_ganjil_positif"},
            "12": {"type": "sus_genap_negatif"}
        }
    }
]

def _normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    # Strip query parameters like ?usp=sf_link
    if "?" in url:
        url = url.split("?")[0]
    return url

def load_saved_forms() -> Dict[str, Any]:
    """Membaca daftar formulir yang pernah disimpan dari dataset/saved_forms.json."""
    if not os.path.exists(SAVED_FORMS_FILE):
        initial_data = {
            "last_active_url": DEFAULT_FORMS_SEED[0]["url"],
            "forms": list(DEFAULT_FORMS_SEED)
        }
        try:
            os.makedirs(os.path.dirname(SAVED_FORMS_FILE), exist_ok=True)
            with open(SAVED_FORMS_FILE, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            return initial_data
        except Exception:
            return {"last_active_url": DEFAULT_FORMS_SEED[0]["url"], "forms": list(DEFAULT_FORMS_SEED)}

    try:
        with open(SAVED_FORMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {"last_active_url": "", "forms": []}
            if "forms" not in data or not isinstance(data["forms"], list):
                data["forms"] = []
            return data
    except Exception:
        return {"last_active_url": "", "forms": []}

def save_saved_forms(data: Dict[str, Any]) -> bool:
    """Menyimpan data formulir ke dataset/saved_forms.json."""
    try:
        os.makedirs(os.path.dirname(SAVED_FORMS_FILE), exist_ok=True)
        with open(SAVED_FORMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan saved_forms.json: {e}")
        return False

def save_form_entry(
    url: str,
    title: str = "",
    structure: Optional[Dict[str, Any]] = None,
    question_rules: Optional[Dict[str, Any]] = None,
    original_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Menyimpan atau memperbarui formulir dalam riwayat tersimpan.
    Menjadikan formulir ini sebagai last_active_url secara otomatis.
    """
    data = load_saved_forms()
    norm_url = _normalize_url(url)
    if not norm_url:
        return data

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    forms: List[Dict[str, Any]] = data.get("forms", [])

    # Cari apakah formulir dengan URL ini sudah ada
    existing_idx = -1
    for idx, f in enumerate(forms):
        if _normalize_url(f.get("url", "")) == norm_url or (original_url and _normalize_url(f.get("original_url", "")) == _normalize_url(original_url)):
            existing_idx = idx
            break

    entry: Dict[str, Any] = {}
    if existing_idx >= 0:
        entry = forms[existing_idx]
    else:
        entry = {
            "id": f"form_{int(time.time())}",
            "url": norm_url,
            "original_url": original_url or url,
            "title": title or "Formulir Kuesioner Google",
            "description": "",
            "num_pages": 1,
            "questions_count": 0,
            "has_email_page": False,
            "question_rules": {},
            "questions": []
        }

    # Perbarui informasi jika disediakan
    if title and title.strip():
        entry["title"] = title.strip()
    if original_url:
        entry["original_url"] = original_url
    entry["url"] = norm_url
    entry["last_used"] = timestamp

    if structure:
        if structure.get("form_title"):
            entry["title"] = structure.get("form_title")
        if structure.get("form_description"):
            entry["description"] = structure.get("form_description")
        if structure.get("num_pages"):
            entry["num_pages"] = structure.get("num_pages")
        if structure.get("questions"):
            entry["questions"] = structure.get("questions")
            entry["questions_count"] = len(structure.get("questions"))
        if "has_email_page" in structure:
            entry["has_email_page"] = structure.get("has_email_page")

    if question_rules is not None:
        entry["question_rules"] = question_rules

    if existing_idx >= 0:
        forms.pop(existing_idx)
    
    # Sisipkan di posisi teratas (paling baru digunakan)
    forms.insert(0, entry)
    
    # Batasi riwayat maksimal 50 formulir
    data["forms"] = forms[:50]
    data["last_active_url"] = norm_url

    save_saved_forms(data)
    return data

def get_last_active_form() -> Optional[Dict[str, Any]]:
    """Mendapatkan formulir yang terakhir kali aktif digunakan."""
    data = load_saved_forms()
    last_url = data.get("last_active_url")
    forms = data.get("forms", [])
    if not forms:
        return None
    if last_url:
        for f in forms:
            if _normalize_url(f.get("url", "")) == _normalize_url(last_url):
                return f
    return forms[0]

def delete_saved_form(url: str) -> Dict[str, Any]:
    """Menghapus formulir dari daftar tersimpan berdasarkan URL."""
    data = load_saved_forms()
    norm_url = _normalize_url(url)
    forms = data.get("forms", [])
    data["forms"] = [f for f in forms if _normalize_url(f.get("url", "")) != norm_url and _normalize_url(f.get("original_url", "")) != norm_url]
    
    if data.get("last_active_url") == norm_url:
        data["last_active_url"] = data["forms"][0]["url"] if data["forms"] else ""
        
    save_saved_forms(data)
    return data

def set_last_active_url(url: str) -> bool:
    """Mengatur URL formulir aktif saat ini."""
    data = load_saved_forms()
    data["last_active_url"] = _normalize_url(url)
    return save_saved_forms(data)
