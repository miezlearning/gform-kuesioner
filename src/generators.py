import random
import re
from typing import Set, List, Optional

def format_natural_name(nama: str) -> str:
    """
    Format nama agar terlihat bervariasi seperti diketik manual 
    oleh orang awam (Title Case, lower case, atau UPPER CASE).
    """
    nama_clean = nama.strip()
    style = random.choices(
        ["title", "lower", "upper"],
        weights=[75, 15, 10]
    )[0]
    
    if style == "title":
        return nama_clean.title()
    elif style == "lower":
        return nama_clean.lower()
    else:
        return nama_clean.upper()


# Kumpulan kata kunci nama Indonesia untuk klasifikasi gender yang sinkron dengan PDDIKTI
FEMALE_NAME_TOKENS = {
    'putri', 'nabilah', 'dewi', 'intan', 'widya', 'ayu', 'fincy', 'gloria', 
    'angelina', 'bilqis', 'azira', 'nadia', 'niky', 'jenita', 'rusdiana', 
    'azzhahra', 'ghesya', 'rhegyta', 'rahmah', 'audia', 'anggraini', 'nathasia', 
    'umami', 'nuraini', 'faradina', 'pertiwi', 'anisa', 'annisa', 'safitri', 
    'lestari', 'wulandari', 'siti', 'nur', 'indah', 'fitri', 'rahma', 'zahra', 
    'tiara', 'maharani', 'novita', 'lia', 'nia', 'ria', 'maya', 'sari', 'mega', 
    'ratna', 'shinta', 'sinta', 'amelia', 'nabila', 'salma', 'nadira', 'khansa', 
    'cantika', 'aulia', 'firda', 'mutiara', 'marwa', 'alfara', 'alika', 'renaya',
    'astuti', 'manulang', 'aisyah', 'alya', 'diana', 'hana', 'hasna', 'nurul',
    'zahira', 'fadila', 'syifa', 'amalia', 'karina', 'nadya', 'tania', 'destiana',
    'kariani', 'cahyani', 'suhartati', 'shofrina', 'sabina', 'aurelia', 'salsabiila',
    'aprisa', 'dengen'
}

MALE_NAME_TOKENS = {
    'muhammad', 'mochammad', 'muh', 'mhd', 'm', 'ahmad', 'achmad', 'akhmad', 'dwiki', 
    'tedy', 'haykal', 'makhmud', 'andi', 'fachry', 'alam', 'tengko', 'syafiq', 
    'hafizh', 'farizi', 'zeydan', 'fazle', 'mawla', 'rusdiansyah', 'ajiva', 
    'alank', 'zulfikar', 'aryawinata', 'elfin', 'sinaga', 'putra', 'ilham', 
    'rizky', 'rizki', 'bagus', 'fajar', 'dimas', 'aditya', 'yoga', 'farhan', 
    'arya', 'arief', 'arifin', 'budi', 'eko', 'agung', 'hendra', 'wahyu', 
    'bayu', 'dani', 'deni', 'faisal', 'hafiz', 'hasan', 'iqbal', 'irfan', 
    'reza', 'satria', 'taufiq', 'yusuf', 'syahrul', 'alif', 'fathur', 'tegar', 
    'bintang', 'raihan', 'faiz', 'gilang', 'pratama', 'aryanda', 'azhari', 
    'setiandra', 'aprilian', 'al-fatih', 'fatih', 'zifa', 'akbar', 'darmawan',
    'kurniawan', 'saputra', 'ramadhan', 'hidayat', 'firmansyah', 'ananda', 'syahputra',
    'rifan', 'fathoni', 'setyawan', 'abdurrosyid', 'yudha', 'rangga', 'fitriansyah'
}

def infer_gender(name: str, options: Optional[List[str]] = None) -> str:
    """
    Menentukan jenis kelamin berdasarkan nama mahasiswa Indonesia secara akurat
    sesuai data PDDIKTI, dan menyesuaikan dengan format opsi di form.
    """
    cleaned = name.lower().replace('.', ' ').replace('-', ' ')
    words = cleaned.split()
    
    gender_detected = "Laki-Laki"
    
    if words and words[0] in {'muhammad', 'mochammad', 'mhd', 'm', 'ahmad', 'achmad', 'akhmad'}:
        gender_detected = "Laki-Laki"
    elif words and words[0] in {'siti', 'nur', 'anisa', 'annisa'}:
        gender_detected = "Perempuan"
    else:
        f_count = sum(1 for w in words if w in FEMALE_NAME_TOKENS)
        m_count = sum(1 for w in words if w in MALE_NAME_TOKENS)
        
        if f_count > m_count:
            gender_detected = "Perempuan"
        elif m_count > f_count:
            gender_detected = "Laki-Laki"
        elif any(w.endswith(('wati', 'putri', 'dini', 'tina', 'tini', 'liana', 'riani', 'ani')) for w in words):
            gender_detected = "Perempuan"
        elif any(w.endswith(('putra', 'syah', 'jaya', 'tama', 'wibowo', 'awan')) for w in words):
            gender_detected = "Laki-Laki"
        else:
            gender_detected = "Perempuan" if words and words[-1].endswith(('a', 'i', 'ah', 'ty', 'ti')) else "Laki-Laki"

    # Jika form memiliki opsi pilihan (misal: 'Laki-Laki' atau 'Laki-laki' atau 'Pria')
    if options:
        for opt in options:
            opt_lower = opt.lower()
            if gender_detected == "Laki-Laki" and (opt_lower in ["laki-laki", "laki - laki", "pria", "l"]):
                return opt
            elif gender_detected == "Perempuan" and (opt_lower in ["perempuan", "wanita", "p"]):
                return opt
        return options[0]
        
    return gender_detected


def get_natural_semester(angkatan: str, options: Optional[List[str]] = None) -> str:
    """
    Menghitung semester yang sinkron dengan angkatan mahasiswa sesuai kalender akademik PDDIKTI:
    - 2025 -> Semester 1 / 2
    - 2024 -> Semester 3 / 4
    - 2023 -> Semester 5 / 6
    - 2022 -> Semester 7 / 8
    - 2021 -> Semester 8 / Akhir
    """
    try:
        yr = int(angkatan) if str(angkatan).isdigit() else 2024
    except Exception:
        yr = 2024

    mapping = {
        2025: [1, 2],
        2024: [3, 4],
        2023: [5, 6],
        2022: [7, 8],
        2021: [8]
    }
    possible_semesters = mapping.get(yr, [3, 4])
    chosen_num = random.choice(possible_semesters)

    if options:
        # Cari opsi yang mengandung angka semester yang tepat
        for num in possible_semesters:
            for opt in options:
                if str(num) in opt:
                    return opt
        return options[0]

    return f"Semester {chosen_num}"


def get_natural_age(angkatan: str) -> str:
    """
    Menghitung usia mahasiswa S1 yang realistis (18-24) berdasarkan angkatan.
    """
    try:
        yr = int(angkatan) if str(angkatan).isdigit() else 2024
    except Exception:
        yr = 2024

    base_ages = {
        2025: [18, 19],
        2024: [19, 20],
        2023: [20, 21],
        2022: [21, 22],
        2021: [22, 23]
    }
    ages = base_ages.get(yr, [19, 20, 21])
    return str(random.choice(ages))


def get_natural_university(options: Optional[List[str]] = None) -> str:
    """
    Mahasiswa di dataset berasal dari Universitas Mulawarman.
    Jika opsi memuat Universitas Mulawarman, prioritaskan opsi tersebut.
    """
    if options:
        for opt in options:
            if "mulawarman" in opt.lower() or "unmul" in opt.lower():
                return opt
        return options[0]
    return "Universitas Mulawarman"


def generate_scale_answer(profile: str = "puas_rata_rata") -> str:
    """
    Menghasilkan nilai skala WebQual (1 sampai 5) 
    yang disesuaikan dengan profil kepuasan responden.
    """
    if profile == "sangat_puas":
        # Cenderung memberikan nilai 4 atau 5
        return str(random.choices([1, 2, 3, 4, 5], weights=[0, 1, 9, 35, 55])[0])
    elif profile == "kritis":
        # Cenderung memberikan nilai 2, 3, atau 4
        return str(random.choices([1, 2, 3, 4, 5], weights=[10, 30, 45, 12, 3])[0])
    else: # puas_rata_rata
        # Cenderung memberikan nilai 3 atau 4
        return str(random.choices([1, 2, 3, 4, 5], weights=[1, 4, 25, 55, 15])[0])


def generate_varied_email(nama: str, nim: str) -> str:
    """
    Menghasilkan alamat email fiktif dengan gaya penulisan yang bervariasi
    (nama standar, username game/nickname, inisial, singkatan).
    """
    # Bersihkan nama dari spasi ganda, karakter aneh, dsb.
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', nama).lower()
    parts = [p for p in clean_name.split() if p]
    if not parts:
        parts = ["user"]
        
    prefix_tahun = str(nim)[:2] if nim else str(random.randint(15, 25))
    
    # Elemen untuk nickname email
    game_prefixes = ["shadow", "neon", "vortex", "cyber", "hyper", "zen", "el", "king", "lord", "pro", "racer", "hunter", "toxic", "phantom", "alpha", "omega", "silent", "dark", "frost"]
    game_suffixes = ["gg", "pro", "gaming", "ml", "ff", "pubg", "boy", "girl", "xd", "god", "z", "xz", "99", "88", "123", "404", "lol"]
    
    email_types = [
        # 1. Variasi nama standar (misal: rian.mhd24, mhd_rian)
        lambda: f"{'.'.join(parts)}{prefix_tahun}",
        lambda: f"{'_'.join(parts)}{random.choice(['', prefix_tahun])}",
        lambda: f"{parts[-1]}.{parts[0]}{prefix_tahun}",
        # 2. Gaya nickname prefix (misal: shadow.rian, neon_rian24)
        lambda: f"{random.choice(game_prefixes)}{random.choice(['.', '_'])}{parts[0]}{random.choice(['', prefix_tahun])}",
        # 3. Gaya nickname suffix (misal: rian_gaming, rian_ml99)
        lambda: f"{parts[0]}{random.choice(['.', '_'])}{random.choice(game_suffixes)}",
        # 4. Kombinasi keduanya (misal: shadow_rian_gg)
        lambda: f"{random.choice(game_prefixes)}_{parts[0]}_{random.choice(game_suffixes)}",
        # 5. Singkatan inisial (misal: mr24_gaming)
        lambda: f"{''.join([p[0] for p in parts])}{prefix_tahun}_{random.choice(game_suffixes)}",
        # 6. Gamer tag random
        lambda: f"{parts[0]}{random.choice(['x', 'z', '_tzy', '_sanz', '_sky'])}{random.choice(['', prefix_tahun])}"
    ]
    
    email_prefix = random.choice(email_types)()
    email_prefix = re.sub(r'[._]{2,}', '_', email_prefix)
    email_prefix = email_prefix.strip('._')
    
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "ymail.com"]
    domain = random.choice(domains)
    
    return f"{email_prefix}@{domain}"


def is_too_similar(text: str, target_set: Set[str], word_threshold: int = 3, overlap_threshold: float = 0.55) -> bool:
    """
    Mendeteksi kemiripan kata di awal (prefix) dan overlap kata (Jaccard Similarity)
    dengan teks yang sudah pernah digunakan agar jawaban kuesioner tidak terlihat seragam.
    """
    clean_text = re.sub(r'[^\w\s]', '', text.lower()).strip()
    text_words = [w for w in clean_text.split() if w]
    if not text_words:
        return False
        
    if len(text_words) < word_threshold:
        return text in target_set
        
    prefix = " ".join(text_words[:word_threshold])
    
    for existing in target_set:
        clean_existing = re.sub(r'[^\w\s]', '', existing.lower()).strip()
        existing_words = [w for w in clean_existing.split() if w]
        
        # 1. Cek prefix match (3 kata pertama sama persis)
        if len(existing_words) >= word_threshold:
            existing_prefix = " ".join(existing_words[:word_threshold])
            if prefix == existing_prefix:
                return True
                
        # 2. Cek overlap Jaccard Similarity
        intersection = set(text_words) & set(existing_words)
        union = set(text_words) | set(existing_words)
        jaccard = len(intersection) / len(union) if union else 0
        if jaccard > overlap_threshold:
            return True
            
    return False


# =========================================================================
# Bank Tanggapan Mahasiswa / Gaya Santai Sosmed (Natural, Tidak Baku, Anti-Alay)
# =========================================================================

STUDENT_PHRASES = {
    "pendapat": [
        "Overall udah bagus banget sih, ga ribet pas dipake.",
        "Tampilannya simpel dan bersih, enak dilihat di hp.",
        "Udah oke kok, alurnya jelas dari awal sampai akhir.",
        "Cukup ngebantu banget buat mahasiswa, prosesnya jadi lebih cepet.",
        "Bagus, loadingnya juga lumayan cepet ga bikin nunggu lama.",
        "Sejauh ini puas sih, ga nemu kendala yang berarti.",
        "Navigasinya gampang dipahami, tampilannya juga responsif.",
        "Alurnya sat set dan to the point, ga bertele-tele.",
        "Udah cukup memuaskan dan fiturnya sesuai kebutuhan.",
        "Keren sih, desainnya modern dan gampang diakses.",
        "Udah mantap banget, ga ada keluhan sejauh ini.",
        "Bagus kok, sistemnya lancar pas dicoba tadi.",
        "Simpel dan praktis banget buat dipake sehari-hari.",
        "Menurutku udah sangat baik dan mudah dipahami instruksinya.",
        "Pengalaman penggunaannya nyaman, informasinya lengkap.",
        "Tampilannya minimalis, ga bikin pusing pas nyari menu.",
        "Semuanya berjalan lancar, ga ada error sama sekali."
    ],
    "saran": [
        "Semoga ke depannya servernya makin stabil pas jam-jam sibuk.",
        "Bisa ditambahin panduan singkat atau petunjuk biar ga bingung.",
        "Mungkin tampilannya bisa dibikin makin responsif lagi pas dibuka di hp.",
        "Tolong dipertahanin aja performanya yang sekarang, udah mantap kok.",
        "Kalau bisa tombol aksinya dibuat lebih keliatan atau kontras dikit.",
        "Loadingnya semoga bisa dipercepat lagi dikit biar makin sat set.",
        "Bisa diperbanyak sosialisasi infonya di medsos biar ga ketinggalan info.",
        "Udah bagus banget, semoga bisa terus dipertahanin dan diupdate rutin.",
        "Mungkin bisa ditambahin fitur notifikasi biar infonya langsung masuk.",
        "Sejauh ini udah oke, tinggal pertahanin aja kualitas layanannya.",
        "Desainnya kalau bisa dibuat makin modern dan minimalis lagi.",
        "Petunjuk pengisian di beberapa bagian bisa diperjelas dikit lagi yaa.",
        "Semoga ke depannya makin banyak pilihan fitur yang mempermudah mahasiswa."
    ],
    "akademik": [
        "Kuncinya konsisten bagi waktu antara kuliah sama istirahat aja sih.",
        "Motivasi terbesarku pengen cepat lulus tepat waktu dan banggain ortu.",
        "Tantangannya lebih ke manajemen waktu kalau pas tugas lagi numpuk barengan.",
        "Sempat ngerasa jenuh, tapi ya tetap dijalanin pelan-pelan sampai kelar.",
        "Sering diskusi bareng temen sekelas biar lebih paham materi yang susah.",
        "Fokus ke target jangka panjang biar ga gampang down pas nilai kurang memuaskan.",
        "Selalu usahain ngerjain tugas dari jauh-jauh hari biar ga panik pas deadline.",
        "Belajar adaptasi sama ritme kuliah aja sih, lama-lama juga terbiasa.",
        "Tetap semangat jalanin perkuliahan walaupun kadang materinya lumayan berat.",
        "Usahain aktif di kelas dan jangan malu buat nanya kalau belum ngerti.",
        "Manfaatin waktu luang buat istirahat biar ga gampang burnout pas masa ujian.",
        "Saling support sama temen-temen satu angkatan ngebantu banget jaga motivasi.",
        "Mencoba eksplor banyak hal baru di kampus biar nambah wawasan dan pengalaman.",
        "Penting banget punya lingkungan temen yang suportif pas lagi ngerjain tugas kuliah."
    ],
    "kendala": [
        "Sejauh ini belum ada kendala yang berarti sih, semuanya masih aman.",
        "Paling kendalanya di koneksi internet aja pas lagi di kosan.",
        "Tantangannya cuma bagi waktu pas tugas kuliah lagi numpuk barengan.",
        "Aman aja sih, kalau ada kesulitan biasanya langsung tanya temen atau dosen.",
        "Awalnya sempat kaget sama beban tugasnya, tapi sekarang udah mulai terbiasa.",
        "Belum nemu masalah yang serius, alhamdulillah masih lancar-lancar aja.",
        "Kendala kecil paling di jadwal kelas yang kadang bentrok, tapi masih aman."
    ],
    "umum": [
        "Sejauh ini semuanya udah berjalan dengan baik dan lancar.",
        "Menurutku udah sesuai sama kebutuhan mahasiswa saat ini.",
        "Aman aja sih, ga ada catatan khusus.",
        "Udah cukup jelas dan mudah diikuti petunjuknya.",
        "Semoga bisa terus konsisten dan berkembang lebih baik lagi.",
        "Secara keseluruhan pengalamannya positif dan sangat membantu."
    ]
}

def apply_natural_youth_style(text: str) -> str:
    """
    Menyesuaikan gaya penulisan agar bervariasi secara natural seperti mahasiswa:
    - 75% huruf besar di awal kalimat standar
    - 25% huruf kecil santai khas medsos/chat
    - 20% tanpa titik di akhir kalimat
    """
    text = text.strip()
    if not text:
        return text
        
    # Kadang tanpa tanda titik di akhir (khas gaya ketik chat/form cepat)
    if random.random() < 0.20 and text.endswith(('.', '!', '?')):
        text = text[:-1]
        
    # Kadang lowercase santai
    if random.random() < 0.25:
        text = text[0].lower() + text[1:]
        
    return text

def assemble_dynamic_student_response(category: str = "pendapat") -> str:
    """
    Membangun kalimat secara modular dengan tata bahasa santai anak muda
    untuk memastikan variasi yang tak terbatas dan tidak kaku.
    """
    if category == "saran":
        openings = ["Kalau bisa ", "Mungkin ke depannya ", "Semoga ", "Bisa tolong ", "Saran dari aku, ", "", ""]
        cores = [
            "tampilannya dibikin makin responsif lagi pas dibuka di hp",
            "servernya dijaga biar tetap stabil pas jam-jam sibuk",
            "ditambahin panduan singkat atau FAQ biar mahasiswa ga bingung",
            "loadingnya bisa dipercepat dikit lagi biar makin sat set",
            "dipertahanin aja kualitasnya yang sekarang, udah mantap kok",
            "tombol aksinya dibikin lebih kontras dikit biar lebih keliatan",
            "infonya lebih sering di-share di medsos biar ga ketinggalan info",
            "desainnya dibuat makin minimalis dan modern",
            "proses verifikasinya bisa lebih dipersingkat lagi"
        ]
        closings = [" yaa.", " ke depannya.", ", terima kasih.", ".", "", " biar makin oke."]
    elif category == "akademik":
        openings = ["Menurutku ", "Kuncinya ", "Kalau aku pribadi ", "Sejauh ini ", "", ""]
        cores = [
            "fokus bagi waktu antara kuliah sama istirahat biar ga burnout",
            "tetap konsisten ngerjain tugas dari jauh-jauh hari",
            "banyakin diskusi bareng temen sekelas kalau ada materi yang susah",
            "ingat tujuan awal kuliah biar tetap termotivasi sampai lulus",
            "selalu berusaha kasih yang terbaik di setiap semester",
            "belajar adaptasi sama ritme tugas dan praktikum yang padat"
        ]
        closings = [" sih.", " aja.", ", itu ngebantu banget.", ".", ""]
    elif category == "kendala":
        openings = ["Sejauh ini ", "Kalau kendala ", "Paling tantangannya ", "Aman aja sih, ", "", ""]
        cores = [
            "belum ada kendala yang berarti, semuanya lancar",
            "cuma di sinyal internet aja kalau pas lagi di kosan",
            "bagi waktu pas tugas kuliah lagi barengan",
            "tugasnya lumayan banyak tapi masih bisa dihandle",
            "sempat kaget sama materi awal tapi sekarang udah terbiasa",
            "kalau ada kesulitan langsung diskusi bareng temen"
        ]
        closings = [" sih.", " aja.", ", selebihnya aman.", ".", ""]
    else: # pendapat / umum
        openings = ["Overall ", "Menurutku ", "Sejauh ini ", "Jujur ", "Secara umum ", "", "", ""]
        cores = [
            "udah bagus banget dan ga ribet pas dipake",
            "udah oke dan gampang dipahami alurnya",
            "tampilannya bersih dan enak dilihat di layar hp",
            "ngebantu banget buat kebutuhan mahasiswa",
            "prosesnya sat set dan lancar tanpa kendala",
            "desainnya simpel dan to the point",
            "semua fiturnya berfungsi dengan sangat baik",
            "aksesnya lumayan cepet ga bikin nunggu lama",
            "gampang diakses kapan aja dan ga bikin bingung"
        ]
        closings = [" sih.", " kok.", ", tinggal dipertahanin aja.", ", mantap.", ".", "", " banget."]

    sent = random.choice(openings) + random.choice(cores) + random.choice(closings)
    sent = sent.strip()
    return apply_natural_youth_style(sent)

def get_fallback_text(prompt_type: str = "pendapat", context: str = "") -> str:
    """
    Mendapatkan tanggapan natural mahasiswa / anak muda masa kini yang santai,
    tidak kaku/baku birokratis, dan tidak alay berlebihan.
    """
    ctx_lower = context.lower() if context else ""
    pt_lower = prompt_type.lower()
    
    # Deteksi kategori yang paling relevan
    if any(k in ctx_lower for k in ["motivasi", "belajar", "akademik", "grit", "cita", "kuliah", "tujuan", "upaya", "prestasi", "alasan"]):
        category = "akademik"
    elif any(k in ctx_lower for k in ["kendala", "hambatan", "kesulitan", "masalah", "keluhan"]):
        category = "kendala"
    elif any(k in ctx_lower for k in ["saran", "masukan", "harapan", "rekomendasi", "kritik", "perbaikan"]) or pt_lower == "saran":
        category = "saran"
    elif any(k in ctx_lower for k in ["pendapat", "ulasan", "review", "kesan", "tanggapan", "pandangan"]) or pt_lower == "pendapat":
        category = "pendapat"
    elif pt_lower in STUDENT_PHRASES:
        category = pt_lower
    else:
        category = "umum"

    # 50% pilih dari pool kurasi berkualitas, 50% generate secara dinamis modular
    if random.random() < 0.5 and category in STUDENT_PHRASES:
        raw_text = random.choice(STUDENT_PHRASES[category])
        return apply_natural_youth_style(raw_text)
    else:
        return assemble_dynamic_student_response(category)
