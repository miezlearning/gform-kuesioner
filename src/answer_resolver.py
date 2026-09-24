import re
import random
from typing import Dict, Any, List, Optional, Union
from .generators import (
    format_natural_name,
    generate_varied_email,
    generate_scale_answer,
    infer_gender,
    get_natural_semester,
    get_natural_age,
    get_natural_university
)
from .ai_handler import AITextGenerator

class AnswerResolver:
    """
    Engine penentu isi jawaban kuesioner.
    Mendukung mode otomatis cerdas (smart auto-detect) dan kustomisasi aturan per pertanyaan.
    """
    def __init__(self, ai_generator: Optional[AITextGenerator] = None):
        self.ai = ai_generator or AITextGenerator()

    def _resolve_raw_field_value(
        self,
        field: Dict[str, Any],
        student: Dict[str, str],
        profile: str = "puas_rata_rata",
        custom_rule: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Menentukan nilai jawaban untuk satu pertanyaan (field) berdasarkan:
        - Aturan kustom pengguna (jika ada)
        - Data responden (student dari CSV)
        - Profil kepuasan responden
        - Tipe dan opsi pertanyaan
        """
        label = field.get("label", "")
        lbl_lower = label.lower()
        type_code = field.get("type", 0)
        options = field.get("options", []) or []
        
        # 1. JIKA ADA ATURAN KUSTOM DARI PENGGUNA
        if custom_rule and isinstance(custom_rule, dict):
            rule_mode = custom_rule.get("mode", "auto")
            
            if rule_mode == "fixed_option":
                val = custom_rule.get("value")
                if val:
                    return val
                if options:
                    return options[0]
                    
            elif rule_mode == "fixed_text":
                return str(custom_rule.get("value", ""))
                
            elif rule_mode == "random_option":
                if options:
                    if type_code == 4: # Checkbox: pilih 1 atau 2 opsi acak
                        sample_k = min(random.randint(1, 2), len(options))
                        return random.sample(options, sample_k)
                    return random.choice(options)
                return "1"
                
            elif rule_mode == "csv_col":
                col = custom_rule.get("column", "").strip().lower()
                if col in student and student[col]:
                    val = student[col]
                    if col == "nama":
                        return format_natural_name(val)
                    # Jika ada opsi di form, sesuaikan jika memungkinkan
                    if options:
                        for opt in options:
                            if opt.strip().lower() == val.strip().lower():
                                return opt
                    return val
                    
            elif rule_mode == "scale":
                sub_profile = custom_rule.get("profile", "auto")
                if sub_profile == "fixed_5":
                    return "5"
                elif sub_profile == "fixed_4":
                    return "4"
                elif sub_profile == "fixed_3":
                    return "3"
                elif sub_profile == "fixed_2":
                    return "2"
                elif sub_profile == "fixed_1":
                    return "1"
                elif sub_profile == "random_4_5":
                    return str(random.choice([4, 5]))
                elif sub_profile in ["sangat_puas", "puas_rata_rata", "kritis"]:
                    return generate_scale_answer(sub_profile)
                else: # auto
                    return generate_scale_answer(profile)
                    
            elif rule_mode == "email":
                return generate_varied_email(student.get("nama", "user"), student.get("nim", "20"))
                
            elif rule_mode == "ai_review":
                cat = custom_rule.get("category", "pendapat")
                if cat in ("pendapat", "saran"):
                    return self.ai.generate_text(cat, context=label)
                return self.ai.generate_context_text(label)

        # 2. MODE OTOMATIS CERDAS (SMART AUTO-DETECT)
        # ----------------------------------------------------
        # Deteksi Nama Lengkap
        if any(k in lbl_lower for k in ["nama", "nama lengkap", "name"]):
            nama = student.get("nama", "Mahasiswa")
            return format_natural_name(nama)

        # Deteksi NIM
        if any(k in lbl_lower for k in ["nim", "nomor induk", "npm"]):
            return student.get("nim", "")

        # Deteksi Angkatan / Tahun Masuk
        if any(k in lbl_lower for k in ["angkatan", "tahun masuk", "batch"]):
            angkatan_mhs = student.get("angkatan", "")
            if not angkatan_mhs and student.get("nim"):
                angkatan_mhs = f"20{student['nim'][:2]}"
                
            if options:
                # Cari opsi yang cocok persis dengan angkatan mahasiswa
                for opt in options:
                    if opt.strip() == angkatan_mhs:
                        return opt
                # Jika tidak ada yang cocok persis, pilih opsi acak
                return random.choice(options)
            return angkatan_mhs

        # Deteksi Email
        if any(k in lbl_lower for k in ["email", "e-mail", "surel"]):
            return generate_varied_email(student.get("nama", "user"), student.get("nim", "20"))

        # Deteksi Kolom CSV Lainnya (Program Studi, Fakultas, IPK, Perguruan Tinggi, dll.)
        for csv_key, csv_val in student.items():
            if csv_key not in ["nim", "nama", "angkatan"] and csv_val:
                if csv_key in lbl_lower or lbl_lower in csv_key or any(k in lbl_lower for k in ["prodi", "jurusan", "program studi", "fakultas", "universitas", "kampus"]):
                    if options:
                        # 1. Exact match (case insensitive)
                        for opt in options:
                            if opt.strip().lower() == csv_val.strip().lower():
                                return opt
                        
                        # 2. Smart partial / token match (e.g. "Pendidikan Dokter" -> "S1 Kedokteran", "Farmasi" -> "S1 Farmasi")
                        val_clean = csv_val.strip().lower()
                        if "dokter" in val_clean or "kedokteran" in val_clean:
                            val_tokens = ["dokter", "kedokteran"]
                        elif "farmasi" in val_clean or "apoteker" in val_clean:
                            val_tokens = ["farmasi", "apoteker"]
                        elif "keperawatan" in val_clean or "ners" in val_clean:
                            val_tokens = ["keperawatan", "ners", "perawat"]
                        elif "kebidanan" in val_clean or "bidan" in val_clean:
                            val_tokens = ["kebidanan", "bidan"]
                        elif "gizi" in val_clean:
                            val_tokens = ["gizi"]
                        elif "kesehatan masyarakat" in val_clean or "kesmas" in val_clean:
                            val_tokens = ["kesehatan masyarakat", "kesmas"]
                        elif "informatika" in val_clean:
                            val_tokens = ["informatika"]
                        elif "sistem informasi" in val_clean:
                            val_tokens = ["sistem informasi"]
                        else:
                            val_tokens = [t for t in re.split(r'\W+', val_clean) if len(t) > 3]

                        for opt in options:
                            opt_lower = opt.strip().lower()
                            if any(tok in opt_lower for tok in val_tokens):
                                return opt

                        # Jika tidak ada yang cocok, pilih salah satu opsi valid
                        return random.choice(options)
                    return csv_val

        # Deteksi Skala Linier (Type 5)
        if type_code == 5:
            ans = generate_scale_answer(profile)
            if options and ans not in options:
                return options[-1] if profile == "sangat_puas" else options[0]
            return ans

        # Deteksi Pilihan Ganda (Type 2) / Dropdown (Type 3)
        if type_code in (2, 3):
            # A. Jika opsi adalah angka rating (1, 2, 3, 4, 5)
            if options and all(opt.isdigit() for opt in options):
                ans = generate_scale_answer(profile)
                return ans if ans in options else random.choice(options)
                
            # B. Jika opsi adalah tahun angkatan (2021, 2022, 2023, ...)
            if options and any(re.match(r'^20\d{2}$', opt) for opt in options):
                angkatan_mhs = student.get("angkatan", "")
                if angkatan_mhs in options:
                    return angkatan_mhs
                return random.choice(options)
                
            # C. Jika opsi adalah jenis kelamin / gender
            if options and any(g in [o.lower() for o in options] for g in ["laki-laki", "perempuan", "pria", "wanita"]):
                gender_csv = student.get("gender") or student.get("jenis kelamin") or student.get("jk")
                if gender_csv:
                    for opt in options:
                        if gender_csv.lower() in opt.lower():
                            return opt
                # Klasifikasi akurat gender berdasarkan nama mahasiswa Indonesia
                nama_mhs = student.get("nama", "")
                return infer_gender(nama_mhs, options)

            # D. Jika opsi adalah Semester
            if any(k in lbl_lower for k in ["semester"]):
                angkatan_mhs = student.get("angkatan", f"20{student.get('nim', '24')[:2]}")
                return get_natural_semester(angkatan_mhs, options)

            # E. Perguruan Tinggi / Kampus
            if any(k in lbl_lower for k in ["perguruan tinggi", "kampus", "universitas"]):
                return get_natural_university(options)
                
            # F. Jika opsi adalah Skala Likert teks (Sangat Sesuai/Setuju, Sesuai/Setuju, dll.)
            opt_str = " ".join([o.lower() for o in options])
            if any(k in opt_str for k in ["sesuai", "setuju"]):
                # Klasifikasikan opsi berdasarkan sentimen
                pos_high = [o for o in options if "sangat" in o.lower() and not "tidak" in o.lower()]
                pos_med = [o for o in options if ("sesuai" in o.lower() or "setuju" in o.lower()) and "sangat" not in o.lower() and "tidak" not in o.lower() and "kurang" not in o.lower()]
                neutral = [o for o in options if any(n in o.lower() for n in ["netral", "ragu", "cukup"])]
                neg_med = [o for o in options if ("tidak" in o.lower() or "kurang" in o.lower()) and "sangat" not in o.lower()]
                neg_high = [o for o in options if "sangat" in o.lower() and ("tidak" in o.lower() or "kurang" in o.lower())]
                
                if profile == "sangat_puas":
                    if pos_high and random.random() < 0.65:
                        return pos_high[0]
                    if pos_med:
                        return pos_med[0]
                elif profile == "puas_rata_rata":
                    if pos_med and random.random() < 0.60:
                        return pos_med[0]
                    if pos_high and random.random() < 0.50:
                        return pos_high[0]
                    if neutral:
                        return neutral[0]
                else:  # kritis
                    if neg_med and random.random() < 0.50:
                        return neg_med[0]
                    if neutral:
                        return neutral[0]
                    if neg_high and random.random() < 0.30:
                        return neg_high[0]
                return random.choice(options)

            # G. Pertanyaan Kesediaan / Informed Consent (misal: 'Saya Bersedia')
            if any(k in lbl_lower for k in ["bersedia", "persetujuan", "consent", "partisipasi"]):
                for opt in options:
                    if "bersedia" in opt.lower() or "setuju" in opt.lower() or "ya" in opt.lower():
                        return opt
                        
            # H. Opsi umum lainnya: pilih salah satu opsi yang tersedia
            if options:
                return random.choice(options)
            return "1"

        # Deteksi Kotak Centang / Checkbox (Type 4)
        if type_code == 4:
            if options:
                sample_k = min(random.randint(1, 2), len(options))
                return random.sample(options, sample_k)
            return ["1"]

        # Deteksi Teks Paragraf / Teks Singkat (Type 0 atau 1)
        if type_code in (0, 1):
            # A. Usia / Umur
            if any(k in lbl_lower for k in ["usia", "umur", "age"]):
                angkatan_mhs = student.get("angkatan", f"20{student.get('nim', '24')[:2]}")
                return get_natural_age(angkatan_mhs)

            # B. Nomor Handphone / WhatsApp / Kontak
            if any(k in lbl_lower for k in ["handphone", "hp", "telepon", "whatsapp", "wa", "no telp"]):
                prefix = random.choice(["0812", "0813", "0821", "0852", "0853", "0822", "0857"])
                suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
                return f"{prefix}{suffix}"

            # C. Domisili / Kota Asal
            if any(k in lbl_lower for k in ["domisili", "kota", "asal daerah", "tempat tinggal"]):
                return random.choice(["Samarinda", "Balikpapan", "Tenggarong", "Bontang", "Kutai Kartanegara"])

            # D. Suku
            if any(k in lbl_lower for k in ["suku", "etnis"]):
                return random.choice(["Jawa", "Bugis", "Banjar", "Kutai", "Dayak"])

            # E. Perguruan Tinggi / Kampus
            if any(k in lbl_lower for k in ["perguruan tinggi", "kampus", "universitas"]):
                return get_natural_university()

            # F. Semester
            if any(k in lbl_lower for k in ["semester"]):
                angkatan_mhs = student.get("angkatan", f"20{student.get('nim', '24')[:2]}")
                return get_natural_semester(angkatan_mhs)

            # G. Ulasan & Pendapat
            if any(k in lbl_lower for k in ["pendapat", "ulasan", "review", "kesan", "pandangan", "tanggapan"]):
                return self.ai.generate_text("pendapat", context=label)
            if any(k in lbl_lower for k in ["saran", "masukan", "kritik", "rekomendasi", "harapan"]):
                return self.ai.generate_text("saran", context=label)
                
            return self.ai.generate_context_text(label)

        # Fallback terakhir
        if options:
            return random.choice(options)
        return "1"

    def resolve_field_value(
        self,
        field: Dict[str, Any],
        student: Dict[str, str],
        profile: str = "puas_rata_rata",
        custom_rule: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[str]]:
        """
        Menentukan dan memvalidasi nilai jawaban dengan Universal Option Integrity Guard.
        Menjamin bahwa untuk tipe pilihan ganda (2) dan dropdown (3), nilai yang dikirimkan
        SELALU merupakan salah satu opsi valid yang diterima Google Forms.
        """
        raw_val = self._resolve_raw_field_value(field, student, profile, custom_rule)

        type_code = field.get("type", 0)
        options = field.get("options", []) or []

        # 1. VALIDASI KOTAK CENTANG (CHECKBOX - TYPE 4)
        if type_code == 4 and options:
            if not isinstance(raw_val, list):
                raw_val = [raw_val]
            valid_vals = [v for v in raw_val if v in options]
            return valid_vals if valid_vals else [options[0]]

        # 2. VALIDASI PILIHAN GANDA (TYPE 2) & DROPDOWN (TYPE 3)
        if type_code in (2, 3) and options:
            if isinstance(raw_val, list):
                raw_val = raw_val[0] if raw_val else options[0]
            val_str = str(raw_val).strip()

            # A. Kecocokan persis
            if val_str in options:
                return val_str

            # B. Kecocokan case-insensitive
            for opt in options:
                if opt.strip().lower() == val_str.lower():
                    return opt

            # C. Pencocokan kata kunci pintar (Fuzzy / Token matching)
            val_lower = val_str.lower()
            if "dokter" in val_lower or "kedokteran" in val_lower:
                matched = next((o for o in options if "dokter" in o.lower() or "kedokteran" in o.lower()), None)
                if matched:
                    return matched
            elif "farmasi" in val_lower or "apoteker" in val_lower:
                matched = next((o for o in options if "farmasi" in o.lower() or "apoteker" in o.lower()), None)
                if matched:
                    return matched
            elif "keperawatan" in val_lower or "perawat" in val_lower or "ners" in val_lower:
                matched = next((o for o in options if "keperawatan" in o.lower() or "perawat" in o.lower() or "ners" in o.lower()), None)
                if matched:
                    return matched
            elif "kebidanan" in val_lower or "bidan" in val_lower:
                matched = next((o for o in options if "kebidanan" in o.lower() or "bidan" in o.lower()), None)
                if matched:
                    return matched
            elif "gizi" in val_lower:
                matched = next((o for o in options if "gizi" in o.lower()), None)
                if matched:
                    return matched
            elif "kesehatan masyarakat" in val_lower or "kesmas" in val_lower:
                matched = next((o for o in options if "kesehatan masyarakat" in o.lower() or "kesmas" in o.lower()), None)
                if matched:
                    return matched
            elif "mulawarman" in val_lower:
                matched = next((o for o in options if "mulawarman" in o.lower()), None)
                if matched:
                    return matched
            elif "semester" in val_lower:
                sem_digits = re.findall(r'\d+', val_lower)
                if sem_digits:
                    matched = next((o for o in options if sem_digits[0] in o), None)
                    if matched:
                        return matched
            else:
                tokens = [t for t in re.split(r'\W+', val_lower) if len(t) > 2]
                matched = next((o for o in options if any(t in o.lower() for t in tokens)), None)
                if matched:
                    return matched

            # D. Fallback mutlak: pilih opsi pertama yang valid di Google Form
            return options[0]

        return raw_val

    def resolve_all_pages(
        self,
        pages: List[List[Dict[str, Any]]],
        student: Dict[str, str],
        profile: str,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Menghasilkan seluruh nilai jawaban untuk setiap halaman form.
        """
        custom_rules = custom_rules or {}
        all_pages_result = []
        
        for page in pages:
            page_result = []
            for field in page:
                entry_id = str(field["entry_id"])
                rule = custom_rules.get(entry_id)
                value = self.resolve_field_value(field, student, profile, rule)
                page_result.append({
                    "entry_id": entry_id,
                    "value": value,
                    "label": field.get("label", ""),
                    "type": field.get("type", 0)
                })
            all_pages_result.append(page_result)
            
        return all_pages_result
