// ==========================================================================
// FormPilot Studio - Universal Form Automation App Logic
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // --- State Variables ---
    let cohortsData = [];
    let checkedCohorts = new Set();
    let customWeights = {};
    let formQuestions = [];
    let questionRules = {};
    let isRunning = false;
    let isAutoscroll = true;
    let eventSource = null;
    let activeTermFilter = "all";
    let activeQuestionFilter = "all";
    let historyData = [];

    // --- DOM Elements ---
    // Navigation
    const navTabs = document.querySelectorAll(".nav-tab");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const tabQuestionsBadge = document.getElementById("tab-questions-badge");
    const tabCohortsBadge = document.getElementById("tab-cohorts-badge");
    const tabHistoryBadge = document.getElementById("tab-history-badge");
    const statusText = document.getElementById("status-text");
    const statusDot = document.querySelector(".status-dot");
    const runnerLiveDot = document.getElementById("runner-live-dot");

    // Quick Actions
    const btnQuickStart = document.getElementById("btn-quick-start");
    const btnQuickStop = document.getElementById("btn-quick-stop");

    // Tab 1: Form Inspector
    const formUrlInput = document.getElementById("form-url");
    const btnScanForm = document.getElementById("btn-scan-form");
    const formMetaCard = document.getElementById("form-meta-card");
    const metaFormTitle = document.getElementById("meta-form-title");
    const metaFormPages = document.getElementById("meta-form-pages");
    const metaFormCount = document.getElementById("meta-form-count");
    const metaFormEmail = document.getElementById("meta-form-email");
    const metaFormDesc = document.getElementById("meta-form-desc");
    const questionsList = document.getElementById("questions-list");
    const filterQuestionSearch = document.getElementById("filter-question-search");
    const questionFilterPills = document.querySelectorAll(".filter-pill");
    const btnExpandAll = document.getElementById("btn-expand-all");
    const btnCollapseAll = document.getElementById("btn-collapse-all");
    const btnResetRules = document.getElementById("btn-reset-rules");

    // Tab 2: Datasets & Targets
    const cohortsGrid = document.getElementById("cohorts-grid");
    const btnSelectAll = document.getElementById("btn-select-all");
    const btnDeselectAll = document.getElementById("btn-deselect-all");
    const targetInput = document.getElementById("target-submissions");
    const presetBtns = document.querySelectorAll(".preset-btn");
    const delayMinInput = document.getElementById("delay-min");
    const delayMaxInput = document.getElementById("delay-max");
    const delayUnitSelect = document.getElementById("delay-unit");
    const delayEquivalentBadge = document.getElementById("delay-equivalent-badge");
    const delayEstimationHint = document.getElementById("delay-estimation-hint");
    const delayPresetBtns = document.querySelectorAll(".delay-preset-btn");
    const distributionRadios = document.getElementsByName("distribution-mode");
    const customWeightAlert = document.getElementById("custom-weight-alert");
    const weightTotalPercentage = document.getElementById("weight-total-percentage");
    const weightValidationMsg = document.getElementById("weight-validation-msg");

    // Tab 3: Execution Studio & Terminal
    const btnStart = document.getElementById("btn-start");
    const btnStop = document.getElementById("btn-stop");
    const runnerBadgeStatus = document.getElementById("runner-badge-status");
    const runnerBadgeText = document.getElementById("runner-badge-text");
    const runnerStatusBullet = document.getElementById("runner-status-bullet");
    const runnerActiveInfo = document.getElementById("runner-active-info");
    const metricCompleted = document.getElementById("metric-completed");
    const metricTotal = document.getElementById("metric-total");
    const metricSuccess = document.getElementById("metric-success");
    const metricFailed = document.getElementById("metric-failed");
    const metricRemaining = document.getElementById("metric-remaining");
    const progressBarFill = document.getElementById("progress-bar-fill");
    const progressPercentText = document.getElementById("progress-percent-text");
    const progressStatusDesc = document.getElementById("progress-status-desc");
    const terminalBody = document.getElementById("terminal-body");
    const consoleIndicator = document.getElementById("console-indicator");
    const terminalLineCount = document.getElementById("terminal-line-count");
    const btnClearTerminal = document.getElementById("btn-clear-terminal");
    const btnCopyTerminal = document.getElementById("btn-copy-terminal");
    const btnToggleAutoscroll = document.getElementById("btn-toggle-autoscroll");
    const termTabs = document.querySelectorAll(".term-tab");

    // Tab 4: History & Analytics
    const historyTableBody = document.getElementById("history-table-body");
    const historySearchInput = document.getElementById("history-search-input");
    const historyTotalCount = document.getElementById("history-total-count");
    const btnRefreshHistory = document.getElementById("btn-refresh-history");
    const btnExportHistory = document.getElementById("btn-export-history");
    const btnResetHistory = document.getElementById("btn-reset-history");

    // Modal & Toast
    const modalConfirm = document.getElementById("modal-confirm");
    const btnConfirmCancel = document.getElementById("btn-confirm-cancel");
    const btnConfirmReset = document.getElementById("btn-confirm-reset");
    const modalDetail = document.getElementById("modal-detail");
    const modalDetailTitle = document.getElementById("modal-detail-title");
    const modalDetailSubtitle = document.getElementById("modal-detail-subtitle");
    const modalDetailBody = document.getElementById("modal-detail-body");
    const btnCloseDetail = document.getElementById("btn-close-detail");
    const btnCopyAnswers = document.getElementById("btn-copy-answers");
    const toastContainer = document.getElementById("toast-container");
    let currentDetailItem = null;

    // Initialize Studio
    init();

    function init() {
        setupTabs();
        setupEventListeners();
        fetchStatus(true);
        loadHistory();
        renderIcons();
    }

    function renderIcons() {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // --- Toast Notifications ---
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        let iconName = "info";
        if (type === "success") iconName = "check-circle";
        if (type === "error") iconName = "alert-circle";
        
        toast.innerHTML = `<i data-lucide="${iconName}"></i> <span>${message}</span>`;
        toastContainer.appendChild(toast);
        renderIcons();

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(20px)";
            toast.style.transition = "all 0.25s ease";
            setTimeout(() => toast.remove(), 250);
        }, 3500);
    }

    // --- Tab Navigation System ---
    function setupTabs() {
        navTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                switchTab(tab.getAttribute("data-tab"));
            });
        });
    }

    function switchTab(tabId) {
        navTabs.forEach(t => {
            const isActive = t.getAttribute("data-tab") === tabId;
            t.classList.toggle("active", isActive);
            t.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        tabPanels.forEach(p => {
            p.classList.toggle("active", p.id === tabId);
        });

        renderIcons();
    }

    // --- Event Listeners ---
    function setupEventListeners() {
        // Scan Form
        btnScanForm.addEventListener("click", () => {
            const url = formUrlInput.value.trim();
            if (!url) {
                showToast("Silakan masukkan URL Google Form terlebih dahulu.", "error");
                formUrlInput.focus();
                return;
            }
            fetchFormStructure(url);
        });

        formUrlInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                btnScanForm.click();
            }
        });

        // Filter Pertanyaan
        filterQuestionSearch.addEventListener("input", (e) => {
            filterQuestions(e.target.value.toLowerCase(), activeQuestionFilter);
        });

        questionFilterPills.forEach(pill => {
            pill.addEventListener("click", () => {
                questionFilterPills.forEach(p => p.classList.remove("active"));
                pill.classList.add("active");
                activeQuestionFilter = pill.getAttribute("data-filter");
                filterQuestions(filterQuestionSearch.value.toLowerCase(), activeQuestionFilter);
            });
        });

        // Expand / Collapse Cards
        btnExpandAll.addEventListener("click", () => toggleAllQuestions(true));
        btnCollapseAll.addEventListener("click", () => toggleAllQuestions(false));
        btnResetRules.addEventListener("click", resetAllRules);

        // Target Preset Buttons
        presetBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                targetInput.value = btn.getAttribute("data-val");
            });
        });

        // Delay Timing & Rate Limit (Detik, Menit, Jam)
        function updateDelayDisplay() {
            if (!delayMinInput || !delayMaxInput || !delayUnitSelect) return;
            const minVal = parseFloat(delayMinInput.value) || 1;
            const maxVal = parseFloat(delayMaxInput.value) || minVal;
            const unit = delayUnitSelect.value;

            let unitLabel = "detik";
            let multiplier = 1;
            if (unit === "menit") {
                unitLabel = "menit";
                multiplier = 60;
            } else if (unit === "jam") {
                unitLabel = "jam";
                multiplier = 3600;
            }

            if (delayEquivalentBadge) {
                if (unit === "detik") {
                    delayEquivalentBadge.textContent = `${minVal} — ${maxVal} detik per responden`;
                } else {
                    const secMin = Math.round(minVal * multiplier);
                    const secMax = Math.round(maxVal * multiplier);
                    delayEquivalentBadge.textContent = `${minVal} — ${maxVal} ${unitLabel} (≈ ${secMin}s - ${secMax}s)`;
                }
            }

            if (delayEstimationHint) {
                if (unit === "jam") {
                    delayEstimationHint.textContent = `Pola pengisian berkala panjang: jeda ${minVal} s/d ${maxVal} jam antar responden cocok untuk menyebar kuesioner sepanjang hari/minggu.`;
                } else if (unit === "menit") {
                    delayEstimationHint.textContent = `Pola pengisian santai alami: jeda ${minVal} s/d ${maxVal} menit antar responden menyerupai pengisian kuesioner asli oleh mahasiswa.`;
                } else {
                    delayEstimationHint.textContent = `Durasi jeda diacak di antara ${minVal} dan ${maxVal} detik untuk meniru jeda pengetikan responden.`;
                }
            }
        }

        if (delayMinInput) delayMinInput.addEventListener("input", updateDelayDisplay);
        if (delayMaxInput) delayMaxInput.addEventListener("input", updateDelayDisplay);
        if (delayUnitSelect) delayUnitSelect.addEventListener("change", updateDelayDisplay);

        delayPresetBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                delayPresetBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                const min = btn.getAttribute("data-min");
                const max = btn.getAttribute("data-max");
                const unit = btn.getAttribute("data-unit");
                if (delayMinInput) delayMinInput.value = min;
                if (delayMaxInput) delayMaxInput.value = max;
                if (delayUnitSelect) delayUnitSelect.value = unit;
                updateDelayDisplay();
            });
        });
        updateDelayDisplay();

        // Cohort Selection Controls
        btnSelectAll.addEventListener("click", () => {
            checkedCohorts = new Set(cohortsData.map(c => c.cohort));
            updateCohortsUI();
        });

        btnDeselectAll.addEventListener("click", () => {
            checkedCohorts.clear();
            updateCohortsUI();
        });

        // Distribution Mode
        distributionRadios.forEach(radio => {
            radio.addEventListener("change", (e) => {
                toggleWeightControls(e.target.value === "kustom");
                validateWeights();
            });
        });

        // Start & Stop Triggers
        btnStart.addEventListener("click", startFilling);
        btnQuickStart.addEventListener("click", () => {
            switchTab("tab-runner");
            startFilling();
        });

        btnStop.addEventListener("click", stopFilling);
        btnQuickStop.addEventListener("click", stopFilling);

        // Terminal Tools
        btnClearTerminal.addEventListener("click", () => {
            terminalBody.innerHTML = `<div class="terminal-line system"><span class="term-time">[${getCurrentTime()}]</span><span class="term-tag">[SYSTEM]</span><span class="term-text">Terminal dibersihkan.</span></div>`;
            if (terminalLineCount) terminalLineCount.textContent = "1 baris";
        });

        btnCopyTerminal.addEventListener("click", () => {
            const text = terminalBody.innerText;
            navigator.clipboard.writeText(text).then(() => {
                showToast("Log terminal berhasil disalin ke clipboard.", "success");
            });
        });

        btnToggleAutoscroll.addEventListener("click", () => {
            isAutoscroll = !isAutoscroll;
            btnToggleAutoscroll.classList.toggle("active", isAutoscroll);
            showToast(`Auto-scroll ${isAutoscroll ? "diaktifkan" : "dinonaktifkan"}.`, "info");
        });

        termTabs.forEach(tab => {
            tab.addEventListener("click", () => {
                termTabs.forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                activeTermFilter = tab.getAttribute("data-filter");
                filterTerminalLogs();
            });
        });

        // History Tools
        btnRefreshHistory.addEventListener("click", loadHistory);
        btnExportHistory.addEventListener("click", exportHistoryCSV);
        btnResetHistory.addEventListener("click", () => modalConfirm.classList.remove("hidden"));
        btnConfirmCancel.addEventListener("click", () => modalConfirm.classList.add("hidden"));
        btnConfirmReset.addEventListener("click", confirmResetHistory);

        // Detail Modal
        if (btnCloseDetail) {
            btnCloseDetail.addEventListener("click", () => modalDetail.classList.add("hidden"));
        }
        if (modalDetail) {
            modalDetail.addEventListener("click", (e) => {
                if (e.target === modalDetail) modalDetail.classList.add("hidden");
            });
        }
        if (btnCopyAnswers) {
            btnCopyAnswers.addEventListener("click", () => {
                if (!currentDetailItem) return;
                navigator.clipboard.writeText(JSON.stringify(currentDetailItem, null, 2)).then(() => {
                    showToast("Data submisi berhasil disalin dalam format JSON.", "success");
                });
            });
        }

        historySearchInput.addEventListener("input", (e) => {
            renderHistoryTable(e.target.value.toLowerCase());
        });
    }

    // --- API Interactions ---
    function fetchStatus(isInitial = false) {
        fetch("/api/status")
            .then(res => res.json())
            .then(data => {
                if (isInitial) {
                    if (data.default_url) formUrlInput.value = data.default_url;
                    if (data.default_target) targetInput.value = data.default_target;
                    if (data.default_delay_min !== undefined) delayMinInput.value = data.default_delay_min;
                    if (data.default_delay_max !== undefined) delayMaxInput.value = data.default_delay_max;

                    // Auto-scan initial form if present
                    if (data.default_url) {
                        fetchFormStructure(data.default_url);
                    }
                }

                cohortsData = data.stats || [];
                tabCohortsBadge.textContent = cohortsData.length;

                if (checkedCohorts.size === 0 && cohortsData.length > 0) {
                    // Default: Pilih dataset kesehatan atau dataset pertama
                    const defaultCohort = cohortsData.find(c => c.cohort.includes("kesehatan")) || cohortsData[0];
                    checkedCohorts.add(defaultCohort.cohort);
                }

                renderCohortsCards();

                // Periksa apakah server sedang menjalankan task
                if (data.is_running) {
                    setExecutionRunning(true);
                    updateProgressUI(data.job_progress);
                    if (!eventSource) startSSEStream();
                } else {
                    if (isRunning) setExecutionRunning(false);
                }
            })
            .catch(err => {
                console.error("Gagal mengambil status:", err);
                statusText.textContent = "Koneksi Terputus";
                statusDot.className = "status-dot";
            });
    }

    function fetchFormStructure(url) {
        btnScanForm.disabled = true;
        btnScanForm.innerHTML = `<i data-lucide="loader-2" class="spin"></i> <span>Menganalisis...</span>`;
        renderIcons();

        fetch("/api/parse-form", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        })
        .then(res => res.json())
        .then(data => {
            btnScanForm.disabled = false;
            btnScanForm.innerHTML = `<i data-lucide="scan"></i> <span>Baca & Analisis Form</span>`;
            renderIcons();

            if (data.success) {
                questionRules = {};
                formQuestions = data.questions || [];
                tabQuestionsBadge.textContent = formQuestions.length;
                tabQuestionsBadge.classList.remove("hidden");

                // Render Metadata
                metaFormTitle.textContent = data.form_title || "Formulir Google";
                metaFormPages.textContent = `${data.num_pages || 1} Halaman`;
                metaFormCount.textContent = `${formQuestions.length} Pertanyaan`;
                metaFormEmail.textContent = data.has_email_page ? "Wajib Diisi" : "Tidak";
                metaFormDesc.textContent = data.form_description || "Formulir tidak memiliki deskripsi tambahan.";
                formMetaCard.classList.remove("hidden");

                renderQuestionsList();
                showToast(`Form berhasil dianalisis: ${formQuestions.length} pertanyaan terdeteksi.`, "success");
            } else {
                showToast(data.message || "Gagal membaca struktur formulir.", "error");
            }
        })
        .catch(err => {
            btnScanForm.disabled = false;
            btnScanForm.innerHTML = `<i data-lucide="scan"></i> <span>Baca & Analisis Form</span>`;
            renderIcons();
            showToast("Terjadi kesalahan jaringan saat membaca form.", "error");
        });
    }

    // --- Render Questions Studio (Tab 1) ---
    function renderQuestionsList() {
        if (!formQuestions || formQuestions.length === 0) {
            questionsList.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="file-x" class="empty-icon"></i>
                    <h3>Tidak Ada Pertanyaan Terdeteksi</h3>
                    <p>Pastikan tautan Google Form publik dan dapat diakses tanpa login terbatas organisasi.</p>
                </div>
            `;
            renderIcons();
            return;
        }

        questionsList.innerHTML = "";
        formQuestions.forEach((q, idx) => {
            const entryId = String(q.entry_id);
            const defaultRule = q.suggested_rule || { mode: "auto" };
            if (!questionRules[entryId]) {
                questionRules[entryId] = { ...defaultRule };
            }

            const currentRule = questionRules[entryId];
            const card = document.createElement("div");
            card.className = "question-card";
            card.setAttribute("data-id", entryId);
            card.setAttribute("data-type", getQuestionTypeCategory(q.type));

            const typeLabel = q.type_name || `Type ${q.type}`;
            const reqBadge = q.required ? `<span class="badge badge-amber"><i data-lucide="asterisk"></i> Wajib</span>` : `<span class="badge badge-zinc">Opsional</span>`;

            card.innerHTML = `
                <div class="question-card-header" onclick="this.parentElement.classList.toggle('active')">
                    <div class="question-card-left">
                        <span class="question-num-badge">Q${idx + 1}</span>
                        <div class="question-title-group">
                            <span class="question-label">${escapeHtml(q.label)}${q.required ? '<span class="question-req-star">*</span>' : ''}</span>
                            <div class="question-tags">
                                <span class="badge badge-indigo">${typeLabel}</span>
                                ${reqBadge}
                                <span class="badge badge-zinc font-mono">ID: ${entryId}</span>
                            </div>
                        </div>
                    </div>
                    <button type="button" class="btn-icon" title="Lihat Aturan">
                        <i data-lucide="chevron-down"></i>
                    </button>
                </div>
                <div class="question-card-body">
                    <div class="rule-selector-container">
                        <div>
                            <label class="form-label"><i data-lucide="zap"></i> Mode Jawaban:</label>
                            <select class="form-control rule-select" data-entry="${entryId}">
                                <option value="auto" ${currentRule.mode === 'auto' ? 'selected' : ''}>🤖 Otomatis Cerdas</option>
                                <option value="csv_col" ${currentRule.mode === 'csv_col' ? 'selected' : ''}>📂 Kolom Database CSV</option>
                                <option value="fixed_option" ${currentRule.mode === 'fixed_option' ? 'selected' : ''}>🎯 Opsi Pilihan Tetap</option>
                                <option value="random_option" ${currentRule.mode === 'random_option' ? 'selected' : ''}>🎲 Opsi Acak Alami</option>
                                <option value="scale" ${currentRule.mode === 'scale' ? 'selected' : ''}>📊 Skala Tertimbang</option>
                                <option value="ai_review" ${currentRule.mode === 'ai_review' ? 'selected' : ''}>✍️ AI Komentar / Saran</option>
                                <option value="fixed_text" ${currentRule.mode === 'fixed_text' ? 'selected' : ''}>✏️ Teks Kustom Tetap</option>
                            </select>
                        </div>
                        <div class="rule-sub-control" id="sub-ctrl-${entryId}">
                            <!-- Dynamic sub controls will be rendered here -->
                        </div>
                        <div class="rule-preview-pill" id="preview-${entryId}">
                            <span>Simulasi Nilai:</span>
                            <strong id="preview-val-${entryId}">[Auto-Detect]</strong>
                        </div>
                    </div>
                </div>
            `;

            questionsList.appendChild(card);
            renderSubControl(q, currentRule);
        });

        setupQuestionRuleEvents();
        renderIcons();
    }

    function getQuestionTypeCategory(typeCode) {
        if (typeCode === 2 || typeCode === 3) return "choice";
        if (typeCode === 5) return "scale";
        if (typeCode === 0 || typeCode === 1) return "text";
        if (typeCode === 4) return "checkbox";
        return "other";
    }

    function renderSubControl(question, rule) {
        const entryId = String(question.entry_id);
        const container = document.getElementById(`sub-ctrl-${entryId}`);
        if (!container) return;

        const options = question.options || [];
        const mode = rule.mode;

        if (mode === "csv_col") {
            const selectedCol = rule.column || "nama";
            container.innerHTML = `
                <label class="form-label"><i data-lucide="table"></i> Pilih Kolom:</label>
                <select class="form-control sub-input" data-entry="${entryId}" data-key="column">
                    <option value="nama" ${selectedCol === 'nama' ? 'selected' : ''}>Nama Mahasiswa</option>
                    <option value="nim" ${selectedCol === 'nim' ? 'selected' : ''}>NIM</option>
                    <option value="angkatan" ${selectedCol === 'angkatan' ? 'selected' : ''}>Angkatan / Tahun</option>
                    <option value="program studi" ${selectedCol === 'program studi' ? 'selected' : ''}>Program Studi</option>
                    <option value="fakultas" ${selectedCol === 'fakultas' ? 'selected' : ''}>Fakultas</option>
                    <option value="perguruan tinggi" ${selectedCol === 'perguruan tinggi' ? 'selected' : ''}>Perguruan Tinggi</option>
                </select>
            `;
        } else if (mode === "fixed_option") {
            if (options.length > 0) {
                const selectedOpt = rule.value || options[0];
                const optHtml = options.map(o => `<option value="${escapeHtml(o)}" ${o === selectedOpt ? 'selected' : ''}>${escapeHtml(o)}</option>`).join("");
                container.innerHTML = `
                    <label class="form-label"><i data-lucide="check"></i> Opsi Pilihan:</label>
                    <select class="form-control sub-input" data-entry="${entryId}" data-key="value">
                        ${optHtml}
                    </select>
                `;
            } else {
                container.innerHTML = `<span class="field-hint text-amber">Tidak ada pilihan opsi tersedia pada pertanyaan ini.</span>`;
            }
        } else if (mode === "scale") {
            const currentProf = rule.profile || "auto";
            container.innerHTML = `
                <label class="form-label"><i data-lucide="bar-chart-2"></i> Bobot Skala:</label>
                <select class="form-control sub-input" data-entry="${entryId}" data-key="profile">
                    <option value="auto" ${currentProf === 'auto' ? 'selected' : ''}>Ikuti Sentimen Global</option>
                    <option value="fixed_5" ${currentProf === 'fixed_5' ? 'selected' : ''}>Nilai Tertinggi / Sangat Sesuai</option>
                    <option value="fixed_4" ${currentProf === 'fixed_4' ? 'selected' : ''}>Nilai 4 / Sesuai</option>
                    <option value="random_4_5" ${currentProf === 'random_4_5' ? 'selected' : ''}>Variasi Positif (4 atau 5)</option>
                    <option value="fixed_3" ${currentProf === 'fixed_3' ? 'selected' : ''}>Nilai Netral / Rata-rata (3)</option>
                </select>
            `;
        } else if (mode === "ai_review") {
            const currentCat = rule.category || "pendapat";
            container.innerHTML = `
                <label class="form-label"><i data-lucide="bot"></i> Kategori AI:</label>
                <select class="form-control sub-input" data-entry="${entryId}" data-key="category">
                    <option value="pendapat" ${currentCat === 'pendapat' ? 'selected' : ''}>Tanggapan Positif / Kesan Baik</option>
                    <option value="saran" ${currentCat === 'saran' ? 'selected' : ''}>Saran & Masukan Konstruktif</option>
                    <option value="context" ${currentCat === 'context' ? 'selected' : ''}>Jawaban Kontekstual Sesuai Pertanyaan</option>
                </select>
            `;
        } else if (mode === "fixed_text") {
            container.innerHTML = `
                <label class="form-label"><i data-lucide="edit-3"></i> Teks Jawaban:</label>
                <input type="text" class="form-control sub-input" data-entry="${entryId}" data-key="value" value="${escapeHtml(rule.value || '')}" placeholder="Masukkan jawaban tetap...">
            `;
        } else {
            container.innerHTML = `<span class="field-hint text-emerald">Sistem otomatis mendeteksi demografi & sentimen alami.</span>`;
        }

        renderIcons();
    }

    function setupQuestionRuleEvents() {
        document.querySelectorAll(".rule-select").forEach(select => {
            select.addEventListener("change", (e) => {
                const entryId = e.target.getAttribute("data-entry");
                const newMode = e.target.value;
                const question = formQuestions.find(q => String(q.entry_id) === entryId);

                questionRules[entryId] = { mode: newMode };
                renderSubControl(question, questionRules[entryId]);
            });
        });

        document.querySelectorAll(".sub-input").forEach(inp => {
            inp.addEventListener("change", (e) => {
                const entryId = e.target.getAttribute("data-entry");
                const key = e.target.getAttribute("data-key");
                if (questionRules[entryId]) {
                    questionRules[entryId][key] = e.target.value;
                }
            });
        });
    }

    function filterQuestions(searchVal, typeFilter) {
        document.querySelectorAll(".question-card").forEach(card => {
            const cardText = card.innerText.toLowerCase();
            const cardType = card.getAttribute("data-type");

            const matchesSearch = !searchVal || cardText.includes(searchVal);
            const matchesType = typeFilter === "all" || cardType === typeFilter;

            card.style.display = matchesSearch && matchesType ? "block" : "none";
        });
    }

    function toggleAllQuestions(expand) {
        document.querySelectorAll(".question-card").forEach(card => {
            card.classList.toggle("active", expand);
        });
    }

    function resetAllRules() {
        formQuestions.forEach(q => {
            const entryId = String(q.entry_id);
            questionRules[entryId] = { ...(q.suggested_rule || { mode: "auto" }) };
        });
        renderQuestionsList();
        showToast("Seluruh aturan pertanyaan dikembalikan ke rekomendasi cerdas.", "info");
    }

    // --- Render Datasets (Tab 2) ---
    function renderCohortsCards() {
        if (!cohortsData || cohortsData.length === 0) {
            cohortsGrid.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="database" class="empty-icon"></i>
                    <p>Tidak ada dataset ditemukan di folder <code>dataset/</code>.</p>
                </div>
            `;
            renderIcons();
            return;
        }

        cohortsGrid.innerHTML = "";
        cohortsData.forEach(c => {
            const card = document.createElement("div");
            const isChecked = checkedCohorts.has(c.cohort);
            card.className = `cohort-card ${isChecked ? 'selected' : ''}`;

            const percentFilled = c.total > 0 ? Math.round((c.filled / c.total) * 100) : 0;
            const badgeClass = c.remaining > 0 ? "has-data" : "empty";

            // Tag kategori data
            let tagBadge = "";
            if (c.cohort.includes("kesehatan")) tagBadge = `<span class="badge badge-emerald">Kesehatan</span>`;
            else if (c.cohort.includes("gratispol")) tagBadge = `<span class="badge badge-indigo">Beasiswa Kaltim</span>`;
            else if (c.cohort.includes("samba")) tagBadge = `<span class="badge badge-zinc">UNMUL Lengkap</span>`;

            card.innerHTML = `
                <div class="cohort-card-top">
                    <div class="cohort-name-group">
                        <input type="checkbox" class="cohort-checkbox" data-cohort="${c.cohort}" ${isChecked ? 'checked' : ''}>
                        <div>
                            <span class="cohort-title">${escapeHtml(c.cohort)}</span>
                            ${tagBadge}
                        </div>
                    </div>
                    <span class="cohort-remaining-badge ${badgeClass}">${c.remaining} Sisa</span>
                </div>
                <div class="cohort-stats-row">
                    <span>Terisi: ${c.filled} / ${c.total}</span>
                    <span>${percentFilled}%</span>
                </div>
                <div class="cohort-progress-mini">
                    <div class="cohort-progress-mini-fill" style="width: ${percentFilled}%;"></div>
                </div>
                <div class="cohort-weight-box hidden" id="weight-box-${c.cohort}">
                    <span>Bobot Distribusi:</span>
                    <input type="number" min="0" max="100" class="weight-input" data-cohort="${c.cohort}" value="${customWeights[c.cohort] || 0}"> %
                </div>
            `;

            // Card click toggle
            card.addEventListener("click", (e) => {
                if (e.target.tagName !== "INPUT") {
                    const cb = card.querySelector(".cohort-checkbox");
                    cb.checked = !cb.checked;
                    toggleCohort(c.cohort, cb.checked);
                }
            });

            const cb = card.querySelector(".cohort-checkbox");
            cb.addEventListener("change", (e) => {
                toggleCohort(c.cohort, e.target.checked);
            });

            cohortsGrid.appendChild(card);
        });

        setupWeightInputs();
        renderIcons();
    }

    function toggleCohort(cohort, isChecked) {
        if (isChecked) {
            checkedCohorts.add(cohort);
        } else {
            checkedCohorts.delete(cohort);
        }
        updateCohortsUI();
    }

    function updateCohortsUI() {
        document.querySelectorAll(".cohort-card").forEach(card => {
            const cb = card.querySelector(".cohort-checkbox");
            const cohort = cb.getAttribute("data-cohort");
            const isSelected = checkedCohorts.has(cohort);
            cb.checked = isSelected;
            card.classList.toggle("selected", isSelected);
        });
        validateWeights();
    }

    function toggleWeightControls(show) {
        document.querySelectorAll(".cohort-weight-box").forEach(box => {
            box.classList.toggle("hidden", !show);
        });
        customWeightAlert.classList.toggle("hidden", !show);
    }

    function setupWeightInputs() {
        document.querySelectorAll(".weight-input").forEach(inp => {
            inp.addEventListener("input", (e) => {
                const c = e.target.getAttribute("data-cohort");
                customWeights[c] = parseInt(e.target.value) || 0;
                validateWeights();
            });
        });
    }

    function validateWeights() {
        const mode = getSelectedDistributionMode();
        if (mode !== "kustom") {
            customWeightAlert.classList.add("hidden");
            return;
        }

        customWeightAlert.classList.remove("hidden");
        let total = 0;
        checkedCohorts.forEach(c => {
            total += customWeights[c] || 0;
        });

        weightTotalPercentage.textContent = `${total}%`;
        const isValid = total === 100;
        weightValidationMsg.classList.toggle("hidden", isValid);
        weightTotalPercentage.style.color = isValid ? "var(--emerald)" : "var(--rose)";
    }

    function getSelectedDistributionMode() {
        for (const radio of distributionRadios) {
            if (radio.checked) return radio.value;
        }
        return "rata";
    }

    function getSelectedSentimentProfile() {
        const radios = document.getElementsByName("sentiment-profile");
        for (const r of radios) {
            if (r.checked) return r.value;
        }
        return "puas_rata_rata";
    }

    // --- Execution Runner (Tab 3) ---
    function startFilling() {
        const url = formUrlInput.value.trim();
        const target = parseInt(targetInput.value);
        const delayMin = parseFloat(delayMinInput.value) || 2;
        const delayMax = parseFloat(delayMaxInput.value) || 5;
        const delayUnit = delayUnitSelect ? delayUnitSelect.value : "detik";
        const mode = getSelectedDistributionMode();
        const profile = getSelectedSentimentProfile();

        if (!url) {
            showToast("Harap isi URL Google Form terlebih dahulu.", "error");
            switchTab("tab-inspect");
            formUrlInput.focus();
            return;
        }

        if (checkedCohorts.size === 0) {
            showToast("Pilih minimal satu dataset mahasiswa di Tab 2.", "error");
            switchTab("tab-datasets");
            return;
        }

        if (mode === "kustom") {
            let totalW = 0;
            checkedCohorts.forEach(c => totalW += (customWeights[c] || 0));
            if (totalW !== 100) {
                showToast("Total bobot kustom harus bernilai 100%.", "error");
                switchTab("tab-datasets");
                return;
            }
        }

        // Siapkan payload ke backend
        const payload = {
            url: url,
            target: target,
            delay_min: delayMin,
            delay_max: delayMax,
            delay_unit: delayUnit,
            distribution_mode: mode,
            cohorts: Array.from(checkedCohorts),
            custom_weights: customWeights,
            sentiment_profile: profile,
            question_rules: questionRules
        };

        btnStart.disabled = true;
        btnQuickStart.disabled = true;

        fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            btnStart.disabled = false;
            btnQuickStart.disabled = false;

            if (data.success) {
                setExecutionRunning(true);
                switchTab("tab-runner");
                startSSEStream();
                showToast("Pengisian otomatis kuesioner berhasil dimulai!", "success");
            } else {
                showToast(data.message || "Gagal memulai pekerjaan.", "error");
            }
        })
        .catch(err => {
            btnStart.disabled = false;
            btnQuickStart.disabled = false;
            showToast("Gagal terhubung ke server backend.", "error");
        });
    }

    function stopFilling() {
        btnStop.disabled = true;
        btnQuickStop.disabled = true;

        fetch("/api/stop", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                btnStop.disabled = false;
                btnQuickStop.disabled = false;
                showToast("Perintah penghentian dikirim...", "info");
            })
            .catch(() => {
                btnStop.disabled = false;
                btnQuickStop.disabled = false;
            });
    }

    function setExecutionRunning(running) {
        isRunning = running;
        btnStart.classList.toggle("hidden", running);
        btnQuickStart.classList.toggle("hidden", running);
        btnStop.classList.remove("hidden");
        btnQuickStop.classList.remove("hidden");

        if (!running) {
            btnStop.classList.add("hidden");
            btnQuickStop.classList.add("hidden");
        }

        statusDot.className = `status-dot ${running ? 'running' : 'online'}`;
        statusText.textContent = running ? "Proses Pengisian Berjalan" : "Server Siap";

        if (runnerLiveDot) runnerLiveDot.classList.toggle("active", running);
        if (runnerStatusBullet) runnerStatusBullet.classList.toggle("running", running);
        if (consoleIndicator) consoleIndicator.className = `console-indicator ${running ? 'running' : 'idle'}`;
        runnerBadgeText.textContent = running ? "Sedang Mengirim Respon..." : "Siap Mengeksekusi";
    }

    function updateProgressUI(jobProgress) {
        if (!jobProgress) return;
        const comp = jobProgress.completed || 0;
        const total = jobProgress.total || 0;
        const succ = jobProgress.success || 0;
        const fail = jobProgress.failed || 0;
        const rem = Math.max(0, total - comp);

        metricCompleted.textContent = comp;
        metricTotal.textContent = total;
        metricSuccess.textContent = succ;
        metricFailed.textContent = fail;
        metricRemaining.textContent = rem;

        const pct = total > 0 ? Math.round((comp / total) * 100) : 0;
        progressBarFill.style.width = `${pct}%`;
        progressPercentText.textContent = `${pct}%`;

        if (jobProgress.waiting_text) {
            progressStatusDesc.textContent = `Sedang jeda antar respon: ${jobProgress.waiting_text}...`;
            if (consoleIndicator) consoleIndicator.className = "console-indicator paused";
            runnerBadgeText.textContent = `Menunggu Jeda (${jobProgress.waiting_text})`;
        } else {
            progressStatusDesc.textContent = isRunning ? `Sedang memproses ${comp} dari ${total} responden...` : `Selesai (${succ} sukses, ${fail} gagal).`;
            if (consoleIndicator && isRunning) consoleIndicator.className = "console-indicator running";
            if (isRunning) runnerBadgeText.textContent = "Sedang Mengirim Respon...";
        }
    }

    // --- Server-Sent Events (SSE) Stream ---
    function startSSEStream() {
        if (eventSource) eventSource.close();
        eventSource = new EventSource("/api/stream");

        eventSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.text === "[FINISHED]") {
                setExecutionRunning(false);
                eventSource.close();
                eventSource = null;
                fetchStatus();
                loadHistory();
                showToast("Seluruh antrean pengisian selesai!", "success");
                return;
            }

            appendTerminalLine(data.text, data.type, data.time);
            fetchStatus(); // Update progress metrics
        };

        eventSource.onerror = () => {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        };
    }

    function appendTerminalLine(text, type = "info", timestamp = null) {
        const timeStr = timestamp || getCurrentTime();
        const line = document.createElement("div");
        line.className = `terminal-line ${type}`;
        line.setAttribute("data-type", type);

        let tag = "[INFO]";
        if (type === "success") tag = "[SUKSES]";
        if (type === "warning") tag = "[WARN]";
        if (type === "danger") tag = "[ERROR]";
        if (type === "system") tag = "[SYSTEM]";

        line.innerHTML = `
            <span class="term-time">[${timeStr}]</span>
            <span class="term-tag">${tag}</span>
            <span class="term-text">${escapeHtml(text)}</span>
        `;

        terminalBody.appendChild(line);

        if (terminalLineCount) {
            const count = terminalBody.querySelectorAll(".terminal-line").length;
            terminalLineCount.textContent = `${count} baris`;
        }

        if (isAutoscroll) {
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }

        // Apply active filter
        if (activeTermFilter !== "all" && type !== activeTermFilter) {
            line.style.display = "none";
        }
    }

    function filterTerminalLogs() {
        document.querySelectorAll(".terminal-line").forEach(line => {
            const type = line.getAttribute("data-type");
            if (activeTermFilter === "all" || type === activeTermFilter) {
                line.style.display = "flex";
            } else {
                line.style.display = "none";
            }
        });
    }

    // --- Tab 4: History Management ---
    function loadHistory() {
        fetch("/api/history")
            .then(res => res.json())
            .then(data => {
                historyData = data.items || [];
                historyTotalCount.textContent = data.total || 0;
                tabHistoryBadge.textContent = data.total || 0;
                renderHistoryTable();
            })
            .catch(() => {
                historyTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Gagal memuat riwayat.</td></tr>`;
            });
    }

    function renderHistoryTable(searchQuery = "") {
        if (!historyData || historyData.length === 0) {
            historyTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-6 text-muted">
                        <i data-lucide="inbox" class="empty-icon-sm"></i>
                        <p>Belum ada riwayat pengisian.</p>
                    </td>
                </tr>
            `;
            renderIcons();
            return;
        }

        const filtered = historyData.filter(item => {
            if (!searchQuery) return true;
            return (
                item.nim.toLowerCase().includes(searchQuery) ||
                item.nama.toLowerCase().includes(searchQuery) ||
                item.prodi.toLowerCase().includes(searchQuery) ||
                item.dataset.toLowerCase().includes(searchQuery)
            );
        });

        if (filtered.length === 0) {
            historyTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Tidak ada data sesuai pencarian.</td></tr>`;
            return;
        }

        historyTableBody.innerHTML = filtered.map((item, idx) => {
            const hasAnswers = item.answers && item.answers.length > 0;
            const subTime = item.timestamp && item.timestamp !== "-" ? item.timestamp.split(" ")[1] || item.timestamp : "-";
            return `
                <tr>
                    <td class="font-mono text-muted">${idx + 1}</td>
                    <td class="font-mono font-semibold">${escapeHtml(item.nim)}</td>
                    <td class="font-medium">
                        <div style="font-weight:600; color:var(--fg);">${escapeHtml(item.nama)}</div>
                        <div class="text-subtle" style="font-size:11px;">${escapeHtml(item.jenis_kelamin || "-")}, ${escapeHtml(item.usia || "-")} th</div>
                    </td>
                    <td>
                        <div style="display:flex; flex-direction:column; gap:2px;">
                            <span style="font-weight:500;">${escapeHtml(item.prodi)}</span>
                            <span class="text-subtle" style="font-size:11px;">${escapeHtml(item.universitas || item.dataset)}</span>
                        </div>
                    </td>
                    <td><span class="badge badge-emerald" style="font-size:11px;">${escapeHtml(item.profile || "Puas Alami")}</span></td>
                    <td class="font-mono text-subtle" style="font-size:11.5px;">${escapeHtml(subTime)}</td>
                    <td>
                        ${hasAnswers ? `
                            <button type="button" class="btn btn-outline btn-xs btn-open-detail" data-idx="${idx}">
                                <i data-lucide="eye"></i> Detail
                            </button>
                        ` : `
                            <span class="text-muted" style="font-size:11px;">Tersimpan</span>
                        `}
                    </td>
                </tr>
            `;
        }).join("");

        // Attach detail button events
        document.querySelectorAll(".btn-open-detail").forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = parseInt(btn.getAttribute("data-idx"));
                showSubmissionDetail(filtered[idx]);
            });
        });

        renderIcons();
    }

    function showSubmissionDetail(item) {
        if (!item) return;
        currentDetailItem = item;
        modalDetailTitle.textContent = `Tanggapan: ${item.nama} (${item.nim})`;
        modalDetailSubtitle.textContent = `Disubmit: ${item.timestamp || '-'} • Profil: ${item.profile || 'Puas Alami'}`;

        let distBadges = "";
        if (item.scale_distribution && Object.keys(item.scale_distribution).length > 0) {
            distBadges = Object.entries(item.scale_distribution).map(([k, v]) => 
                `<span class="badge badge-emerald" style="margin-right:6px; margin-bottom:4px;">${escapeHtml(k)}: <strong>${v}x</strong></span>`
            ).join("");
        } else {
            distBadges = `<span class="text-muted" style="font-size:12px;">Tidak ada skala kuesioner khusus.</span>`;
        }

        const qaRows = (item.answers || []).map((ans, qIdx) => `
            <div class="qa-item">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <span class="qa-item-num">#${String(qIdx + 1).padStart(2, '0')}</span>
                </div>
                <div class="qa-item-question">${escapeHtml(ans.label)}</div>
                <div class="qa-item-answer">
                    ➔ ${escapeHtml(Array.isArray(ans.value) ? ans.value.join(", ") : ans.value)}
                </div>
            </div>
        `).join("");

        modalDetailBody.innerHTML = `
            <div class="modal-detail-grid">
                <div class="modal-detail-item">
                    <span class="modal-detail-label">Nama Lengkap</span>
                    <span class="modal-detail-val">${escapeHtml(item.nama)}</span>
                </div>
                <div class="modal-detail-item">
                    <span class="modal-detail-label">NIM / Angkatan</span>
                    <span class="modal-detail-val font-mono">${escapeHtml(item.nim)} (${escapeHtml(item.angkatan)})</span>
                </div>
                <div class="modal-detail-item">
                    <span class="modal-detail-label">Data Personal</span>
                    <span class="modal-detail-val">${escapeHtml(item.jenis_kelamin || "-")}, Usia ${escapeHtml(item.usia || "-")} th (Smt ${escapeHtml(item.semester || "-")})</span>
                </div>
                <div class="modal-detail-item">
                    <span class="modal-detail-label">Email Form</span>
                    <span class="modal-detail-val font-mono">${escapeHtml(item.email || "-")}</span>
                </div>
                <div class="modal-detail-item" style="grid-column: 1 / -1;">
                    <span class="modal-detail-label">Perguruan Tinggi & Prodi</span>
                    <span class="modal-detail-val">${escapeHtml(item.universitas || "-")} — ${escapeHtml(item.prodi || "-")}</span>
                </div>
            </div>

            <div class="mb-4">
                <div class="qa-section-title">
                    <span>Sebaran Pilihan Sikap / Skala</span>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    ${distBadges}
                </div>
            </div>

            <div>
                <div class="qa-section-title">
                    <span>Daftar Input & Jawaban Lengkap (${(item.answers || []).length} Butir)</span>
                </div>
                <div class="qa-list">
                    ${qaRows || '<div class="text-muted text-center py-4">Tidak ada data jawaban tersimpan.</div>'}
                </div>
            </div>
        `;

        modalDetail.classList.remove("hidden");
        renderIcons();
    }

    function confirmResetHistory() {
        btnConfirmReset.disabled = true;
        fetch("/api/reset-history", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                btnConfirmReset.disabled = false;
                modalConfirm.classList.add("hidden");
                if (data.success) {
                    showToast("Database riwayat pengisian berhasil direset!", "success");
                    loadHistory();
                    fetchStatus();
                } else {
                    showToast(data.message || "Gagal mereset riwayat.", "error");
                }
            })
            .catch(() => {
                btnConfirmReset.disabled = false;
                modalConfirm.classList.add("hidden");
                showToast("Terjadi kesalahan saat mereset riwayat.", "error");
            });
    }

    function exportHistoryCSV() {
        if (!historyData || historyData.length === 0) {
            showToast("Tidak ada riwayat untuk diekspor.", "info");
            return;
        }

        let csv = "NIM,Nama,Angkatan,Program Studi,Dataset\n";
        historyData.forEach(item => {
            csv += `"${item.nim}","${item.nama}","${item.angkatan}","${item.prodi}","${item.dataset}"\n`;
        });

        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `riwayat_kuesioner_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
        showToast("File CSV riwayat berhasil diunduh.", "success");
    }

    // --- Helpers ---
    function getCurrentTime() {
        const now = new Date();
        return now.toTimeString().split(" ")[0];
    }

    function escapeHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
