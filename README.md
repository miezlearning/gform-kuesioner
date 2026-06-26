# 📋 Google Forms Questionnaire Auto-Filler

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](https://opensource.org/licenses/MIT)

Script otomatisasi pengisian Google Forms multi-page secara cerdas dan natural menggunakan database responden dari file CSV, dilengkapi ulasan dinamis berbasis AI GPT.

---

## 📂 Struktur Proyek

Klik pada folder atau berkas di bawah untuk membuka secara langsung:

* 📂 **[cli/](./cli/)** - Folder eksekusi antarmuka terminal
  * 📄 **[kuesioner_cli.py](./cli/kuesioner_cli.py)** - Script utama versi CLI
* 📂 **[dataset/](./dataset/)** - Folder penyimpanan database mahasiswa (CSV)
  * 📄 **[2024.csv](./dataset/2024.csv)** & **[2025.csv](./dataset/2025.csv)** - Sampel data responden
* 📂 **[src/](./src/)** - Folder modul pembantu (Helpers)
  * 📄 **[config.py](./src/config.py)** - Parameter konfigurasi default
  * 📄 **[csv_helper.py](./src/csv_helper.py)** - Loader & parser berkas CSV
  * 📄 **[generators.py](./src/generators.py)** - Generator data acak (nama, email, skala)
  * 📄 **[ai_handler.py](./src/ai_handler.py)** - Integrator AI GPT & ulasan dinamis
  * 📄 **[form_handler.py](./src/form_handler.py)** - Parser form & submit payload
* 📄 **[kuesioner.py](./kuesioner.py)** - Script eksekusi utama (Default/GUI)
* 📄 **[requirements.txt](./requirements.txt)** - Daftar dependensi pustaka python

---

## 🚀 Cara Penggunaan

### 1. Instalasi Dependensi
Jalankan perintah ini di terminal Anda untuk menginstal pustaka yang diperlukan:
```bash
pip install -r requirements.txt
```

### 2. Menjalankan Script Standar
Gunakan konfigurasi default yang ada di dalam `src/config.py`:
```bash
python kuesioner.py
```

### 3. Menjalankan Script CLI
Gunakan argumen terminal jika ingin merubah parameter secara dinamis:
```bash
# Menampilkan menu bantuan & argumen
python cli/kuesioner_cli.py --help

# Mengisi kuesioner dengan target 10 responden
python cli/kuesioner_cli.py --target 10

# Mengisi kuesioner dengan berkas CSV dan URL kustom
python cli/kuesioner_cli.py --csv dataset/2024.csv --url "https://docs.google.com/forms/d/e/.../viewform" --target 5
```
