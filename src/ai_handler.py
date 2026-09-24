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

    def _get_prompt(self, prompt_type: str, context: str = "") -> str:
        """Mengembalikan petunjuk instruksi untuk AI sesuai jenis permintaan dan konteks kuesioner."""
        topic_info = f"Pertanyaan: '{context}'." if context else ""
        return (
            "Kamu adalah seorang mahasiswa Indonesia masa kini (Gen Z). "
            f"{topic_info} "
            "Tuliskan 1 kalimat tanggapan/jawaban kuesioner yang SANGAT NATURAL, santai, dan realistis (sekitar 5 sampai 15 kata). "
            "Gunakan gaya bahasa mahasiswa anak muda zaman sekarang yang wajar dan biasa dipakai di sosmed/chat "
            "(misal memakai kata: udah, banget, sih, ga ribet, lumayan, overall, ngebantu, dll). "
            "PENTING: JANGAN kaku atau terlalu baku birokratis (hindari kata kaku seperti 'memadai', 'seyogyanya', 'berkenaan'). "
            "TAPI JANGAN JUGA alay lebay berlebihan (hindari kata alay seperti 'wkwk', 'xixi', 'ygy', huruf besar kecil tak beraturan). "
            "Tuliskan teks polos tanpa tanda petik dan tanpa markdown."
        )

    def generate_text(self, prompt_type: str, context: str = "", max_retries: int = 1) -> str:
        """
        Menghasilkan teks unik (pendapat / saran / jawaban konteks) dengan gaya natural mahasiswa.
        Jika API offline atau lambat, langsung beralih ke synthesizer fallback lokal secara instan.
        """
        target_set = self.used_pendapat if prompt_type == "pendapat" else self.used_saran
        prompt = self._get_prompt(prompt_type, context)
        
        # 1. Coba menggunakan API jika sirkuit aktif dengan timeout ketat (2 detik)
        if self.api_available:
            for _ in range(max_retries):
                try:
                    response = requests.get(self.api_url, params={"text": prompt}, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        ai_text = data.get("text") or data.get("result") or data.get("response") or data.get("reply") or str(data)
                        ai_text = ai_text.strip().replace('"', '').replace('\u2011', '-')
                        ai_text = re.sub(r'[*_#`~]', '', ai_text).strip()
                        
                        if ai_text and not is_too_similar(ai_text, target_set):
                            target_set.add(ai_text)
                            return ai_text
                except Exception:
                    # Matikan API jika error / timeout agar proses pengisian tetap secepat kilat
                    self.api_available = False
                    break
                    
        # 2. Generator Fallback Lokal Natural Mahasiswa (Instan & Beragam)
        for _ in range(30):
            val = get_fallback_text(prompt_type, context=context)
            if not is_too_similar(val, target_set):
                target_set.add(val)
                return val
                
        # 3. Fallback absolut unik
        val = get_fallback_text(prompt_type, context=context)
        target_set.add(val)
        return val

    def generate_context_text(self, question_label: str) -> str:
        """
        Menghasilkan jawaban teks bebas yang relevan dengan pertanyaan terbuka form secara dinamis,
        menggunakan gaya bahasa natural mahasiswa masa kini.
        """
        lbl_lower = question_label.lower()
        if any(w in lbl_lower for w in ["motivasi", "belajar", "akademik", "grit", "cita", "kuliah", "tujuan", "upaya", "prestasi", "alasan"]):
            return self.generate_text("akademik", context=question_label)
        if any(w in lbl_lower for w in ["kendala", "hambatan", "kesulitan", "masalah", "keluhan"]):
            return self.generate_text("kendala", context=question_label)
        if any(w in lbl_lower for w in ["saran", "masukan", "kritik", "rekomendasi", "harapan", "perbaikan"]):
            return self.generate_text("saran", context=question_label)
        if any(w in lbl_lower for w in ["pendapat", "ulasan", "review", "kesan", "pandangan", "tanggapan"]):
            return self.generate_text("pendapat", context=question_label)
            
        return self.generate_text("umum", context=question_label)
