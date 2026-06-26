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

def generate_field_value(
    field: Dict[str, Any], 
    nama: str, 
    nim: str, 
    angkatan: str, 
    pendapat: str, 
    saran: str, 
    email: str, 
    profile: str
) -> str:
    """Menentukan nilai untuk setiap field berdasarkan label dan tipe pertanyaan."""
    lbl_lower = field["label"].lower()
    
    if "nama" in lbl_lower:
        return nama
    elif "nim" in lbl_lower:
        return nim
    elif "angkatan" in lbl_lower:
        return angkatan
    elif "pendapat" in lbl_lower:
        return pendapat
    elif "saran" in lbl_lower:
        return saran
    elif "email" in lbl_lower:
        return email
    else:
        return generate_scale_answer(profile)

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

def run_web_fill(target: int, cohorts: List[str], mode: str, custom_weights: dict, min_delay: int, max_delay: int, url: str):
    global job_status
    history = load_history()
    
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
    
    form_data = form_handler.extract_structure()
    if not form_data:
        job_status.add_log("Gagal mengekstrak struktur Google Form. Periksa internet atau URL Anda.", "error")
        job_status.is_running = False
        return
        
    pages = form_data["pages"]
    fbzx = form_data["fbzx"]
    fvv = form_data["fvv"]
    has_email_page = form_data["has_email_page"]
    page_history = form_data["page_history"]
    
    job_status.add_log("Struktur form berhasil dimuat. Memulai pengisian...", "success")
    
    for index, (student, angkatan) in enumerate(selected_pool):
        if not job_status.is_running:
            job_status.add_log("Proses pengisian dibatalkan oleh pengguna.", "warning")
            break
            
        nama_raw = student['nama']
        nama = format_natural_name(nama_raw)
        nim = student['nim']
        
        job_status.add_log(f"[{index+1}/{actual_target}] Mengisi: {nama} ({nim} - Angkatan {angkatan})...", "info")
        
        profile = random.choices(
            ["sangat_puas", "puas_rata_rata", "kritis"],
            weights=[35, 55, 10]
        )[0]
        
        email = generate_varied_email(nama, nim)
        pendapat = ai_generator.generate_text("pendapat")
        saran = ai_generator.generate_text("saran")
        
        all_page_values = []
        for page in pages:
            page_values = []
            for field in page:
                value = generate_field_value(field, nama, nim, angkatan, pendapat, saran, email, profile)
                page_values.append({
                    "entry_id": field["entry_id"],
                    "value": value,
                    "label": field["label"]
                })
            all_page_values.append(page_values)
            
        partial_entries = []
        for page_values in all_page_values[:-1]:
            for field_val in page_values:
                partial_entries.append((field_val["entry_id"], field_val["value"]))
                
        partial_response_json = form_handler.build_partial_response(partial_entries, fbzx, email)
        
        last_page = all_page_values[-1]
        payload = {}
        for field_val in last_page:
            entry_key = f"entry.{field_val['entry_id']}"
            payload[entry_key] = field_val["value"]
            
            for field in pages[-1]:
                if field["entry_id"] == field_val["entry_id"] and field["type"] == 5:
                    payload[f"{entry_key}_sentinel"] = ""
                    break
                    
        payload["fvv"] = fvv
        payload["partialResponse"] = partial_response_json
        payload["pageHistory"] = page_history
        payload["fbzx"] = fbzx
        payload["submissionTimestamp"] = str(int(time.time() * 1000))
        
        if has_email_page:
            payload["emailAddress"] = email
            
        success, message = form_handler.submit(payload, referer_url=form_handler.submit_url)
        
        if success:
            save_to_history(nim)
            job_status.success_count += 1
            job_status.add_log(f"  ✓ Sukses: {nama} ({nim})", "success")
            job_status.add_log(f"    > Pendapat: \"{pendapat}\"", "info")
            job_status.add_log(f"    > Saran   : \"{saran}\"", "info")
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
    
    if not cohorts:
        return jsonify({"success": False, "message": "Pilih minimal satu angkatan!"}), 400
        
    job_status.reset()
    job_status.is_running = True
    
    # Jalankan background thread
    job_status.thread = threading.Thread(
        target=run_web_fill,
        args=(target, cohorts, mode, custom_weights, min_delay, max_delay, url)
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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
