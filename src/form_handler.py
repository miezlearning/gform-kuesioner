import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple

TYPE_NAMES = {
    0: "Teks Singkat",
    1: "Paragraf",
    2: "Pilihan Ganda",
    3: "Dropdown",
    4: "Kotak Centang",
    5: "Skala Linier",
    7: "Kisi Pilihan Ganda",
    9: "Tanggal",
    10: "Waktu"
}

def suggest_rule(label: str, type_code: int, options: List[str]) -> Dict[str, Any]:
    """Menentukan rekomendasi aturan jawaban secara otomatis berdasarkan judul & tipe pertanyaan."""
    lbl = label.lower()
    if any(k in lbl for k in ["nama", "nama lengkap", "name"]):
        return {"mode": "csv_col", "column": "nama"}
    if any(k in lbl for k in ["nim", "nomor induk", "npm"]):
        return {"mode": "csv_col", "column": "nim"}
    if any(k in lbl for k in ["angkatan", "tahun masuk", "batch"]):
        return {"mode": "csv_col", "column": "angkatan"}
    if any(k in lbl for k in ["email", "e-mail"]):
        return {"mode": "email"}
    if any(k in lbl for k in ["program studi", "prodi", "jurusan"]):
        return {"mode": "csv_col", "column": "program studi"}
    if any(k in lbl for k in ["fakultas", "faculty"]):
        return {"mode": "csv_col", "column": "fakultas"}
    if any(k in lbl for k in ["jenis kelamin", "gender", "kelamin"]):
        return {"mode": "random_option"}
    if type_code == 5:
        return {"mode": "scale", "profile": "auto"}
    if type_code in (2, 3):
        # Cek jika opsi adalah angka skala (1, 2, 3, 4, 5)
        if options and all(opt.isdigit() for opt in options):
            return {"mode": "scale", "profile": "auto"}
        # Cek jika opsi adalah tahun angkatan (2021, 2022, ...)
        if options and any(re.match(r'^20\d{2}$', opt) for opt in options):
            return {"mode": "csv_col", "column": "angkatan"}
        return {"mode": "random_option"}
    if type_code == 4:
        return {"mode": "random_option"}
    if type_code in (0, 1):
        if any(k in lbl for k in ["pendapat", "ulasan", "review", "kesan", "tanggapan", "penilaian"]):
            return {"mode": "ai_review", "category": "pendapat"}
        if any(k in lbl for k in ["saran", "masukan", "kritik", "rekomendasi", "feedback"]):
            return {"mode": "ai_review", "category": "saran"}
        return {"mode": "auto"}
    return {"mode": "auto"}


class GoogleFormHandler:
    """
    Mengelola interaksi dengan Google Forms:
    - Ekstraksi struktur lengkap pertanyaan, opsi, skala, section, dan session token.
    - Pembentukan data partialResponse untuk multi-page form.
    - Pengiriman payload respon via HTTP POST.
    """
    def __init__(self, form_url: str):
        self.form_url = form_url.strip()
        # Normalisasi URL ke format /viewform dan /formResponse
        if "/formResponse" in self.form_url:
            self.form_url = self.form_url.replace("/formResponse", "/viewform")
        self.submit_url = self.form_url.replace("/viewform", "/formResponse")

    def extract_structure(self) -> Optional[Dict[str, Any]]:
        """
        Mengekstrak struktur lengkap Google Form secara otomatis:
        judul form, section/halaman, seluruh pertanyaan beserta tipe dan opsi,
        session data (fbzx, fvv), dan halaman email.
        """
        print(f"Sedang mengekstrak struktur Google Form: {self.form_url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(self.form_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Gagal memuat form. Kode Status: {response.status_code}")
                return None
                
            html = response.text
            match = re.search(r'FB_PUBLIC_LOAD_DATA_ = (.*?);', html, flags=re.S)
            if not match:
                print("Gagal menemukan struktur data form. Pastikan link Google Form Anda benar dan dapat diakses publik.")
                return None
                
            raw_data = json.loads(match.group(1))
            
            # Ambil judul dan deskripsi form
            form_title = ""
            form_description = ""
            try:
                if len(raw_data) > 1 and len(raw_data[1]) > 8 and raw_data[1][8]:
                    form_title = str(raw_data[1][8]).strip()
                if len(raw_data) > 1 and len(raw_data[1]) > 0 and raw_data[1][0]:
                    form_description = str(raw_data[1][0]).strip()
            except Exception:
                pass
                
            if not form_title:
                soup_title = BeautifulSoup(html, "html.parser").find("title")
                form_title = soup_title.text.replace(" - Google Forms", "").strip() if soup_title else "Formulir Google"

            questions_list = raw_data[1][1] if len(raw_data) > 1 and len(raw_data[1]) > 1 and raw_data[1][1] else []
            
            pages: List[List[Dict[str, Any]]] = []
            flat_questions: List[Dict[str, Any]] = []
            current_page_fields: List[Dict[str, Any]] = []
            current_section_title = "Bagian 1"
            page_index = 0
            
            for item in questions_list:
                try:
                    type_code = item[3]
                    
                    if type_code == 8:
                        # Section header = batas halaman baru
                        if current_page_fields:
                            pages.append(current_page_fields)
                            page_index += 1
                        current_page_fields = []
                        current_section_title = item[1].strip() if item[1] else f"Bagian {page_index + 1}"
                        continue
                    
                    label = item[1].strip() if item[1] else ""
                    desc = item[2].strip() if len(item) > 2 and item[2] else ""
                    sub = item[4] if len(item) > 4 else None
                    if not sub:
                        continue
                    
                    # Cek tipe 7 (Grid / Kisi) yang memiliki multiple sub-items
                    if type_code == 7 and len(sub) > 1:
                        for row_sub in sub:
                            row_entry_id = str(row_sub[0])
                            row_label = f"{label} - {row_sub[3][0]}" if len(row_sub) > 3 and row_sub[3] else label
                            col_options = [opt[0] for opt in row_sub[1] if opt and len(opt) > 0 and opt[0] is not None] if len(row_sub) > 1 and row_sub[1] else []
                            is_req = bool(row_sub[2]) if len(row_sub) > 2 and row_sub[2] is not None else False
                            
                            q_info = {
                                "entry_id": row_entry_id,
                                "label": row_label,
                                "description": desc,
                                "type": 2, # Diperlakukan sebagai radio per baris
                                "type_name": "Pilihan Ganda (Baris Kisi)",
                                "options": col_options,
                                "scale_bounds": None,
                                "required": is_req,
                                "section_title": current_section_title,
                                "page_index": page_index,
                                "suggested_rule": suggest_rule(row_label, 2, col_options)
                            }
                            current_page_fields.append(q_info)
                            flat_questions.append(q_info)
                        continue
                    
                    # Pertanyaan standar (0, 1, 2, 3, 4, 5, dll.)
                    entry_id = str(sub[0][0])
                    options = []
                    if len(sub[0]) > 1 and sub[0][1]:
                        options = [str(opt[0]) for opt in sub[0][1] if opt and len(opt) > 0 and opt[0] is not None]
                    
                    required = bool(sub[0][2]) if len(sub[0]) > 2 and sub[0][2] is not None else False
                    
                    scale_bounds = None
                    if type_code == 5:
                        scale_labels = sub[0][3] if len(sub[0]) > 3 and sub[0][3] else ["", ""]
                        min_lbl = scale_labels[0] if len(scale_labels) > 0 and scale_labels[0] else ""
                        max_lbl = scale_labels[1] if len(scale_labels) > 1 and scale_labels[1] else ""
                        min_val = options[0] if options else "1"
                        max_val = options[-1] if options else "5"
                        scale_bounds = {
                            "min": min_val,
                            "max": max_val,
                            "min_label": min_lbl,
                            "max_label": max_lbl
                        }
                    
                    q_info = {
                        "entry_id": entry_id,
                        "label": label,
                        "description": desc,
                        "type": type_code,
                        "type_name": TYPE_NAMES.get(type_code, f"Tipe {type_code}"),
                        "options": options,
                        "scale_bounds": scale_bounds,
                        "required": required,
                        "section_title": current_section_title,
                        "page_index": page_index,
                        "suggested_rule": suggest_rule(label, type_code, options)
                    }
                    current_page_fields.append(q_info)
                    flat_questions.append(q_info)
                    
                except (IndexError, TypeError, KeyError) as e:
                    continue
            
            # Masukkan halaman terakhir jika ada pertanyaan
            if current_page_fields:
                pages.append(current_page_fields)
            
            # Jika form tidak memiliki section pemisah, minimal 1 halaman
            if not pages and current_page_fields:
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
            
            num_pages = len(pages)
            if has_email_page:
                num_pages += 1
                
            page_history = ",".join(str(i) for i in range(max(1, num_pages)))
            
            total_fields = len(flat_questions)
            print(f"Berhasil mendeteksi {total_fields} pertanyaan dalam {len(pages)} halaman.")
            print(f"Judul Form: '{form_title}'")
            print("-" * 50)
            
            return {
                "form_title": form_title,
                "form_description": form_description,
                "pages": pages,
                "questions": flat_questions,
                "fbzx": fbzx,
                "fvv": fvv,
                "has_email_page": has_email_page,
                "page_history": page_history,
                "num_pages": len(pages)
            }
            
        except Exception as e:
            print(f"Terjadi error saat ekstraksi struktur form: {e}")
            return None

    @staticmethod
    def build_partial_response(pages_data: List[Tuple[str, Any]], fbzx: str, email: str) -> str:
        """
        Membangun JSON parameter 'partialResponse' untuk form multi-page.
        Mendukung nilai tunggal maupun majemuk (list checkbox).
        """
        entries = []
        for entry_id, value in pages_data:
            num_id = int(entry_id) if str(entry_id).isdigit() else entry_id
            if isinstance(value, list):
                entries.append([None, num_id, [str(v) for v in value], 0])
            else:
                entries.append([None, num_id, [str(value)], 0])
        
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
            response = requests.post(self.submit_url, data=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                success = (
                    "freebirdFormviewerViewResponseConfirmationMessage" in response.text or
                    "Jawaban Anda telah direkam" in response.text or
                    "Tanggapan Anda telah dicatat" in response.text or
                    "Your response has been recorded" in response.text
                )
                if success:
                    return True, "Sukses mengirim respon"
                else:
                    return False, "Dikirim tapi mungkin ada validasi error pada form"
            else:
                return False, f"Gagal mengirim. Kode Status HTTP: {response.status_code}"
        except Exception as e:
            return False, f"Error saat mengirim data: {e}"
