import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple

class GoogleFormHandler:
    """
    Mengelola interaksi dengan Google Forms, mulai dari parsing struktur otomatis,
    pembentukan data partialResponse (multi-page), dan pengiriman data (submit).
    """
    def __init__(self, form_url: str):
        self.form_url = form_url
        # Ubah URL dari viewform ke formResponse untuk pengiriman data
        self.submit_url = form_url.replace("/viewform", "/formResponse")

    def extract_structure(self) -> Optional[Dict[str, Any]]:
        """
        Mengekstrak struktur lengkap Google Form secara otomatis, mendeteksi halaman (page),
        entry ID pertanyaan, session data (fbzx, fvv), dan halaman email bawaan Google.
        """
        print("Sedang mengambil struktur Google Form secara otomatis...")
        try:
            response = requests.get(self.form_url, timeout=15)
            if response.status_code != 200:
                print(f"Gagal memuat form. Kode Status: {response.status_code}")
                return None
                
            html = response.text
            match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
            if not match:
                print("Gagal menemukan struktur data form. Pastikan link gform Anda benar.")
                return None
                
            raw_data = json.loads(match.group(1))
            questions_list = raw_data[1][1]
            
            pages: List[List[Dict[str, Any]]] = []
            current_page_fields: List[Dict[str, Any]] = []
            
            for item in questions_list:
                try:
                    type_code = item[3]
                    if type_code == 8:
                        # Section header = mulai halaman baru
                        if current_page_fields:
                            pages.append(current_page_fields)
                        current_page_fields = []
                    else:
                        label = item[1].strip()
                        entry_id = item[4][0][0]  # Numeric ID tanpa prefix "entry."
                        current_page_fields.append({
                            "label": label,
                            "entry_id": entry_id,
                            "type": type_code  # 0=text, 1=textarea, 2=radio, 5=scale
                        })
                except (IndexError, TypeError):
                    continue
            
            # Simpan halaman terakhir jika ada
            if current_page_fields:
                pages.append(current_page_fields)
            
            # Ekstrak data session (fbzx, fvv) dari HTML
            soup = BeautifulSoup(html, "html.parser")
            fbzx_input = soup.find("input", {"name": "fbzx"})
            fbzx = fbzx_input.get("value") if fbzx_input else ""
            
            fvv_input = soup.find("input", {"name": "fvv"})
            fvv = fvv_input.get("value") if fvv_input else "1"
            
            # Deteksi halaman email bawaan Google
            has_email_page = False
            try:
                email_setting = raw_data[1][10][3]
                has_email_page = email_setting is not None and email_setting > 0
            except (IndexError, TypeError):
                has_email_page = soup.find("input", {"name": "emailAddress"}) is not None
            
            # Hitung total halaman (termasuk halaman email sebagai Page 0)
            num_pages = len(pages)
            if has_email_page:
                num_pages += 1
                
            page_history = ",".join(str(i) for i in range(num_pages))
            
            # Log struktur form hasil scrapping
            total_fields = sum(len(p) for p in pages)
            print(f"Berhasil mendeteksi {total_fields} pertanyaan dalam {len(pages)} halaman.")
            if has_email_page:
                print("  Page 0: Email (bawaan Google Forms)")
            for pi, page in enumerate(pages):
                page_num = pi + 1 if has_email_page else pi
                print(f"  Page {page_num}: {len(page)} pertanyaan")
                for field in page:
                    print(f"    - entry.{field['entry_id']} -> '{field['label']}' (type={field['type']})")
            print("-" * 50)
            
            return {
                "pages": pages,
                "fbzx": fbzx,
                "fvv": fvv,
                "has_email_page": has_email_page,
                "page_history": page_history,
            }
            
        except Exception as e:
            print(f"Terjadi error saat ekstraksi struktur form: {e}")
            return None

    @staticmethod
    def build_partial_response(pages_data: List[Tuple[int, Any]], fbzx: str, email: str) -> str:
        """
        Membangun JSON parameter 'partialResponse' untuk form multi-page.
        Berisi data halaman 1 s/d N-1 (seluruh halaman sebelum halaman terakhir).
        """
        entries = []
        for entry_id, value in pages_data:
            entries.append([None, entry_id, [str(value)], 0])
        
        partial = [
            entries,
            None,
            fbzx,
            None,
            None,
            None,
            email,
            1
        ]
        return json.dumps(partial, separators=(',', ':'))

    def submit(self, payload: Dict[str, Any], referer_url: Optional[str] = None) -> Tuple[bool, str]:
        """
        Mengirim payload data respon ke Google Forms via HTTP POST.
        Mengembalikan status keberhasilan (True/False) dan pesan detail.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://docs.google.com",
            "Referer": referer_url or self.submit_url,
        }
        
        try:
            response = requests.post(self.submit_url, data=payload, headers=headers)
            if response.status_code == 200:
                # Verifikasi respons dari html balikan Google Forms
                success = (
                    "freebirdFormviewerViewResponseConfirmationMessage" in response.text or
                    "Jawaban Anda telah direkam" in response.text
                )
                if success:
                    return True, "Sukses mengirim respon"
                else:
                    return False, "Dikirim tapi mungkin ada validasi error di form"
            else:
                return False, f"Gagal mengirim. Kode Status HTTP: {response.status_code}"
        except Exception as e:
            return False, f"Error saat mengirim data: {e}"
