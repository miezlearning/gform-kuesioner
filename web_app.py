import os
import json
import random
import threading
import time
from typing import Dict, Any, List
from flask import Flask, render_template, jsonify, request, Response

from src.config import (
    CSV_FILE_PATH,
    FORM_URL,
    TARGET_SUBMISSIONS,
    SUBMISSION_DELAY_MIN,
    SUBMISSION_DELAY_MAX
)
from src.csv_helper import load_students_from_csv
from src.history_helper import load_history, save_to_history, clear_history
from src.form_handler import GoogleFormHandler
from src.ai_handler import AITextGenerator
from src.answer_resolver import AnswerResolver
from src.generators import (
    format_natural_name,
    generate_varied_email,
    generate_scale_answer
)

app = Flask(__name__)

# State management global untuk status running job
class JobStatus:
    def __init__(self):
        self.logs = []
        self.is_running = False
        self.total_target = 0
        self.completed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.thread = None
        self.lock = threading.Lock()

    def add_log(self, text: str, type: str = "info"):
        with self.lock:
            self.logs.append({
                "text": text,
                "type": type,
                "time": time.strftime("%H:%M:%S")
            })

    def get_logs_from(self, index: int) -> List[Dict[str, Any]]:
        with self.lock:
            return self.logs[index:]

    def reset(self):
        with self.lock:
            self.logs = []
            self.is_running = False
            self.total_target = 0
            self.completed_count = 0
            self.success_count = 0
            self.failed_count = 0

job_status = JobStatus()

def get_available_cohorts() -> List[str]:
    """Membaca daftar angkatan berdasarkan file CSV di folder dataset."""
    cohorts = []
    dataset_dir = "dataset"
    if os.path.exists(dataset_dir):
        for file in os.listdir(dataset_dir):
            if file.endswith(".csv"):
                cohorts.append(file[:-4])
    return sorted(cohorts)

def distribute_targets(target: int, cohorts: List[str], mode: str, custom_weights: dict, history: List[str]):
    """
    Menghitung pembagian target ke masing-masing angkatan.
    Mengembalikan: (dict_target_per_angkatan, dict_sisa_mahasiswa_per_angkatan)
    """
    remaining_students = {}
    for c in cohorts:
        filepath = f"dataset/{c}.csv"
        students = load_students_from_csv(filepath)
        rem = [s for s in students if s['nim'] not in history]
        remaining_students[c] = rem

    total_remaining = sum(len(rem) for rem in remaining_students.values())
    if total_remaining == 0:
        return {}, remaining_students

    # Cap target agar tidak melebihi sisa data
    target = min(target, total_remaining)
    cohort_targets = {c: 0 for c in cohorts}

    if mode == "rata":
        active_cohorts = list(cohorts)
        rem_target = target
        while rem_target > 0 and active_cohorts:
            share = rem_target // len(active_cohorts)
            if share == 0:
                share = 1
            
            next_active = []
            for c in active_cohorts:
                if rem_target <= 0:
                    break
                capacity = len(remaining_students[c]) - cohort_targets[c]
                allocation = min(share, capacity, rem_target)
                cohort_targets[c] += allocation
                rem_target -= allocation
                if cohort_targets[c] < len(remaining_students[c]):
                    next_active.append(c)
            active_cohorts = next_active

    elif mode == "proporsional":
        rem_target = target
        capacities = {c: len(remaining_students[c]) for c in cohorts}
        while rem_target > 0:
            total_capacity = sum(capacities[c] for c in cohorts if capacities[c] > 0)
            if total_capacity == 0:
                break
            allocated_any = False
            for c in cohorts:
                if capacities[c] <= 0 or rem_target <= 0:
                    continue
                share = int(rem_target * (capacities[c] / total_capacity))
                if share == 0 and rem_target > 0:
                    share = 1
                allocation = min(share, capacities[c], rem_target)
                cohort_targets[c] += allocation
                capacities[c] -= allocation
                rem_target -= allocation
                allocated_any = True
            if not allocated_any:
                break

    elif mode == "kustom":
        weights = {c: float(custom_weights.get(c, 0)) for c in cohorts}
        total_weight = sum(weights.values())
        if total_weight == 0:
            return distribute_targets(target, cohorts, "rata", {}, history)
            
        rem_target = target
        capacities = {c: len(remaining_students[c]) for c in cohorts}
        
        for c in cohorts:
            pct = weights[c] / total_weight
            allocation = min(int(target * pct), capacities[c])
            cohort_targets[c] = allocation
            capacities[c] -= allocation
            rem_target -= allocation
            
        while rem_target > 0:
            available_cohorts = [c for c in cohorts if capacities[c] > 0]
            if not available_cohorts:
                break
            sub_total_weight = sum(weights[c] for c in available_cohorts)
            if sub_total_weight == 0:
                share = 1
                for c in available_cohorts:
                    if rem_target <= 0:
                        break
                    allocation = min(share, capacities[c], rem_target)
                    cohort_targets[c] += allocation
                    capacities[c] -= allocation
                    rem_target -= allocation
            else:
                for c in available_cohorts:
                    if rem_target <= 0:
                        break
                    pct = weights[c] / sub_total_weight
                    share = int(rem_target * pct)
                    if share == 0:
                        share = 1
                    allocation = min(share, capacities[c], rem_target)
                    cohort_targets[c] += allocation
                    capacities[c] -= allocation
                    rem_target -= allocation

    return cohort_targets, remaining_students

def run_web_fill(target: int, cohorts: List[str], mode: str, custom_weights: dict, min_delay: int, max_delay: int, url: str, question_rules: dict = None):
    global job_status
    history = load_history()
    question_rules = question_rules or {}
    
    targets, remaining_students = distribute_targets(target, cohorts, mode, custom_weights, history)
    
    if not targets:
        job_status.add_log("Error: Tidak ada data mahasiswa yang terpilih atau kapasitas sudah penuh.", "error")
        job_status.is_running = False
        return

    job_status.add_log("Alokasi responden terpilih:", "info")
    for c, count in targets.items():
        job_status.add_log(f"  - Angkatan {c}: {count} responden (dari {len(remaining_students[c])} sisa data)", "info")
        
    selected_pool = []
    for c, count in targets.items():
        if count > 0:
            samples = random.sample(remaining_students[c], count)
            for s in samples:
                selected_pool.append((s, c))
                
    random.shuffle(selected_pool)
    actual_target = len(selected_pool)
    job_status.total_target = actual_target
    job_status.add_log(f"Total responden yang akan diisi secara acak: {actual_target}", "info")
    
    job_status.add_log("Mengekstrak struktur Google Form...", "info")
    form_handler = GoogleFormHandler(url)
    ai_generator = AITextGenerator()
    resolver = AnswerResolver(ai_generator)
    
    form_data = form_handler.extract_structure()
    if not form_data:
        job_status.add_log("Gagal mengekstrak struktur Google Form. Periksa koneksi internet atau link form Anda.", "error")
        job_status.is_running = False
        return
        
    pages = form_data["pages"]
    fbzx = form_data["fbzx"]
    fvv = form_data["fvv"]
    has_email_page = form_data["has_email_page"]
    page_history = form_data["page_history"]
    form_title = form_data.get("form_title", "Google Form")
    
    job_status.add_log(f"Form '{form_title}' terdeteksi ({len(pages)} halaman). Memulai pengisian...", "success")
    if question_rules:
        job_status.add_log(f"Menerapkan {len(question_rules)} aturan kustom pada pertanyaan.", "info")
    
    for index, (student, angkatan) in enumerate(selected_pool):
        if not job_status.is_running:
            job_status.add_log("Proses pengisian dibatalkan oleh pengguna.", "warning")
            break
            
        nama = format_natural_name(student.get('nama', 'Mahasiswa'))
        nim = student.get('nim', '')
        
        job_status.add_log(f"[{index+1}/{actual_target}] Mengisi: {nama} ({nim} - Angkatan {angkatan})...", "info")
        
        profile = random.choices(
            ["sangat_puas", "puas_rata_rata", "kritis"],
            weights=[35, 55, 10]
        )[0]
        
        email = generate_varied_email(nama, nim)
        
        # Selesaikan seluruh nilai jawaban menggunakan AnswerResolver
        all_page_values = resolver.resolve_all_pages(pages, student, profile, question_rules)
        
        # Kirim form secara multi-halaman sempurna
        success, message = form_handler.submit_pages(
            all_page_values, 
            email=email if has_email_page else ""
        )
        
        if success:
            save_to_history(nim)
            job_status.success_count += 1
            job_status.add_log(f"  ✓ Sukses: {nama} ({nim})", "success")
            # Tampilkan sample ulasan jika ada field ulasan/saran
            for p in all_page_values:
                for item in p:
                    if any(k in item['label'].lower() for k in ["pendapat", "saran", "masukan", "ulasan"]):
                        job_status.add_log(f"    > {item['label'][:25]}...: \"{item['value']}\"", "info")
        else:
            job_status.failed_count += 1
            job_status.add_log(f"  ✗ Gagal: {nama} ({nim}) - Detail: {message}", "error")
            
        job_status.completed_count += 1
        
        if index < actual_target - 1:
            delay = random.randint(min_delay, max_delay)
            job_status.add_log(f"Menunggu {delay} detik sebelum pengisian berikutnya...", "info")
            for _ in range(int(delay * 10)):
                if not job_status.is_running:
                    break
                time.sleep(0.1)
                
    job_status.add_log(f"=== Pekerjaan Selesai! Sukses: {job_status.success_count}, Gagal: {job_status.failed_count} ===", "success")
    job_status.is_running = False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/parse-form", methods=["POST"])
def parse_form():
    """Membaca dan mengekstrak seluruh pertanyaan & opsi dari Google Form URL."""
    data = request.json or {}
    url = data.get("url") or FORM_URL
    if not url:
        return jsonify({"success": False, "message": "URL Google Form wajib diisi."}), 400
        
    handler = GoogleFormHandler(url)
    structure = handler.extract_structure()
    if not structure:
        return jsonify({
            "success": False, 
            "message": "Gagal membaca struktur Google Form. Pastikan link Google Form benar, publik, dan berformat https://docs.google.com/forms/d/e/.../viewform"
        }), 400
        
    return jsonify({
        "success": True,
        "form_title": structure.get("form_title", "Formulir Google"),
        "form_description": structure.get("form_description", ""),
        "num_pages": structure.get("num_pages", len(structure.get("pages", []))),
        "questions": structure.get("questions", []),
        "has_email_page": structure.get("has_email_page", False)
    })

@app.route("/api/status", methods=["GET"])
def get_status():
    cohorts = get_available_cohorts()
    history = load_history()
    stats = []
    for c in cohorts:
        filepath = f"dataset/{c}.csv"
        students = load_students_from_csv(filepath)
        total = len(students)
        filled = len([s for s in students if s['nim'] in history])
        stats.append({
            "cohort": c,
            "total": total,
            "filled": filled,
            "remaining": total - filled
        })
    return jsonify({
        "stats": stats,
        "default_url": FORM_URL,
        "default_target": TARGET_SUBMISSIONS,
        "default_delay_min": SUBMISSION_DELAY_MIN,
        "default_delay_max": SUBMISSION_DELAY_MAX,
        "is_running": job_status.is_running,
        "job_progress": {
            "completed": job_status.completed_count,
            "target": job_status.total_target,
            "success": job_status.success_count,
            "failed": job_status.failed_count
        }
    })

@app.route("/api/start", methods=["POST"])
def start_job():
    global job_status
    if job_status.is_running:
        return jsonify({"success": False, "message": "Pekerjaan sedang berjalan!"}), 400
        
    data = request.json or {}
    target = int(data.get("target", TARGET_SUBMISSIONS))
    cohorts = data.get("cohorts", [])
    mode = data.get("mode", "rata")
    custom_weights = data.get("weights", {})
    min_delay = int(data.get("min_delay", SUBMISSION_DELAY_MIN))
    max_delay = int(data.get("max_delay", SUBMISSION_DELAY_MAX))
    url = data.get("url", FORM_URL)
    question_rules = data.get("question_rules", {})
    
    if not cohorts:
        return jsonify({"success": False, "message": "Pilih minimal satu angkatan!"}), 400
        
    job_status.reset()
    job_status.is_running = True
    
    # Jalankan background thread
    job_status.thread = threading.Thread(
        target=run_web_fill,
        args=(target, cohorts, mode, custom_weights, min_delay, max_delay, url, question_rules)
    )
    job_status.thread.daemon = True
    job_status.thread.start()
    
    return jsonify({"success": True, "message": "Pekerjaan berhasil dimulai."})

@app.route("/api/stop", methods=["POST"])
def stop_job():
    global job_status
    if not job_status.is_running:
        return jsonify({"success": False, "message": "Pekerjaan tidak sedang berjalan!"})
    job_status.is_running = False
    return jsonify({"success": True, "message": "Pekerjaan sedang dihentikan..."})

@app.route("/api/reset-history", methods=["POST"])
def reset_history():
    if job_status.is_running:
        return jsonify({"success": False, "message": "Tidak dapat mereset riwayat saat pekerjaan sedang berjalan!"}), 400
    success = clear_history()
    if success:
        return jsonify({"success": True, "message": "Riwayat berhasil direset."})
    return jsonify({"success": False, "message": "Gagal mereset riwayat."}), 500

@app.route("/api/history", methods=["GET"])
def get_history_details():
    """Mengembalikan daftar lengkap mahasiswa dan NIM yang telah mengisi form."""
    history_nims = set(load_history())
    cohorts = get_available_cohorts()
    details = []
    seen = set()
    for c in cohorts:
        students = load_students_from_csv(f"dataset/{c}.csv")
        for s in students:
            nim = s.get("nim", "")
            if nim in history_nims and nim not in seen:
                seen.add(nim)
                details.append({
                    "nim": nim,
                    "nama": s.get("nama", "-"),
                    "angkatan": s.get("angkatan", "-"),
                    "prodi": s.get("program studi", "-"),
                    "dataset": c
                })
    for nim in history_nims:
        if nim not in seen:
            seen.add(nim)
            details.append({
                "nim": nim,
                "nama": "Mahasiswa",
                "angkatan": f"20{nim[:2]}" if len(nim) >= 2 else "-",
                "prodi": "-",
                "dataset": "Riwayat Tersimpan"
            })
    return jsonify({
        "total": len(history_nims),
        "items": details
    })

@app.route("/api/stream")
def stream_logs():
    def generate():
        last_idx = 0
        while True:
            logs = job_status.get_logs_from(last_idx)
            for log in logs:
                yield f"data: {json.dumps(log)}\n\n"
                last_idx += 1
                
            if not job_status.is_running:
                # Ambil sisa log yang masuk di detik terakhir
                logs = job_status.get_logs_from(last_idx)
                for log in logs:
                    yield f"data: {json.dumps(log)}\n\n"
                    last_idx += 1
                yield f"data: {json.dumps({'text': '[FINISHED]', 'type': 'system'})}\n\n"
                break
                
            time.sleep(0.5)
            
    return Response(generate(), mimetype='text/event-stream')

def find_available_port(preferred_port: int = 5001) -> int:
    """Mencari port yang benar-benar terbuka agar terhindar dari konflik port sistem Windows."""
    import socket
    ports_to_try = [preferred_port, 5001, 5055, 8080, 8000]
    for p in ports_to_try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                return p
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

if __name__ == "__main__":
    requested_port = int(os.environ.get("PORT", 5001))
    port = find_available_port(requested_port)
    print(f"\n=======================================================")
    print(f"  KUESIONER AUTO-FILLER WEB DASHBOARD")
    print(f"  Akses di Browser: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)

