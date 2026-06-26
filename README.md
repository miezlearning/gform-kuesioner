# 📋 Google Forms Questionnaire Auto-Filler (Kuesioner Auto)

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg?style=flat-square)](https://github.com/)

Script otomatisasi pengisian Google Forms multi-page secara cerdas dan natural menggunakan dataset responden dari file CSV, dilengkapi dengan generator data realistis dan ulasan dinamis berbasis AI GPT.

---

## ✨ Fitur Utama

- **🧠 AI-Powered & Anti-Duplicate**: Menghasilkan ulasan (pendapat & saran) dinamis yang unik via GPT API dengan sistem filter *Jaccard Similarity* & *Prefix Matching* untuk mencegah adanya teks duplikat.
- **🛡️ Fallback System**: Menyediakan template jawaban cadangan secara lokal yang siap digunakan apabila API mengalami kendala atau kehabisan limit.
- **⚡ Auto-Scraping**: Mendeteksi struktur Google Form secara dinamis (ID entry, linear scale, tipe masukan, session `fbzx`, dan halaman email bawaan) tanpa perlu inspect HTML manual.
- **📂 Multi-Page Support**: Mendukung pengisian Google Forms dengan banyak halaman menggunakan pemrosesan parameter `partialResponse`.
- **🎭 Human-Like Simulation**:
  - Profiling kepuasan responden secara acak (*sangat puas*, *kritis*, atau *rata-rata*).
  - Variasi format pengetikan nama (*Title Case*, *lowercase*, *UPPERCASE*).
  - Variasi gaya pembuatan email fiktif (gamer tag, nama inisial, singkatan).
  - Jeda acak antar pengisian (random sleep) untuk menghindari deteksi bot.
- **📦 Modular & CLI-Ready**: Kode terstruktur rapi dan memiliki versi CLI untuk kemudahan penggunaan lewat terminal.

---

## 🛠️ Struktur Repositori

```text
kuesioner_auto/
│
├── cli/
│   └── kuesioner_cli.py     # Script eksekusi versi Command-Line Interface (CLI)
│
├── dataset/
│   ├── 2024.csv             # Contoh database responden mahasiswa angkatan 2024
│   └── 2025.csv             # Contoh database responden mahasiswa angkatan 2025
│
├── src/                     # Paket Modul Pendukung (Helper Modules)
│   ├── __init__.py          # Penanda package python
│   ├── config.py            # Konfigurasi konstan (URL Form, API, target, dll)
│   ├── csv_helper.py        # Helper pemroses & pembaca data CSV
│   ├── generators.py        # Logika pembuat data acak (nama, email, skala)
│   ├── ai_handler.py        # Modul integrasi GPT API & ulasan dinamis
│   └── form_handler.py      # Pengelola parsing & submit payload ke Google Form
│
├── kuesioner.py             # Script eksekusi utama versi standar (GUI/Default config)
└── README.md                # Dokumentasi proyek
```

---

## 🚀 Cara Penggunaan

### 1. Instalasi Dependensi
Pastikan Anda memiliki Python 3.8+ dan jalankan instalasi dependensi berikut:
```bash
pip install requests beautifulsoup4
```

### 2. Jalankan Versi Standar (Default)
Menggunakan konfigurasi langsung dari berkas `src/config.py`:
```bash
python kuesioner.py
```

### 3. Jalankan Versi CLI (Fleksibel)
Anda dapat mengirim argumen masukan secara dinamis langsung lewat terminal:
```bash
# Menampilkan menu bantuan & daftar argumen yang tersedia
python cli/kuesioner_cli.py --help

# Menjalankan dengan target 10 pengisian
python cli/kuesioner_cli.py --target 10

# Menjalankan dengan file CSV dan form URL kustom
python cli/kuesioner_cli.py --csv dataset/2024.csv --url "https://docs.google.com/forms/d/e/.../viewform" --target 5

# Mengatur jeda pengisian dinamis (misal jeda acak 2 s/d 5 detik)
python cli/kuesioner_cli.py --min-delay 2 --max-delay 5 --target 3
```

---

## ⚙️ Konfigurasi
Anda dapat menyesuaikan parameter utama program melalui berkas `src/config.py` atau lewat variabel lingkungan (Environment Variables):
- `CSV_FILE_PATH`: Path file CSV database responden.
- `FORM_URL`: Link Google Form target.
- `AI_API_URL`: Link API GPT pembangun ulasan.
- `TARGET_SUBMISSIONS`: Jumlah pengisian yang diinginkan.
- `SUBMISSION_DELAY_MIN` & `SUBMISSION_DELAY_MAX`: Rentang waktu tunggu pengisian.

---

## 📄 Lisensi
Proyek ini dilisensikan di bawah **MIT License** - lihat file [LICENSE](LICENSE) untuk detailnya.
