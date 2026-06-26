import requests
import random
import re
from typing import Set
from config import AI_API_URL
from generators import is_too_similar, get_fallback_text

class AITextGenerator:
    """
    Menangani pemanggilan AI API GPT untuk menghasilkan ulasan (pendapat) 
    dan saran unik secara dinamis dengan deteksi duplikat otomatis.
    """
    def __init__(self, api_url: str = AI_API_URL):
        self.api_url = api_url
        self.used_pendapat: Set[str] = set()
        self.used_saran: Set[str] = set()

    def _get_prompt(self, prompt_type: str) -> str:
        """Mengembalikan petunjuk (prompt) instruksi untuk GPT sesuai jenis permintaan."""
        if prompt_type == "pendapat":
            return (
                "Kamu adalah mahasiswa Universitas Mulawarman yang baru saja menggunakan website 'E-Surat 2 FT Unmul'. "
                "Tuliskan 1 kalimat ulasan/pendapat yang SANGAT SINGKAT, SIMPEL, dan alami (hanya 3 sampai 6 kata saja). "
                "Pilih HANYA SATU dari topik berikut tentang website ini untuk ditulis:\n"
                "- Tampilan dashboard atau menu sidebar yang rapi (contoh: 'tampilan menunya sudah rapi')\n"
                "- Kemudahan proses pengajuan surat (contoh: 'pengajuan suratnya tidak ribet')\n"
                "- Kecepatan respon/loading halaman (contoh: 'aksesnya lumayan cepat', 'cukup fast respond')\n"
                "- Kemudahan tracking status surat (contoh: 'cek status surat mudah')\n"
                "Hindari kalimat panjang atau kata penghubung bertumpuk. Tuliskan langsung intinya saja dalam gaya mengetik mahasiswa yang santai, wajar, dan manusiawi. "
                "JANGAN menggunakan kata slang/alay yang berlebihan (seperti 'sat set', 'no debat', 'gacor', 'gokil', 'parah', dll). "
                "Tuliskan teks polos saja, TANPA tanda bintang (*), tebal, miring, atau format markdown lainnya."
            )
        else:  # saran
            return (
                "Kamu adalah mahasiswa Universitas Mulawarman yang baru saja menggunakan website 'E-Surat 2 FT Unmul'. "
                "Tuliskan 1 kalimat saran perbaikan yang SANGAT SINGKAT, SIMPEL, dan alami (hanya 3 sampai 6 kata saja). "
                "Pilih HANYA SATU dari topik perbaikan berikut tentang website ini untuk dijadikan saran:\n"
                "- Menambahkan batas maksimal file size upload slip UKT/KTM (contoh: 'infokan batas maksimal file upload')\n"
                "- Mengubah warna merah pada tombol 'Kirim Permintaan' (contoh: 'warna tombol kirim ganti biru')\n"
                "- Segera mengaktifkan fitur Permohonan KHS (contoh: 'menu KHS segera diaktifkan')\n"
                "- Mempercepat loading saat submit berkas PDF (contoh: 'loading submit PDF dipercepat')\n"
                "- Menambahkan notifikasi WhatsApp otomatis (contoh: 'tambah notifikasi WhatsApp')\n"
                "- Merapikan tata letak tampilan versi mobile di HP (contoh: 'tampilan mobile dirapikan dikit')\n"
                "Hindari kalimat panjang atau kata penghubung bertumpuk. Tuliskan langsung intinya saja dalam gaya mengetik mahasiswa yang santai, wajar, dan manusiawi. "
                "JANGAN menggunakan kata slang/alay yang berlebihan. "
                "Tuliskan teks polos saja, TANPA tanda bintang (*), tebal, miring, atau format markdown lainnya."
            )

    def generate_text(self, prompt_type: str, max_retries: int = 10) -> str:
        """
        Menghasilkan teks AI unik yang tidak mirip dengan teks sebelumnya.
        Jika API gagal atau menghasilkan duplikat, akan beralih ke generator fallback lokal.
        """
        target_set = self.used_pendapat if prompt_type == "pendapat" else self.used_saran
        prompt = self._get_prompt(prompt_type)
        
        # 1. Coba menggunakan API
        for _ in range(max_retries):
            try:
                response = requests.get(self.api_url, params={"text": prompt}, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    # Ambil field yang kemungkinan dikembalikan oleh API
                    ai_text = data.get("text") or data.get("result") or data.get("response") or data.get("reply") or str(data)
                    ai_text = ai_text.strip().replace('"', '').replace('\u2011', '-')
                    ai_text = re.sub(r'[*_#`~]', '', ai_text)
                    ai_text = ai_text.strip()
                    
                    if ai_text and not is_too_similar(ai_text, target_set):
                        target_set.add(ai_text)
                        return ai_text
            except Exception:
                pass
                
        # 2. Coba menggunakan Fallback Lokal Dinamis jika API gagal/duplikat terus
        for _ in range(30):
            val = get_fallback_text(prompt_type)
            if not is_too_similar(val, target_set):
                target_set.add(val)
                return val
                
        # 3. Fallback absolut (ditambahkan angka acak agar unik)
        val = get_fallback_text(prompt_type) + f" {random.randint(100, 999)}"
        target_set.add(val)
        return val
