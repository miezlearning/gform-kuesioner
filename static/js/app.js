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
    
    // Questions Section Elements
    const btnScanForm = document.getElementById("btn-scan-form");
    const questionsSection = document.getElementById("questions-section");
    const questionsWrapper = document.getElementById("questions-wrapper");
    const questionsList = document.getElementById("questions-list");
    const btnToggleQuestions = document.getElementById("btn-toggle-questions");
    const toggleText = document.getElementById("toggle-text");
    const btnResetRules = document.getElementById("btn-reset-rules");
    const badgeQuestionCount = document.getElementById("badge-question-count");
    const formInfoSubtitle = document.getElementById("form-info-subtitle");
    
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
    let formQuestions = [];
    let questionRules = {}; // { entry_id: rule_object }
    let isQuestionsCollapsed = false;
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
        // Scan Form questions
        if (btnScanForm) {
            btnScanForm.addEventListener("click", () => {
                const url = formUrlInput.value.trim();
                if (url) fetchFormStructure(url);
            });
        }

        // Toggle questions panel collapse
        if (btnToggleQuestions) {
            btnToggleQuestions.addEventListener("click", toggleQuestionsView);
        }

        // Reset all rules to smart default
        if (btnResetRules) {
            btnResetRules.addEventListener("click", resetAllRules);
        }

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

                    // Auto fetch form structure
                    if (data.default_url) {
                        fetchFormStructure(data.default_url);
                    }
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
            if (btnScanForm) btnScanForm.disabled = true;
            if (btnResetRules) btnResetRules.disabled = true;
            
            // Disable settings input during run
            formUrlInput.disabled = true;
            targetInput.disabled = true;
            delayMinInput.disabled = true;
            delayMaxInput.disabled = true;
            distributionRadios.forEach(r => r.disabled = true);
            document.querySelectorAll(".weight-val-input").forEach(i => i.disabled = true);
            document.querySelectorAll('input[type="range"]').forEach(r => r.disabled = true);
            document.querySelectorAll(".rule-select").forEach(s => s.disabled = true);
            document.querySelectorAll(".rule-input").forEach(i => i.disabled = true);
        } else {
            btnStart.classList.remove("hidden");
            btnStop.classList.add("hidden");
            btnResetHistory.disabled = false;
            btnSelectAll.disabled = false;
            btnDeselectAll.disabled = false;
            if (btnScanForm) btnScanForm.disabled = false;
            if (btnResetRules) btnResetRules.disabled = false;
            
            formUrlInput.disabled = false;
            targetInput.disabled = false;
            delayMinInput.disabled = false;
            delayMaxInput.disabled = false;
            distributionRadios.forEach(r => r.disabled = false);
            document.querySelectorAll(".weight-val-input").forEach(i => i.disabled = false);
            document.querySelectorAll('input[type="range"]').forEach(r => r.disabled = false);
            document.querySelectorAll(".rule-select").forEach(s => s.disabled = false);
            document.querySelectorAll(".rule-input").forEach(i => i.disabled = false);
        }
    }

    // Start questionnaire filler process
    function startJob() {
        const mode = document.querySelector('input[name="distribution-mode"]:checked').value;
        const payload = {
            url: formUrlInput.value.trim ? formUrlInput.value.trim() : formUrlInput.value,
            target: parseInt(targetInput.value),
            min_delay: parseInt(delayMinInput.value),
            max_delay: parseInt(delayMaxInput.value),
            mode: mode,
            cohorts: Array.from(checkedCohorts),
            weights: {},
            question_rules: questionRules
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

    // ==================== FORM QUESTIONS & RULE ENGINE ====================

    // Fetch and extract form questions from backend
    function fetchFormStructure(url) {
        if (!url) return;
        
        if (badgeQuestionCount) badgeQuestionCount.textContent = "Memindai...";
        if (formInfoSubtitle) formInfoSubtitle.textContent = "Sedang mengekstrak seluruh pertanyaan...";
        if (questionsList) {
            questionsList.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fa-solid fa-circle-notch fa-spin"></i> Sedang membaca struktur form & daftar pertanyaan...
                </div>
            `;
        }

        fetch("/api/parse-form", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                formQuestions = data.questions || [];
                if (badgeQuestionCount) badgeQuestionCount.textContent = `${formQuestions.length} Pertanyaan`;
                if (formInfoSubtitle) formInfoSubtitle.innerHTML = `<strong>${data.form_title}</strong> (${data.num_pages} Halaman${data.has_email_page ? ' + Email' : ''})`;
                
                // Initialize default rules from backend suggested rules
                questionRules = {};
                formQuestions.forEach(q => {
                    questionRules[q.entry_id] = q.suggested_rule || { mode: "auto" };
                });

                renderQuestions();
                appendTerminalLine(`Form "${data.form_title}" berhasil dimuat: ${formQuestions.length} pertanyaan terdeteksi.`, "success");
            } else {
                if (badgeQuestionCount) badgeQuestionCount.textContent = "Gagal";
                if (formInfoSubtitle) formInfoSubtitle.textContent = data.message || "Gagal memuat form";
                if (questionsList) {
                    questionsList.innerHTML = `
                        <div class="loading-placeholder">
                            <i class="fa-solid fa-triangle-exclamation" style="color: var(--color-error)"></i> ${data.message || "Gagal membaca struktur Google Form."}
                        </div>
                    `;
                }
                appendTerminalLine(`Gagal membaca form: ${data.message}`, "error");
            }
        })
        .catch(err => {
            console.error("Gagal parse form:", err);
            if (badgeQuestionCount) badgeQuestionCount.textContent = "Error";
            if (formInfoSubtitle) formInfoSubtitle.textContent = "Terjadi kesalahan saat menghubungi server";
            if (questionsList) {
                questionsList.innerHTML = `
                    <div class="loading-placeholder">
                        <i class="fa-solid fa-triangle-exclamation" style="color: var(--color-error)"></i> Terjadi kesalahan koneksi saat membaca struktur form.
                    </div>
                `;
            }
            appendTerminalLine("Gagal memanggil API /api/parse-form.", "error");
        });
    }

    // Toggle collapse of questions panel
    function toggleQuestionsView() {
        isQuestionsCollapsed = !isQuestionsCollapsed;
        if (questionsWrapper) questionsWrapper.classList.toggle("collapsed", isQuestionsCollapsed);
        if (btnToggleQuestions) {
            btnToggleQuestions.innerHTML = isQuestionsCollapsed ? 
                '<i class="fa-solid fa-chevron-down"></i> <span id="toggle-text">Bentangkan</span>' : 
                '<i class="fa-solid fa-chevron-up"></i> <span id="toggle-text">Ciutkan</span>';
        }
    }

    // Reset all rules back to suggested defaults
    function resetAllRules() {
        questionRules = {};
        formQuestions.forEach(q => {
            questionRules[q.entry_id] = q.suggested_rule || { mode: "auto" };
        });
        renderQuestions();
        appendTerminalLine("Aturan seluruh pertanyaan berhasil direset ke rekomendasi otomatis.", "info");
    }

    // Render questions grouped by section / page
    function renderQuestions() {
        if (!questionsList) return;

        if (!formQuestions || formQuestions.length === 0) {
            questionsList.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fa-solid fa-circle-question"></i> Tidak ada pertanyaan yang terdeteksi pada form ini.
                </div>
            `;
            return;
        }

        // Group by page_index
        const pageGroups = {};
        formQuestions.forEach(q => {
            const pIdx = q.page_index || 0;
            if (!pageGroups[pIdx]) {
                pageGroups[pIdx] = {
                    title: q.section_title || `Halaman ${pIdx + 1}`,
                    questions: []
                };
            }
            pageGroups[pIdx].questions.push(q);
        });

        questionsList.innerHTML = "";

        let globalIndex = 1;
        Object.keys(pageGroups).forEach(pIdx => {
            const grp = pageGroups[pIdx];
            const groupEl = document.createElement("div");
            groupEl.className = "page-group";
            
            groupEl.innerHTML = `
                <div class="page-group-header">
                    <div class="page-group-title">
                        <i class="fa-regular fa-file-lines"></i>
                        <span>${grp.title} (Halaman ${parseInt(pIdx) + 1})</span>
                    </div>
                    <span class="badge-count">${grp.questions.length} Pertanyaan</span>
                </div>
                <div class="page-questions"></div>
            `;

            const questionsContainer = groupEl.querySelector(".page-questions");

            grp.questions.forEach(q => {
                const currentRule = questionRules[q.entry_id] || q.suggested_rule || { mode: "auto" };
                const isCustom = currentRule.mode !== "auto";
                
                // Determine type badge styling
                let typeBadgeClass = "type-text";
                if (q.type === 5) typeBadgeClass = "type-scale";
                else if (q.type === 2 || q.type === 3) typeBadgeClass = "type-radio";
                else if (q.type === 4) typeBadgeClass = "type-dropdown";

                const card = document.createElement("div");
                card.className = `question-card ${isCustom ? 'customized' : ''}`;
                card.id = `q-card-${q.entry_id}`;

                let optionsPreviewHtml = "";
                if (q.options && q.options.length > 0) {
                    const displayOpts = q.options.slice(0, 7);
                    const rem = q.options.length - displayOpts.length;
                    optionsPreviewHtml = `
                        <div class="question-options-preview">
                            ${displayOpts.map(o => `<span class="option-pill">${o}</span>`).join('')}
                            ${rem > 0 ? `<span class="option-pill" title="Dan ${rem} opsi lainnya...">+${rem} lainnya</span>` : ''}
                        </div>
                    `;
                } else if (q.scale_bounds) {
                    const sb = q.scale_bounds;
                    optionsPreviewHtml = `
                        <div class="scale-preview">
                            <i class="fa-solid fa-sliders"></i>
                            <span>Skala: ${sb.min} ${sb.min_label ? `(${sb.min_label})` : ''} s/d ${sb.max} ${sb.max_label ? `(${sb.max_label})` : ''}</span>
                        </div>
                    `;
                }

                // Build rule select options
                card.innerHTML = `
                    <div class="question-header">
                        <div class="question-title-area">
                            <span class="q-num">#${globalIndex}</span>
                            <span class="q-title">${q.label}${q.required ? '<span class="q-required" title="Wajib diisi">*</span>' : ''}</span>
                        </div>
                        <div class="q-badges">
                            <span class="q-type-badge ${typeBadgeClass}">${q.type_name}</span>
                        </div>
                    </div>
                    ${optionsPreviewHtml}
                    <div class="question-controls">
                        <span class="control-label"><i class="fa-solid fa-sliders"></i> Aturan:</span>
                        <select class="rule-select" id="rule-mode-${q.entry_id}">
                            <option value="auto">🧠 Otomatis (Rekomendasi Cerdas)</option>
                            <option value="csv_col:nama">👤 Nama Mahasiswa (CSV)</option>
                            <option value="csv_col:nim">🆔 NIM Mahasiswa (CSV)</option>
                            <option value="csv_col:angkatan">🎓 Angkatan Mahasiswa (CSV)</option>
                            <option value="email">📧 Email Mahasiswa</option>
                            <option value="csv_col:program studi">🏛️ Program Studi (CSV)</option>
                            <option value="csv_col:fakultas">🏛️ Fakultas (CSV)</option>
                            <option value="scale:auto">⭐ Skala: Sesuai Profil Kepuasan</option>
                            <option value="scale:sangat_puas">⭐ Skala: Cenderung 4 - 5 (Sangat Puas)</option>
                            <option value="scale:puas_rata_rata">⭐ Skala: Cenderung 3 - 4 (Puas Rata-rata)</option>
                            <option value="scale:kritis">⭐ Skala: Kritis (2 - 3)</option>
                            <option value="scale:fixed_5">⭐ Skala: Selalu 5 (Maksimal)</option>
                            <option value="scale:fixed_4">⭐ Skala: Selalu 4</option>
                            <option value="scale:random_4_5">⭐ Skala: Acak 4 atau 5</option>
                            <option value="fixed_option">🔘 Pilih Opsi Tertentu...</option>
                            <option value="random_option">🎲 Acak dari Opsi Form</option>
                            <option value="fixed_text">✍️ Teks Tetap (Input Manual)...</option>
                            <option value="ai_review:pendapat">🤖 AI: Ulasan / Pendapat Positif</option>
                            <option value="ai_review:saran">🤖 AI: Saran Perbaikan</option>
                        </select>
                        <div class="rule-sub-control" id="sub-ctrl-${q.entry_id}"></div>
                    </div>
                `;

                // Handle sub-controls and select synchronization
                const ruleSelect = card.querySelector(`#rule-mode-${q.entry_id}`);
                const subCtrl = card.querySelector(`#sub-ctrl-${q.entry_id}`);

                // Map currentRule to select value
                let selectedVal = "auto";
                if (currentRule.mode === "csv_col") {
                    selectedVal = `csv_col:${currentRule.column || 'nama'}`;
                } else if (currentRule.mode === "scale") {
                    selectedVal = `scale:${currentRule.profile || 'auto'}`;
                } else if (currentRule.mode === "ai_review") {
                    selectedVal = `ai_review:${currentRule.category || 'pendapat'}`;
                } else if (currentRule.mode === "email") {
                    selectedVal = "email";
                } else if (currentRule.mode === "fixed_option") {
                    selectedVal = "fixed_option";
                } else if (currentRule.mode === "fixed_text") {
                    selectedVal = "fixed_text";
                } else if (currentRule.mode === "random_option") {
                    selectedVal = "random_option";
                }

                if (ruleSelect.querySelector(`option[value="${selectedVal}"]`)) {
                    ruleSelect.value = selectedVal;
                } else {
                    ruleSelect.value = "auto";
                }

                // Render sub-control if needed
                function updateSubControl(val) {
                    subCtrl.innerHTML = "";
                    if (val === "fixed_option") {
                        if (q.options && q.options.length > 0) {
                            const optSelect = document.createElement("select");
                            optSelect.className = "rule-select";
                            q.options.forEach(opt => {
                                const o = document.createElement("option");
                                o.value = opt;
                                o.textContent = opt;
                                if (currentRule.value === opt) o.selected = true;
                                optSelect.appendChild(o);
                            });
                            optSelect.addEventListener("change", (e) => {
                                questionRules[q.entry_id] = { mode: "fixed_option", value: e.target.value };
                                card.classList.add("customized");
                            });
                            subCtrl.appendChild(optSelect);
                            questionRules[q.entry_id] = { mode: "fixed_option", value: optSelect.value };
                        } else {
                            subCtrl.innerHTML = '<span style="font-size:0.75rem; color:var(--color-warning);">Tidak ada opsi pada pertanyaan ini</span>';
                        }
                    } else if (val === "fixed_text") {
                        const txtInput = document.createElement("input");
                        txtInput.type = "text";
                        txtInput.className = "rule-input";
                        txtInput.placeholder = "Ketik jawaban teks...";
                        txtInput.value = currentRule.value || "";
                        txtInput.addEventListener("input", (e) => {
                            questionRules[q.entry_id] = { mode: "fixed_text", value: e.target.value };
                            card.classList.add("customized");
                        });
                        subCtrl.appendChild(txtInput);
                    }
                }

                updateSubControl(ruleSelect.value);

                ruleSelect.addEventListener("change", (e) => {
                    const chosen = e.target.value;
                    card.classList.toggle("customized", chosen !== "auto");
                    
                    if (chosen.startsWith("csv_col:")) {
                        const col = chosen.split(":")[1];
                        questionRules[q.entry_id] = { mode: "csv_col", column: col };
                    } else if (chosen.startsWith("scale:")) {
                        const prof = chosen.split(":")[1];
                        questionRules[q.entry_id] = { mode: "scale", profile: prof };
                    } else if (chosen.startsWith("ai_review:")) {
                        const cat = chosen.split(":")[1];
                        questionRules[q.entry_id] = { mode: "ai_review", category: cat };
                    } else if (chosen === "email") {
                        questionRules[q.entry_id] = { mode: "email" };
                    } else if (chosen === "random_option") {
                        questionRules[q.entry_id] = { mode: "random_option" };
                    } else if (chosen === "auto") {
                        questionRules[q.entry_id] = q.suggested_rule || { mode: "auto" };
                    }
                    
                    updateSubControl(chosen);
                });

                questionsContainer.appendChild(card);
                globalIndex++;
            });

            questionsList.appendChild(groupEl);
        });
    }
});
