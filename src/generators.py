import random
import re
from typing import Set, List

def format_natural_name(nama: str) -> str:
    """
    Format nama agar terlihat bervariasi seperti diketik manual 
    oleh orang awam (Title Case, lower case, atau UPPER CASE).
    """
    nama_clean = nama.strip()
    style = random.choices(
        ["title", "lower", "upper"],
        weights=[70, 20, 10]
    )[0]
    
    if style == "title":
        return nama_clean.title()
    elif style == "lower":
        return nama_clean.lower()
    else:
        return nama_clean.upper()


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


def get_fallback_text(prompt_type: str) -> str:
    """
    Mendapatkan teks ulasan (pendapat) atau saran acak dari template lokal
    sebagai fallback jika pemanggilan AI API gagal.
    """
    if prompt_type == "pendapat":
        direct = [
            "Aksesnya cukup lancar.",
            "Lumayan fast respond.",
            "Tampilan webnya sudah oke.",
            "Menu surat gampang dicari.",
            "Proses upload berkas lancar.",
            "Dashboard responsif di HP.",
            "Alurnya sangat praktis.",
            "Cek status surat mudah.",
            "Tampilannya bersih dan rapi.",
            "Menu pengajuan tertata baik.",
            "Instruksi form cukup jelas.",
            "Sistemnya sangat membantu.",
            "Pengajuan surat tidak ribet.",
            "Desain web lumayan modern.",
            "Loading website cukup cepat.",
            "Prosesnya sat set banget.",
            "Tracking surat sangat membantu."
        ]
    else:  # saran
        direct = [
            "Loading submit PDF dipercepat.",
            "Tombol kirim ganti warna.",
            "Tambahkan notifikasi WhatsApp.",
            "Infokan max file size upload.",
            "Menu KHS segera diaktifkan.",
            "Tampilan mobile diperbaiki lagi.",
            "Loading web tolong dioptimalkan.",
            "Desain halaman dibuat modern.",
            "Navigasi form dibuat ringkas.",
            "Tracking status dipercepat responnya.",
            "Catatan revisi diperjelas infonya.",
            "Tampilan menu dirapikan sedikit.",
            "Notif status dibuat real-time.",
            "Perjelas kolom deskripsi opsional.",
            "WhatsApp notif segera diadakan.",
            "Upload slip UKT dipermudah lagi."
        ]
    return random.choice(direct)
