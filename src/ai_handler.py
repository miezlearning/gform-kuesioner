import requests
import random
import re
from typing import Set, Dict, Optional
from .config import AI_API_URL
from .generators import is_too_similar, get_fallback_text

class AITextGenerator:
    """
    Menangani pemanggilan AI API GPT untuk menghasilkan ulasan (pendapat) 
    dan saran unik secara dinamis dengan deteksi duplikat otomatis serta
    fallback template cerdas berkinerja tinggi.
    """
    def __init__(self, api_url: str = AI_API_URL):
        self.api_url = api_url
        self.used_pendapat: Set[str] = set()
        self.used_saran: Set[str] = set()
        self.used_custom: Dict[str, Set[str]] = {}
        self.api_available: bool = True  # Circuit breaker jika API eksternal offline/error SSL

    def _get_prompt(self, prompt_type: str) -> str:
        """Mengembalikan petunjuk instruksi untuk AI sesuai jenis permintaan."""
        if prompt_type == "pendapat":
            return (
                "Kamu adalah mahasiswa yang baru saja menggunakan website 'E-Surat 2 FT Unmul'. "
                "Tuliskan 1 kalimat ulasan/pendapat yang SANGAT SINGKAT, SIMPEL, dan alami (hanya 3 sampai 6 kata saja). "
                "Pilih HANYA SATU topik: tampilan rapi, proses pengajuan mudah, loading cepat, atau tracking surat gampang. "
                "Hindari kalimat panjang atau alay berlebihan. Tuliskan teks polos tanpa tanda petik atau markdown."
            )
        else:  # saran
            return (
                "Kamu adalah mahasiswa yang baru saja menggunakan website 'E-Surat 2 FT Unmul'. "
                "Tuliskan 1 kalimat saran perbaikan yang SANGAT SINGKAT, SIMPEL, dan alami (hanya 3 sampai 6 kata saja). "
                "Pilih HANYA SATU topik: batas file size upload, tombol kirim ganti warna, menu KHS segera diaktifkan, atau loading dipercepat. "
                "Hindari kalimat panjang. Tuliskan teks polos tanpa tanda petik atau markdown."
            )

    def generate_text(self, prompt_type: str, max_retries: int = 2) -> str:
        """
        Menghasilkan teks AI unik (pendapat / saran) yang tidak mirip dengan teks sebelumnya.
        Jika API offline/gagal, langsung beralih ke generator fallback lokal secara instan.
        """
        target_set = self.used_pendapat if prompt_type == "pendapat" else self.used_saran
        prompt = self._get_prompt(prompt_type)
        
        # 1. Coba menggunakan API jika sirkuit aktif
        if self.api_available:
            for _ in range(max_retries):
                try:
                    response = requests.get(self.api_url, params={"text": prompt}, timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        ai_text = data.get("text") or data.get("result") or data.get("response") or data.get("reply") or str(data)
                        ai_text = ai_text.strip().replace('"', '').replace('\u2011', '-')
                        ai_text = re.sub(r'[*_#`~]', '', ai_text).strip()
                        
                        if ai_text and not is_too_similar(ai_text, target_set):
                            target_set.add(ai_text)
                            return ai_text
                except Exception:
                    # Nonaktifkan pemanggilan berulang jika API eksternal bermasalah (SSL / Connection Error)
                    self.api_available = False
                    break
                    
        # 2. Coba menggunakan Fallback Lokal Dinamis
        for _ in range(30):
            val = get_fallback_text(prompt_type)
            if not is_too_similar(val, target_set):
                target_set.add(val)
                return val
                
        # 3. Fallback absolut (ditambahkan angka acak agar tetap unik)
        val = get_fallback_text(prompt_type) + f" {random.randint(100, 999)}"
        target_set.add(val)
        return val

    def generate_context_text(self, question_label: str) -> str:
        """
        Menghasilkan jawaban teks bebas yang relevan dengan pertanyaan terbuka form secara dinamis.
        """
        lbl_lower = question_label.lower()
        if any(w in lbl_lower for w in ["pendapat", "ulasan", "review", "kesan", "pandangan", "tanggapan"]):
            return self.generate_text("pendapat")
        if any(w in lbl_lower for w in ["saran", "masukan", "kritik", "rekomendasi", "harapan"]):
            return self.generate_text("saran")
            
        # Untuk pertanyaan umum lainnya
        generic_answers = [
            "Sudah cukup baik dan memadai.",
            "Secara umum sudah sesuai harapan.",
            "Prosesnya cukup lancar dan efisien.",
            "Fitur yang tersedia sudah sangat membantu.",
            "Pengalaman penggunaan cukup memuaskan.",
            "Sistem bekerja dengan stabil dan baik.",
            "Informasi yang disajikan jelas.",
            "Tidak ada kendala yang berarti."
        ]
        chosen = random.choice(generic_answers)
        return chosen
