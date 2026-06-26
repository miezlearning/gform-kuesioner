document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const formUrlInput = document.getElementById("form-url");
    const targetInput = document.getElementById("target-submissions");
    const delayMinInput = document.getElementById("delay-min");
    const delayMaxInput = document.getElementById("delay-max");
    const distributionRadios = document.getElementsByName("distribution-mode");
    const cohortsGrid = document.getElementById("cohorts-grid");
    const btnStart = document.getElementById("btn-start");
    const btnStop = document.getElementById("btn-stop");
    const btnSelectAll = document.getElementById("btn-select-all");
    const btnDeselectAll = document.getElementById("btn-deselect-all");
    const btnResetHistory = document.getElementById("btn-reset-history");
    const btnClearTerminal = document.getElementById("btn-clear-terminal");
    const btnToggleAutoscroll = document.getElementById("btn-toggle-autoscroll");
    const terminalBody = document.getElementById("terminal-body");
    
    // Progress Section
    const progressContainer = document.getElementById("progress-container");
    const progressText = document.getElementById("progress-text");
    const statSuccessCount = document.getElementById("stat-success-count");
    const statFailedCount = document.getElementById("stat-failed-count");
    const progressBarFill = document.getElementById("progress-bar-fill");
    
    // Custom Weights Bar
    const customWeightAlert = document.getElementById("custom-weight-alert");
    const weightTotalPercentage = document.getElementById("weight-total-percentage");
    const weightValidationMsg = document.getElementById("weight-validation-msg");
    
    // Modals
    const modalConfirm = document.getElementById("modal-confirm");
    const btnConfirmCancel = document.getElementById("btn-confirm-cancel");
    const btnConfirmReset = document.getElementById("btn-confirm-reset");
    
    // State Variables
    let cohortsData = [];
    let checkedCohorts = new Set();
    let customWeights = {}; // { cohort: percentage_int }
    let isAutoscroll = true;
    let eventSource = null;
    let statusInterval = null;
    let isRunning = false;

    // Initialize application
    init();

    function init() {
        fetchStatus(true); // Load initial setup
        setupEventListeners();
    }

    function setupEventListeners() {
        // Clear terminal
        btnClearTerminal.addEventListener("click", () => {
            terminalBody.innerHTML = '<div class="terminal-line system">Terminal dibersihkan.</div>';
        });

        // Toggle Autoscroll
        btnToggleAutoscroll.addEventListener("click", () => {
            isAutoscroll = !isAutoscroll;
            btnToggleAutoscroll.classList.toggle("active", isAutoscroll);
        });

        // Mode Distribusi Change
        distributionRadios.forEach(radio => {
            radio.addEventListener("change", (e) => {
                toggleWeightControls(e.target.value === "kustom");
                validateWeights();
            });
        });

        // Select All / Deselect All
        btnSelectAll.addEventListener("click", () => {
            checkedCohorts.clear();
            cohortsData.forEach(c => checkedCohorts.add(c.cohort));
            renderCohorts();
            validateWeights();
        });

        btnDeselectAll.addEventListener("click", () => {
            checkedCohorts.clear();
            renderCohorts();
            validateWeights();
        });

        // Reset History Modals
        btnResetHistory.addEventListener("click", () => {
            modalConfirm.classList.remove("hidden");
        });

        btnConfirmCancel.addEventListener("click", () => {
            modalConfirm.classList.add("hidden");
        });

        btnConfirmReset.addEventListener("click", () => {
            modalConfirm.classList.add("hidden");
            resetHistory();
        });

        // Submit form (Start Job)
        document.getElementById("settings-form").addEventListener("submit", (e) => {
            e.preventDefault();
            if (isRunning) return;
            startJob();
        });

        // Stop Job button
        btnStop.addEventListener("click", stopJob);
    }

    // Toggle showing weight inputs/sliders
    function toggleWeightControls(show) {
        const weightControls = document.querySelectorAll(".cohort-weight-control");
        weightControls.forEach(ctrl => {
            if (show) {
                ctrl.classList.remove("hidden");
            } else {
                ctrl.classList.add("hidden");
            }
        });
        
        if (show) {
            customWeightAlert.classList.remove("hidden");
            // Auto allocate equal weights if empty or 0
            const activeCount = checkedCohorts.size;
            if (activeCount > 0) {
                let sum = 0;
                checkedCohorts.forEach(c => {
                    if (!customWeights[c]) {
                        customWeights[c] = Math.floor(100 / activeCount);
                    }
                    sum += customWeights[c];
                });
                
                // Adjust rounding difference to first element
                if (sum !== 100) {
                    const first = Array.from(checkedCohorts)[0];
                    customWeights[first] += (100 - sum);
                }
                
                // Sync to inputs
                checkedCohorts.forEach(c => {
                    const slider = document.getElementById(`slider-${c}`);
                    const input = document.getElementById(`val-${c}`);
                    if (slider) slider.value = customWeights[c];
                    if (input) input.value = customWeights[c];
                });
            }
        } else {
            customWeightAlert.classList.add("hidden");
        }
    }

    // Validate weights sum to 100%
    function validateWeights() {
        const mode = document.querySelector('input[name="distribution-mode"]:checked').value;
        
        if (checkedCohorts.size === 0) {
            btnStart.disabled = true;
            btnStart.title = "Pilih minimal satu angkatan!";
            return;
        }

        if (mode !== "kustom") {
            btnStart.disabled = false;
            btnStart.title = "";
            return;
        }

        let total = 0;
        checkedCohorts.forEach(c => {
            total += parseInt(customWeights[c] || 0);
        });

        weightTotalPercentage.textContent = `${total}%`;

        if (total !== 100) {
            btnStart.disabled = true;
            weightValidationMsg.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Total persen harus bernilai 100% (saat ini ${total}%)`;
            weightValidationMsg.className = "validation-error";
        } else {
            btnStart.disabled = false;
            weightValidationMsg.innerHTML = `<i class="fa-solid fa-circle-check"></i> Total bobot valid (100%)`;
            weightValidationMsg.className = "validation-error success";
        }
    }

    // Fetch cohort stats and default configs
    function fetchStatus(isInitial = false) {
        fetch("/api/status")
            .then(res => res.json())
            .then(data => {
                cohortsData = data.stats;
                
                // Sync configs on initial load
                if (isInitial) {
                    formUrlInput.value = data.default_url;
                    targetInput.value = data.default_target;
                    delayMinInput.value = data.default_delay_min;
                    delayMaxInput.value = data.default_delay_max;
                    
                    // Check all cohorts by default on first load
                    cohortsData.forEach(c => checkedCohorts.add(c.cohort));
                }

                renderCohorts();
                
                // Restore run state if server page was reloaded but server is running a job
                if (data.is_running && !isRunning) {
                    setIsRunning(true);
                    progressContainer.classList.remove("hidden");
                    updateProgressUI(data.job_progress);
                    startStreaming();
                } else if (!data.is_running && isRunning) {
                    setIsRunning(false);
                    stopStreaming();
                } else if (isRunning) {
                    updateProgressUI(data.job_progress);
                }

                validateWeights();
            })
            .catch(err => {
                console.error("Gagal memuat status dari server:", err);
                appendTerminalLine("Gagal menghubungi server untuk update data status.", "error");
            });
    }

    // Update Progress panel counters
    function updateProgressUI(progress) {
        progressText.textContent = `${progress.completed}/${progress.target}`;
        statSuccessCount.textContent = progress.success;
        statFailedCount.textContent = progress.failed;
        
        const pct = progress.target > 0 ? (progress.completed / progress.target) * 100 : 0;
        progressBarFill.style.width = `${pct}%`;
    }

    // Render cards to DOM
    function renderCohorts() {
        const isKustomMode = document.querySelector('input[name="distribution-mode"]:checked').value === "kustom";
        
        if (cohortsData.length === 0) {
            cohortsGrid.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fa-solid fa-circle-xmark"></i> Tidak ditemukan file CSV di folder dataset/
                </div>`;
            return;
        }

        // Simpan referensi input/slider untuk input kustom agar posisinya stabil
        cohortsGrid.innerHTML = "";
        cohortsData.forEach(c => {
            const isChecked = checkedCohorts.has(c.cohort);
            const pctFilled = c.total > 0 ? (c.filled / c.total) * 100 : 0;
            
            // Default weight
            if (!customWeights[c.cohort]) {
                customWeights[c.cohort] = 0;
            }

            const card = document.createElement("div");
            card.className = `cohort-card ${isChecked ? 'selected' : ''}`;
            card.innerHTML = `
                <div class="cohort-select-wrapper">
                    <span class="cohort-name">Angkatan ${c.cohort}</span>
                    <div class="card-checkbox">
                        <i class="fa-solid fa-check"></i>
                    </div>
                </div>
                
                <div class="cohort-stats">
                    <div class="stat-item">
                        <span>Total Data:</span>
                        <span>${c.total}</span>
                    </div>
                    <div class="stat-item">
                        <span>Sudah Diisi:</span>
                        <span>${c.filled}</span>
                    </div>
                    <div class="stat-item">
                        <span>Sisa:</span>
                        <span>${c.remaining}</span>
                    </div>
                    <div class="cohort-progress" title="${pctFilled.toFixed(1)}% terisi">
                        <div class="cohort-progress-fill" style="width: ${pctFilled}%"></div>
                    </div>
                </div>

                <div class="cohort-weight-control ${isKustomMode && isChecked ? '' : 'hidden'}" id="weight-ctrl-${c.cohort}">
                    <div class="weight-label">
                        <span>Bobot Pengisian:</span>
                        <span id="label-val-${c.cohort}">${customWeights[c.cohort]}%</span>
                    </div>
                    <div class="slider-wrapper">
                        <input type="range" id="slider-${c.cohort}" min="0" max="100" value="${customWeights[c.cohort]}">
                        <input type="number" id="val-${c.cohort}" min="0" max="100" class="weight-val-input" value="${customWeights[c.cohort]}">
                    </div>
                </div>
            `;

            // Prevent event capture issues by stopping slider/input click propagation
            const weightCtrl = card.querySelector(`#weight-ctrl-${c.cohort}`);
            if (weightCtrl) {
                weightCtrl.addEventListener("click", (e) => {
                    e.stopPropagation();
                });
            }

            // Click listener for selecting card
            card.addEventListener("click", () => {
                if (checkedCohorts.has(c.cohort)) {
                    checkedCohorts.delete(c.cohort);
                    card.classList.remove("selected");
                    if (weightCtrl) weightCtrl.classList.add("hidden");
                } else {
                    checkedCohorts.add(c.cohort);
                    card.classList.add("selected");
                    if (isKustomMode && weightCtrl) {
                        weightCtrl.classList.remove("hidden");
                    }
                }
                
                // Adjust weights after select change
                adjustWeightsAfterSelection();
                validateWeights();
            });

            // Sliders listener
            const slider = card.querySelector(`#slider-${c.cohort}`);
            const numInput = card.querySelector(`#val-${c.cohort}`);
            const labelVal = card.querySelector(`#label-val-${c.cohort}`);

            if (slider && numInput) {
                const updateVal = (newVal) => {
                    newVal = Math.max(0, Math.min(100, parseInt(newVal) || 0));
                    customWeights[c.cohort] = newVal;
                    slider.value = newVal;
                    numInput.value = newVal;
                    labelVal.textContent = `${newVal}%`;
                    validateWeights();
                };

                slider.addEventListener("input", (e) => updateVal(e.target.value));
                numInput.addEventListener("input", (e) => updateVal(e.target.value));
            }

            cohortsGrid.appendChild(card);
        });
    }

    // Auto balance weights when checking/unchecking cohorts in custom mode
    function adjustWeightsAfterSelection() {
        const mode = document.querySelector('input[name="distribution-mode"]:checked').value;
        if (mode !== "kustom" || checkedCohorts.size === 0) return;

        // Collect current values
        let sum = 0;
        checkedCohorts.forEach(c => {
            sum += customWeights[c] || 0;
        });

        if (sum === 0 || sum !== 100) {
            // Recalculate evenly
            const val = Math.floor(100 / checkedCohorts.size);
            checkedCohorts.forEach(c => {
                customWeights[c] = val;
            });
            
            // Adjust difference to the first one
            const remaining = 100 - (val * checkedCohorts.size);
            if (remaining > 0) {
                const first = Array.from(checkedCohorts)[0];
                customWeights[first] += remaining;
            }

            // Sync HTML elements
            checkedCohorts.forEach(c => {
                const s = document.getElementById(`slider-${c}`);
                const v = document.getElementById(`val-${c}`);
                const l = document.getElementById(`label-val-${c}`);
                if (s) s.value = customWeights[c];
                if (v) v.value = customWeights[c];
                if (l) l.textContent = `${customWeights[c]}%`;
            });
        }
    }

    // Set UI Mode (Running / Stop)
    function setIsRunning(running) {
        isRunning = running;
        if (running) {
            btnStart.classList.add("hidden");
            btnStop.classList.remove("hidden");
            btnResetHistory.disabled = true;
            btnSelectAll.disabled = true;
            btnDeselectAll.disabled = true;
            
            // Disable settings input during run
            formUrlInput.disabled = true;
            targetInput.disabled = true;
            delayMinInput.disabled = true;
            delayMaxInput.disabled = true;
            distributionRadios.forEach(r => r.disabled = true);
            document.querySelectorAll(".weight-val-input").forEach(i => i.disabled = true);
            document.querySelectorAll('input[type="range"]').forEach(r => r.disabled = true);
        } else {
            btnStart.classList.remove("hidden");
            btnStop.classList.add("hidden");
            btnResetHistory.disabled = false;
            btnSelectAll.disabled = false;
            btnDeselectAll.disabled = false;
            
            formUrlInput.disabled = false;
            targetInput.disabled = false;
            delayMinInput.disabled = false;
            delayMaxInput.disabled = false;
            distributionRadios.forEach(r => r.disabled = false);
            document.querySelectorAll(".weight-val-input").forEach(i => i.disabled = false);
            document.querySelectorAll('input[type="range"]').forEach(r => r.disabled = false);
        }
    }

    // Start questionnaire filler process
    function startJob() {
        const mode = document.querySelector('input[name="distribution-mode"]:checked').value;
        const payload = {
            url: formUrlInput.value.strip ? formUrlInput.value.strip() : formUrlInput.value,
            target: parseInt(targetInput.value),
            min_delay: parseInt(delayMinInput.value),
            max_delay: parseInt(delayMaxInput.value),
            mode: mode,
            cohorts: Array.from(checkedCohorts),
            weights: {}
        };

        if (mode === "kustom") {
            checkedCohorts.forEach(c => {
                payload.weights[c] = customWeights[c];
            });
        }

        setIsRunning(true);
        progressContainer.classList.remove("hidden");
        updateProgressUI({ completed: 0, target: payload.target, success: 0, failed: 0 });
        
        terminalBody.innerHTML = '<div class="terminal-line system">Memulai koneksi ke server...</div>';

        fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                startStreaming();
            } else {
                appendTerminalLine(`Gagal memulai pekerjaan: ${data.message}`, "error");
                setIsRunning(false);
            }
        })
        .catch(err => {
            console.error("Gagal menghubungi API start:", err);
            appendTerminalLine("Gagal memanggil API Start Server.", "error");
            setIsRunning(false);
        });
    }

    // Stop execution
    function stopJob() {
        appendTerminalLine("Mengirim permintaan penghentian...", "warning");
        fetch("/api/stop", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    appendTerminalLine(`Penghentian gagal: ${data.message}`, "error");
                }
            })
            .catch(err => console.error("Gagal stop job:", err));
    }

    // Reset filled database history
    function resetHistory() {
        appendTerminalLine("Mereset database riwayat pengisian...", "warning");
        fetch("/api/reset-history", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    appendTerminalLine("Riwayat berhasil direset.", "success");
                    fetchStatus(); // Refresh stats
                } else {
                    appendTerminalLine(`Reset gagal: ${data.message}`, "error");
                }
            })
            .catch(err => {
                console.error("Gagal reset:", err);
                appendTerminalLine("Gagal mereset riwayat pengisian.", "error");
            });
    }

    // SSE EventSource listening
    function startStreaming() {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource("/api/stream");
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.text === "[FINISHED]") {
                appendTerminalLine("Proses streaming selesai.", "system");
                stopStreaming();
                setIsRunning(false);
                fetchStatus(); // Final status sync
                return;
            }

            appendTerminalLine(data.text, data.type, data.time);
        };

        eventSource.onerror = (err) => {
            console.error("EventSource Error:", err);
            appendTerminalLine("Koneksi log terputus. Mencoba menghubungkan kembali...", "warning");
        };

        // Poll status every 1.5 seconds to sync dashboard bars
        if (statusInterval) clearInterval(statusInterval);
        statusInterval = setInterval(() => {
            fetchStatus();
        }, 1500);
    }

    function stopStreaming() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
    }

    // Append a line in terminal box
    function appendTerminalLine(text, type = "info", timeStr = null) {
        if (!timeStr) {
            const now = new Date();
            const pad = (n) => String(n).padStart(2, '0');
            timeStr = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        }

        const line = document.createElement("div");
        line.className = `terminal-line ${type}`;
        
        const timeSpan = document.createElement("span");
        timeSpan.className = "line-time";
        timeSpan.textContent = `[${timeStr}] `;
        
        line.appendChild(timeSpan);
        line.appendChild(document.createTextNode(text));
        
        terminalBody.appendChild(line);

        if (isAutoscroll) {
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }
    }
});
