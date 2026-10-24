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

    // Tab 1: Form Inspector & Saved Forms Toolbar
    const savedFormsSelect = document.getElementById("saved-forms-select");
    const savedFormsChips = document.getElementById("saved-forms-chips");
    const savedFormsCount = document.getElementById("saved-forms-count");
    const btnSaveCurrentForm = document.getElementById("btn-save-current-form");
    const btnDeleteSavedForm = document.getElementById("btn-delete-saved-form");
    const btnCopyFormUrl = document.getElementById("btn-copy-form-url");
    const formAutosaveBadge = document.getElementById("form-autosave-badge");
    let savedFormsList = [];
    let currentSavedFormUrl = "";
    let autoSaveRulesTimer = null;

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
    const btnCopyLatestChat = document.getElementById("btn-copy-latest-chat");
    const btnToggleAutoscroll = document.getElementById("btn-toggle-autoscroll");
    const termTabs = document.querySelectorAll(".term-tab");

    // Tab 4: History & Analytics
    const historyTableBody = document.getElementById("history-table-body");
    const historySearchInput = document.getElementById("history-search-input");
    const historyTotalCount = document.getElementById("history-total-count");
    const btnRefreshHistory = document.getElementById("btn-refresh-history");
    const btnExportHistory = document.getElementById("btn-export-history");
    const btnExportChat = document.getElementById("btn-export-chat");
    const btnResetHistory = document.getElementById("btn-reset-history");
    const historyFilterStatus = document.getElementById("history-filter-status");

    // Tab 4: KPI Summary Elements
    const kpiTotalSubs = document.getElementById("kpi-total-subs");
    const kpiFormName = document.getElementById("kpi-form-name");
    const kpiFormStatus = document.getElementById("kpi-form-status");
    const kpiSegmentation = document.getElementById("kpi-segmentation");
    const kpiSegmentSub = document.getElementById("kpi-segment-sub");
    const kpiAvgSus = document.getElementById("kpi-avg-sus");
    const kpiAvgGrade = document.getElementById("kpi-avg-grade");

    // Modal & Toast
    const modalConfirm = document.getElementById("modal-confirm");
    const btnConfirmClose = document.getElementById("btn-confirm-close");
    const btnConfirmCancel = document.getElementById("btn-confirm-cancel");
    const btnConfirmReset = document.getElementById("btn-confirm-reset");
    const modalDetail = document.getElementById("modal-detail");
    const modalDetailTitle = document.getElementById("modal-detail-title");
    const modalDetailSubtitle = document.getElementById("modal-detail-subtitle");
    const modalDetailBody = document.getElementById("modal-detail-body");
    const btnCloseDetail = document.getElementById("btn-close-detail");
    const btnCopyAnswers = document.getElementById("btn-copy-answers");
    const btnCopyChatFormat = document.getElementById("btn-copy-chat-format");
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
        // Saved Forms Toolbar Listeners
        if (savedFormsSelect) {
            savedFormsSelect.addEventListener("change", (e) => {
                const val = e.target.value;
                if (val) {
                    selectSavedForm(val);
                }
            });
        }

        if (btnSaveCurrentForm) {
            btnSaveCurrentForm.addEventListener("click", () => {
                const url = formUrlInput.value.trim();
                if (!url) {
                    showToast("Masukkan URL Google Form terlebih dahulu.", "error");
                    return;
                }
                btnSaveCurrentForm.disabled = true;
                btnSaveCurrentForm.innerHTML = `<i data-lucide="loader-2" class="spin"></i> Menyimpan...`;
                renderIcons();

                fetch("/api/forms/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        url: url,
                        title: metaFormTitle.textContent && metaFormTitle.textContent !== "-" ? metaFormTitle.textContent : "Formulir Kuesioner Google",
                        structure: {
                            form_title: metaFormTitle.textContent,
                            form_description: metaFormDesc.textContent,
                            questions: formQuestions,
                            num_pages: parseInt(metaFormPages.textContent) || 1,
                            has_email_page: metaFormEmail.textContent === "Wajib Diisi"
                        },
                        question_rules: questionRules
                    })
                })
                .then(res => res.json())
                .then(data => {
                    btnSaveCurrentForm.disabled = false;
                    btnSaveCurrentForm.innerHTML = `<i data-lucide="save"></i> Simpan Preset`;
                    renderIcons();
                    if (data.success) {
                        savedFormsList = data.forms || [];
                        currentSavedFormUrl = url;
                        localStorage.setItem("last_form_url", url);
                        renderSavedFormsUI(url);
                        showToast("✓ Formulir dan seluruh konfigurasi aturan berhasil disimpan sebagai preset!", "success");
                    } else {
                        showToast(data.message || "Gagal menyimpan formulir.", "error");
                    }
                })
                .catch(() => {
                    btnSaveCurrentForm.disabled = false;
                    btnSaveCurrentForm.innerHTML = `<i data-lucide="save"></i> Simpan Preset`;
                    renderIcons();
                    showToast("Terjadi kesalahan jaringan saat menyimpan formulir.", "error");
                });
            });
        }

        if (btnDeleteSavedForm) {
            btnDeleteSavedForm.addEventListener("click", () => {
                const url = formUrlInput.value.trim();
                if (!url) return;
                const formObj = savedFormsList.find(f => f.url === url || f.original_url === url);
                const formTitle = formObj ? formObj.title : "formulir ini";
                if (!confirm(`Hapus "${formTitle}" dari riwayat formulir tersimpan?`)) return;

                fetch("/api/forms/delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: url })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        savedFormsList = data.forms || [];
                        showToast("✓ Formulir berhasil dihapus dari riwayat.", "info");
                        if (savedFormsList.length > 0) {
                            selectSavedForm(savedFormsList[0].url);
                        } else {
                            renderSavedFormsUI("");
                        }
                    }
                })
                .catch(() => showToast("Gagal menghapus formulir.", "error"));
            });
        }

        if (btnCopyFormUrl) {
            btnCopyFormUrl.addEventListener("click", () => {
                const url = formUrlInput.value.trim();
                if (!url) {
                    showToast("Belum ada URL formulir yang diinput.", "warning");
                    return;
                }
                navigator.clipboard.writeText(url).then(() => {
                    showToast("✓ URL formulir berhasil disalin ke clipboard!", "success");
                });
            });
        }

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

        // Quick Preset Template Buttons
        document.querySelectorAll(".btn-preset").forEach(btn => {
            btn.addEventListener("click", () => {
                const preset = btn.getAttribute("data-preset");
                applyPreset(preset);
            });
        });

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

        if (btnCopyLatestChat) {
            btnCopyLatestChat.addEventListener("click", () => {
                fetch("/api/history")
                    .then(res => res.json())
                    .then(data => {
                        const items = data.items || [];
                        const latest = items.find(i => i.answers && i.answers.length > 0);
                        if (!latest) {
                            showToast("Belum ada data responden kuesioner yang berhasil disubmit.", "warning");
                            return;
                        }
                        const chatText = formatSubmissionForChat(latest);
                        navigator.clipboard.writeText(chatText).then(() => {
                            showToast(`✓ Format chat untuk ${latest.nama} (${latest.nim}) disalin! Siap dikirim ke WA/Telegram.`, "success");
                        });
                    })
                    .catch(() => showToast("Gagal mengambil data responden terbaru.", "error"));
            });
        }

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
        if (btnExportChat) {
            btnExportChat.addEventListener("click", exportHistoryChat);
        }
        btnResetHistory.addEventListener("click", () => modalConfirm.classList.remove("hidden"));
        btnConfirmCancel.addEventListener("click", () => modalConfirm.classList.add("hidden"));
        if (btnConfirmClose) {
            btnConfirmClose.addEventListener("click", () => modalConfirm.classList.add("hidden"));
        }
        if (modalConfirm) {
            modalConfirm.addEventListener("click", (e) => {
                if (e.target === modalConfirm) modalConfirm.classList.add("hidden");
            });
        }
        btnConfirmReset.addEventListener("click", confirmResetHistory);

        // Global Escape key listener to close modals
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                if (modalConfirm && !modalConfirm.classList.contains("hidden")) {
                    modalConfirm.classList.add("hidden");
                }
                if (modalDetail && !modalDetail.classList.contains("hidden")) {
                    modalDetail.classList.add("hidden");
                }
            }
        });

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
        if (btnCopyChatFormat) {
            btnCopyChatFormat.addEventListener("click", () => {
                if (!currentDetailItem) return;
                const chatText = formatSubmissionForChat(currentDetailItem);
                navigator.clipboard.writeText(chatText).then(() => {
                    showToast(`✓ Format chat untuk ${currentDetailItem.nama} berhasil disalin! Siap dipaste ke WA/Telegram.`, "success");
                });
            });
        }

        historySearchInput.addEventListener("input", (e) => {
            renderHistoryTable(e.target.value.toLowerCase());
        });

        if (historyFilterStatus) {
            historyFilterStatus.addEventListener("change", () => {
                renderHistoryTable(historySearchInput.value.toLowerCase());
            });
        }
    }

    // --- API Interactions ---
    function fetchStatus(isInitial = false) {
        fetch("/api/status")
            .then(res => res.json())
            .then(data => {
                if (data.saved_forms) {
                    savedFormsList = data.saved_forms;
                }

                if (isInitial) {
                    // Prioritas: 1) local storage user, 2) last active form dari server, 3) default config
                    const savedLocalUrl = localStorage.getItem("last_form_url");
                    const targetUrl = savedLocalUrl || data.default_url;
                    
                    if (targetUrl) {
                        formUrlInput.value = targetUrl;
                        currentSavedFormUrl = targetUrl;
                    }
                    if (data.default_target) targetInput.value = data.default_target;
                    if (data.default_delay_min !== undefined) delayMinInput.value = data.default_delay_min;
                    if (data.default_delay_max !== undefined) delayMaxInput.value = data.default_delay_max;

                    // Muat daftar riwayat formulir di UI
                    loadSavedForms(targetUrl);

                    // Periksa apakah form sudah memiliki cache struktur di savedFormsList agar instan tanpa loading
                    const cachedForm = (savedFormsList || []).find(f => f.url === targetUrl || f.original_url === targetUrl);
                    if (cachedForm && cachedForm.questions && cachedForm.questions.length > 0) {
                        selectSavedForm(targetUrl, true);
                    } else if (targetUrl) {
                        fetchFormStructure(targetUrl);
                    }
                } else {
                    renderSavedFormsUI(currentSavedFormUrl);
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

    function loadSavedForms(preferredUrl = null) {
        fetch("/api/forms/history")
            .then(res => res.json())
            .then(data => {
                if (!data.success) return;
                savedFormsList = data.forms || [];
                const activeUrl = preferredUrl || currentSavedFormUrl || data.last_active_url || (savedFormsList[0] ? savedFormsList[0].url : "");
                currentSavedFormUrl = activeUrl;
                renderSavedFormsUI(activeUrl);
            })
            .catch(err => console.error("Gagal memuat riwayat formulir:", err));
    }

    function renderSavedFormsUI(activeUrl = "") {
        if (savedFormsCount) {
            savedFormsCount.textContent = `${savedFormsList.length} tersimpan`;
        }

        // Render Select Dropdown
        if (savedFormsSelect) {
            savedFormsSelect.innerHTML = `<option value="">-- ⚡ Pilih dari Riwayat Formulir (${savedFormsList.length} tersimpan) --</option>`;
            savedFormsList.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f.url;
                const isSelected = activeUrl && (f.url === activeUrl || f.original_url === activeUrl);
                if (isSelected) opt.selected = true;
                const qCount = f.questions_count || (f.questions ? f.questions.length : 0);
                opt.textContent = `${f.title || "Formulir"} (${qCount} Soal) • [${f.last_used || "Tersimpan"}]`;
                savedFormsSelect.appendChild(opt);
            });
        }

        // Render Quick Chips (Top 4 most recent)
        if (savedFormsChips) {
            savedFormsChips.innerHTML = "";
            const topForms = savedFormsList.slice(0, 4);
            topForms.forEach(f => {
                const chip = document.createElement("button");
                chip.type = "button";
                const isSelected = activeUrl && (f.url === activeUrl || f.original_url === activeUrl);
                chip.className = `saved-form-chip ${isSelected ? "active" : ""}`;
                const qCount = f.questions_count || (f.questions ? f.questions.length : 0);
                chip.innerHTML = `<i data-lucide="bookmark"></i> <span>${f.title || "Formulir"}</span> <span class="badge badge-zinc" style="padding:1px 5px; font-size:10px;">${qCount} soal</span>`;
                chip.title = `${f.title}\nURL: ${f.url}\nTerakhir digunakan: ${f.last_used || "-"}`;
                chip.addEventListener("click", () => {
                    selectSavedForm(f.url);
                });
                savedFormsChips.appendChild(chip);
            });
            renderIcons();
        }

        // Toggle Delete Button
        if (btnDeleteSavedForm) {
            const isSaved = savedFormsList.some(f => f.url === activeUrl || f.original_url === activeUrl);
            btnDeleteSavedForm.classList.toggle("hidden", !isSaved);
        }
    }

    function selectSavedForm(url, skipServerNotify = false) {
        if (!url) return;
        const formObj = savedFormsList.find(f => f.url === url || f.original_url === url);
        if (!formObj) return;

        currentSavedFormUrl = formObj.url;
        formUrlInput.value = formObj.url;
        localStorage.setItem("last_form_url", formObj.url);

        if (!skipServerNotify) {
            fetch("/api/forms/set-active", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: formObj.url })
            }).catch(() => {});
        }

        // Jika formulir memiliki struktur dan aturan tersimpan, muat instan tanpa tunggu request network!
        if (formObj.questions && formObj.questions.length > 0) {
            formQuestions = formObj.questions;
            questionRules = formObj.question_rules ? { ...formObj.question_rules } : {};
            tabQuestionsBadge.textContent = formQuestions.length;
            tabQuestionsBadge.classList.remove("hidden");

            metaFormTitle.textContent = formObj.title || "Formulir Google";
            metaFormPages.textContent = `${formObj.num_pages || 1} Halaman`;
            metaFormCount.textContent = `${formQuestions.length} Pertanyaan`;
            metaFormEmail.textContent = formObj.has_email_page ? "Wajib Diisi" : "Tidak";
            metaFormDesc.textContent = formObj.description || "Formulir tidak memiliki deskripsi tambahan.";
            formMetaCard.classList.remove("hidden");

            renderQuestionsList();
            renderSavedFormsUI(formObj.url);
            showToast(`✓ Formulir "${formObj.title}" dan ${formQuestions.length} pertanyaan berhasil dimuat dari riwayat!`, "success");
        } else {
            // Ambil struktur baru
            fetchFormStructure(formObj.url);
        }
    }

    function triggerAutoSaveRules() {
        if (autoSaveRulesTimer) clearTimeout(autoSaveRulesTimer);
        autoSaveRulesTimer = setTimeout(() => {
            const currentUrl = formUrlInput.value.trim();
            if (!currentUrl || formQuestions.length === 0) return;

            fetch("/api/forms/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: currentUrl,
                    title: metaFormTitle.textContent && metaFormTitle.textContent !== "-" ? metaFormTitle.textContent : "Formulir Google",
                    structure: {
                        form_title: metaFormTitle.textContent,
                        form_description: metaFormDesc.textContent,
                        questions: formQuestions,
                        num_pages: parseInt(metaFormPages.textContent) || 1,
                        has_email_page: metaFormEmail.textContent === "Wajib Diisi"
                    },
                    question_rules: questionRules
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.forms) {
                    savedFormsList = data.forms;
                    renderSavedFormsUI(currentUrl);
                }
            })
            .catch(() => {});
        }, 800);
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
                const activeUrl = data.canonical_url || url;
                formUrlInput.value = activeUrl;
                currentSavedFormUrl = activeUrl;
                localStorage.setItem("last_form_url", activeUrl);

                if (data.saved_forms) {
                    savedFormsList = data.saved_forms;
                }
                loadSavedForms(activeUrl);

                // Cek apakah form ini sudah punya konfigurasi aturan tersimpan sebelumnya
                const existingForm = (savedFormsList || []).find(f => f.url === activeUrl || f.original_url === activeUrl);
                if (existingForm && existingForm.question_rules && Object.keys(existingForm.question_rules).length > 0) {
                    questionRules = { ...existingForm.question_rules };
                } else {
                    questionRules = {};
                }

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
                showToast(`Form berhasil dianalisis: ${formQuestions.length} pertanyaan terdeteksi & tersimpan otomatis.`, "success");
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
                                <option value="filter_options" ${currentRule.mode === 'filter_options' ? 'selected' : ''}>✅ Filter Opsi Terpilih (Whitelist)</option>
                                <option value="weighted_options" ${currentRule.mode === 'weighted_options' ? 'selected' : ''}>⚖️ Atur Rasio / Bobot Opsi (%)</option>
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
        } else if (mode === "filter_options") {
            if (options.length > 0) {
                const allowed = Array.isArray(rule.allowed_options) ? rule.allowed_options : [...options];
                rule.allowed_options = allowed;
                const checkHtml = options.map((opt) => {
                    const isChecked = allowed.includes(opt);
                    return `
                        <label class="checkbox-option-item">
                            <input type="checkbox" class="sub-checkbox" data-entry="${entryId}" value="${escapeHtml(opt)}" ${isChecked ? 'checked' : ''}>
                            <span>${escapeHtml(opt)}</span>
                        </label>
                    `;
                }).join('');
                container.innerHTML = `
                    <label class="form-label"><i data-lucide="check-square"></i> Pilih Opsi yang Diperbolehkan:</label>
                    <div class="checkbox-options-list">
                        ${checkHtml}
                    </div>
                    <span class="field-hint">Sistem HANYA akan memilih di antara opsi yang dicentang di atas.</span>
                `;
            } else {
                container.innerHTML = `<span class="field-hint text-amber">Tidak ada pilihan opsi tersedia pada pertanyaan ini.</span>`;
            }
        } else if (mode === "weighted_options") {
            if (options.length > 0) {
                const weights = rule.weights || {};
                rule.weights = weights;
                const rowsHtml = options.map(opt => {
                    const curW = weights[opt] !== undefined ? weights[opt] : Math.round(100 / options.length);
                    weights[opt] = curW;
                    return `
                        <div class="weighted-option-row">
                            <span class="weighted-opt-name" title="${escapeHtml(opt)}">${escapeHtml(opt)}</span>
                            <div class="weighted-opt-input-wrap">
                                <input type="number" min="0" max="100" class="sub-weight-input form-control" data-entry="${entryId}" data-opt="${escapeHtml(opt)}" value="${curW}">
                                <span class="pct-sign">%</span>
                            </div>
                        </div>
                    `;
                }).join('');
                container.innerHTML = `
                    <label class="form-label"><i data-lucide="percent"></i> Atur Rasio / Bobot Pilihan:</label>
                    <div class="weighted-options-container">
                        ${rowsHtml}
                    </div>
                    <span class="field-hint">Ketik 0% jika opsi tidak ingin dipilih sama sekali (misal Pegawai: 0%, Mahasiswa: 80%, UMKM: 20%).</span>
                `;
            } else {
                container.innerHTML = `<span class="field-hint text-amber">Tidak ada pilihan opsi tersedia pada pertanyaan ini.</span>`;
            }
        } else if (mode === "scale") {
            const currentProf = rule.profile || "auto";
            container.innerHTML = `
                <label class="form-label"><i data-lucide="bar-chart-2"></i> Bobot Skala:</label>
                <select class="form-control sub-input" data-entry="${entryId}" data-key="profile">
                    <option value="auto" ${currentProf === 'auto' ? 'selected' : ''}>Ikuti Sentimen Global (Auto SUS)</option>
                    <option value="sus_positive" ${currentProf === 'sus_positive' ? 'selected' : ''}>SUS Positif (4 atau 5)</option>
                    <option value="sus_negative" ${currentProf === 'sus_negative' ? 'selected' : ''}>SUS Negatif (1 atau 2)</option>
                    <option value="random_4_5" ${currentProf === 'random_4_5' ? 'selected' : ''}>Variasi Tinggi (4 atau 5)</option>
                    <option value="random_1_2" ${currentProf === 'random_1_2' ? 'selected' : ''}>Variasi Rendah (1 atau 2)</option>
                    <option value="fixed_5" ${currentProf === 'fixed_5' ? 'selected' : ''}>Nilai Tertinggi (5)</option>
                    <option value="fixed_4" ${currentProf === 'fixed_4' ? 'selected' : ''}>Nilai 4 / Sesuai</option>
                    <option value="fixed_3" ${currentProf === 'fixed_3' ? 'selected' : ''}>Nilai Netral (3)</option>
                    <option value="fixed_2" ${currentProf === 'fixed_2' ? 'selected' : ''}>Nilai 2 / Kurang</option>
                    <option value="fixed_1" ${currentProf === 'fixed_1' ? 'selected' : ''}>Nilai Terendah (1)</option>
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
                triggerAutoSaveRules();
            });
        });

        document.querySelectorAll(".sub-input").forEach(inp => {
            inp.addEventListener("change", (e) => {
                const entryId = e.target.getAttribute("data-entry");
                const key = e.target.getAttribute("data-key");
                if (questionRules[entryId]) {
                    questionRules[entryId][key] = e.target.value;
                    triggerAutoSaveRules();
                }
            });
        });

        document.querySelectorAll(".sub-checkbox").forEach(cb => {
            cb.addEventListener("change", (e) => {
                const entryId = e.target.getAttribute("data-entry");
                const container = document.getElementById(`sub-ctrl-${entryId}`);
                if (container && questionRules[entryId]) {
                    const checkedValues = Array.from(container.querySelectorAll(".sub-checkbox:checked")).map(c => c.value);
                    questionRules[entryId].allowed_options = checkedValues;
                    triggerAutoSaveRules();
                }
            });
        });

        document.querySelectorAll(".sub-weight-input").forEach(inp => {
            inp.addEventListener("input", (e) => {
                const entryId = e.target.getAttribute("data-entry");
                const opt = e.target.getAttribute("data-opt");
                const val = parseFloat(e.target.value) || 0;
                if (questionRules[entryId]) {
                    if (!questionRules[entryId].weights) questionRules[entryId].weights = {};
                    questionRules[entryId].weights[opt] = val;
                    triggerAutoSaveRules();
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
        triggerAutoSaveRules();
        showToast("Seluruh aturan pertanyaan dikembalikan ke rekomendasi cerdas.", "info");
    }

    function applyPreset(presetType) {
        if (!formQuestions || formQuestions.length === 0) {
            showToast("Buka form terlebih dahulu sebelum menerapkan preset.", "warning");
            return;
        }

        const susNegKeywords = ["rumit", "bantuan orang lain", "teknisi", "ketidaksesuaian", "membingungkan", "banyak hal sebelum"];
        const susPosKeywords = ["sering menggunakan", "mudah digunakan", "terintegrasi", "terintegerasi", "dengan cepat", "percaya diri"];

        let countModified = 0;
        formQuestions.forEach(q => {
            const entryId = String(q.entry_id);
            const isScale = (q.type === 5) || (q.type in [2, 3] && q.options && q.options.every(o => /^\d+$/.test(o)));
            const lblLower = (q.label || '').toLowerCase();

            if (presetType === "sus" && isScale) {
                if (susNegKeywords.some(k => lblLower.includes(k))) {
                    questionRules[entryId] = { mode: "scale", profile: "sus_negative" };
                    countModified++;
                } else {
                    questionRules[entryId] = { mode: "scale", profile: "sus_positive" };
                    countModified++;
                }
            } else if (presetType === "csat" && isScale) {
                questionRules[entryId] = { mode: "scale", profile: "random_4_5" };
                countModified++;
            } else if (presetType === "realistic" && isScale) {
                questionRules[entryId] = { mode: "scale", profile: "auto" };
                countModified++;
            } else if (presetType === "kritis" && isScale) {
                questionRules[entryId] = { mode: "scale", profile: "kritis" };
                countModified++;
            }
        });

        renderQuestionsList();
        triggerAutoSaveRules();

        const presetNames = {
            "sus": "SUS (System Usability Scale)",
            "csat": "Sangat Puas (CSAT 4-5)",
            "realistic": "Puas Alami / Realistis",
            "kritis": "Kritis & Berimbang (1-5)"
        };
        showToast(`Preset ${presetNames[presetType] || presetType} diterapkan pada ${countModified} pertanyaan!`, "success");
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

    // --- Tab 4: History Management (Enterprise Audit & Analytics Standard) ---
    function loadHistory() {
        fetch("/api/history")
            .then(res => res.json())
            .then(data => {
                historyData = data.items || [];
                historyTotalCount.textContent = data.total || 0;
                tabHistoryBadge.textContent = data.total || 0;

                // Update KPI Summary Metrics (Standar Industri)
                if (kpiTotalSubs) kpiTotalSubs.textContent = historyData.length;
                
                let mhsCount = 0;
                let umkmCount = 0;
                let susScores = [];
                let detectedFormTitle = "KUESIONER PENGUJIAN SYSTEM USABILITY SCALE (SUS) APLIKASI AUGMENTED REALITY";

                historyData.forEach(i => {
                    if (i.form_title && i.form_title !== "Formulir Kuesioner Google") {
                        detectedFormTitle = i.form_title;
                    }
                    const statusStr = (i.status_responden || "").toLowerCase();
                    if (statusStr.includes("umkm") || statusStr.includes("wiraswasta")) {
                        umkmCount++;
                    } else {
                        mhsCount++;
                    }
                    if (i.sus_score !== undefined && i.sus_score !== null && !isNaN(parseFloat(i.sus_score))) {
                        susScores.push(parseFloat(i.sus_score));
                    }
                });

                if (kpiFormName) {
                    kpiFormName.textContent = detectedFormTitle;
                    kpiFormName.title = detectedFormTitle;
                }
                if (kpiFormStatus) {
                    kpiFormStatus.textContent = "Protokol: HTTP 200 OK (Google Form)";
                }
                if (kpiSegmentation) {
                    kpiSegmentation.textContent = `${mhsCount} Mhs • ${umkmCount} UMKM`;
                }
                if (kpiSegmentSub) {
                    kpiSegmentSub.textContent = `Pegawai / Karyawan: 0 (0%)`;
                }
                if (kpiAvgSus) {
                    if (susScores.length > 0) {
                        const avg = susScores.reduce((a, b) => a + b, 0) / susScores.length;
                        kpiAvgSus.textContent = `${avg.toFixed(1)} / 100`;
                        if (kpiAvgGrade) {
                            kpiAvgGrade.textContent = avg >= 85 ? "Grade A (Sangat Memuaskan)" : avg >= 70 ? "Grade B (Sangat Baik)" : "Grade C (Cukup)";
                        }
                    } else {
                        kpiAvgSus.textContent = "100% Valid";
                        if (kpiAvgGrade) kpiAvgGrade.textContent = "Data Lengkap";
                    }
                }

                renderHistoryTable();
            })
            .catch(() => {
                historyTableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">Gagal memuat riwayat.</td></tr>`;
            });
    }

    function renderHistoryTable(searchQuery = "") {
        if (!historyData || historyData.length === 0) {
            historyTableBody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-6 text-muted">
                        <i data-lucide="inbox" class="empty-icon-sm"></i>
                        <p>Belum ada riwayat pengisian.</p>
                    </td>
                </tr>
            `;
            renderIcons();
            return;
        }

        const statusFilter = historyFilterStatus ? historyFilterStatus.value : "all";

        const filtered = historyData.filter(item => {
            const matchesSearch = !searchQuery || (
                (item.nim && item.nim.toLowerCase().includes(searchQuery)) ||
                (item.nama && item.nama.toLowerCase().includes(searchQuery)) ||
                (item.prodi && item.prodi.toLowerCase().includes(searchQuery)) ||
                (item.universitas && item.universitas.toLowerCase().includes(searchQuery)) ||
                (item.form_title && item.form_title.toLowerCase().includes(searchQuery)) ||
                (item.submission_id && item.submission_id.toLowerCase().includes(searchQuery)) ||
                (item.status_responden && item.status_responden.toLowerCase().includes(searchQuery)) ||
                (item.dataset && item.dataset.toLowerCase().includes(searchQuery))
            );

            const itemStatus = (item.status_responden || "").toLowerCase();
            const matchesStatus = (statusFilter === "all") || (
                statusFilter === "UMKM" ? (itemStatus.includes("umkm") || itemStatus.includes("wiraswasta")) :
                statusFilter === "Mahasiswa" ? (!itemStatus || itemStatus.includes("mahasiswa")) :
                true
            );

            return matchesSearch && matchesStatus;
        });

        if (filtered.length === 0) {
            historyTableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">Tidak ada data responden yang sesuai pencarian atau filter.</td></tr>`;
            return;
        }

        historyTableBody.innerHTML = filtered.map((item, idx) => {
            const hasAnswers = item.answers && item.answers.length > 0;
            const subTime = item.timestamp && item.timestamp !== "-" ? item.timestamp.split(" ")[1] || item.timestamp : "-";
            const auditId = item.submission_id || `SUB-${item.nim.slice(-4)}`;
            const isUmkm = (item.status_responden || "").toLowerCase().includes("umkm") || (item.status_responden || "").toLowerCase().includes("wiraswasta");
            
            return `
                <tr>
                    <td class="font-mono text-muted">${idx + 1}</td>
                    <td>
                        <span class="badge badge-outline font-mono" style="font-size:11px; letter-spacing:0.02em;">#${escapeHtml(auditId)}</span>
                    </td>
                    <td class="font-medium">
                        <div style="font-weight:600; color:var(--fg);">${escapeHtml(item.nama)}</div>
                        <div class="font-mono text-subtle" style="font-size:11px;">NIM: ${escapeHtml(item.nim)} • ${escapeHtml(item.jenis_kelamin || "-")}, ${escapeHtml(item.usia || "-")} th</div>
                        <div class="text-subtle" style="font-size:11px;">${escapeHtml(item.prodi || "-")} (${escapeHtml(item.universitas || item.dataset)})</div>
                    </td>
                    <td>
                        <div style="max-width:210px;">
                            <div style="font-weight:600; font-size:12px; line-height:1.35; color:var(--fg); overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;" title="${escapeHtml(item.form_title || 'Google Form')}">
                                ${escapeHtml(item.form_title || "Google Form")}
                            </div>
                            ${item.form_url && item.form_url !== "-" ? `
                                <a href="${escapeHtml(item.form_url)}" target="_blank" rel="noopener noreferrer" style="font-size:11px; color:var(--primary); display:inline-flex; align-items:center; gap:2px; margin-top:2px; text-decoration:underline;">
                                    <i data-lucide="external-link" style="width:11px; height:11px;"></i> Form Asli
                                </a>
                            ` : ''}
                        </div>
                    </td>
                    <td>
                        ${isUmkm ? `
                            <span class="badge badge-amber font-semibold" style="font-size:11px;">
                                <i data-lucide="store" style="width:12px; height:12px; margin-right:3px;"></i> UMKM
                            </span>
                        ` : `
                            <span class="badge badge-primary font-semibold" style="font-size:11px;">
                                <i data-lucide="graduation-cap" style="width:12px; height:12px; margin-right:3px;"></i> Mahasiswa
                            </span>
                        `}
                    </td>
                    <td>
                        ${item.sus_score ? `
                            <div>
                                <span style="font-weight:700; font-size:13px; color:var(--primary);">${item.sus_score}</span>
                                <span class="text-subtle" style="font-size:11px;">/100</span>
                            </div>
                            <span class="badge badge-emerald" style="font-size:10px; margin-top:2px;">${escapeHtml(item.sus_grade || "Grade B")}</span>
                        ` : `
                            <span class="badge badge-secondary" style="font-size:11px;">${escapeHtml(item.profile || "Normal")}</span>
                        `}
                    </td>
                    <td>
                        <div class="font-mono text-subtle" style="font-size:11.5px;">${escapeHtml(subTime)}</div>
                        <span class="badge badge-emerald" style="font-size:10px; margin-top:2px;">
                            <i data-lucide="check" style="width:10px; height:10px; margin-right:2px;"></i> ${escapeHtml(item.http_status || "200 OK")}
                        </span>
                    </td>
                    <td>
                        ${hasAnswers ? `
                            <div style="display:flex; flex-direction:column; gap:4px;">
                                <button type="button" class="btn btn-outline btn-xs btn-open-detail" data-idx="${idx}">
                                    <i data-lucide="eye"></i> Detail Audit
                                </button>
                                <button type="button" class="btn btn-secondary btn-xs btn-copy-row-chat" data-idx="${idx}" title="Salin Format Chat (WA/Telegram)">
                                    <i data-lucide="message-square"></i> Salin Chat
                                </button>
                            </div>
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

        // Attach row quick-copy chat events
        document.querySelectorAll(".btn-copy-row-chat").forEach(btn => {
            btn.addEventListener("click", () => {
                const idx = parseInt(btn.getAttribute("data-idx"));
                const item = filtered[idx];
                const chatText = formatSubmissionForChat(item);
                navigator.clipboard.writeText(chatText).then(() => {
                    showToast(`✓ Format chat untuk ${item.nama} berhasil disalin! Siap dipaste ke WA/Telegram.`, "success");
                });
            });
        });

        renderIcons();
    }

    function formatSubmissionForChat(item) {
        if (!item) return "";
        const lines = [];
        lines.push("📋 *BUKTI PENGISIAN KUESIONER*");
        if (item.form_title) {
            lines.push(`📌 *Formulir:* ${item.form_title}`);
        }
        const auditId = item.submission_id || `SUB-${item.nim}`;
        lines.push(`🔗 *ID Audit:* ${auditId} | *Status:* HTTP 200 OK (Terverifikasi)`);
        lines.push("━━━━━━━━━━━━━━━━━━━━━━━");

        // Identitas & Demografi
        lines.push("👤 *DATA RESPONDEN*");
        lines.push(`• *Nama Lengkap:* ${item.nama || "-"}`);
        lines.push(`• *NIM:* ${item.nim || "-"}`);
        if (item.status_responden && item.status_responden !== "-") {
            lines.push(`• *Peran / Status:* ${item.status_responden}`);
        }

        const personal = [];
        if (item.jenis_kelamin && item.jenis_kelamin !== "-") personal.push(item.jenis_kelamin);
        if (item.usia && item.usia !== "-") personal.push(`Usia ${item.usia} th`);
        if (item.semester && item.semester !== "-") {
            const smt = String(item.semester).trim();
            personal.push(smt.toLowerCase().includes("semester") ? smt : `Semester ${smt}`);
        }
        if (personal.length > 0) {
            lines.push(`• *Data Diri:* ${personal.join(" | ")}`);
        }

        if (item.universitas && item.universitas !== "-") {
            lines.push(`• *Kampus:* ${item.universitas}`);
        }
        if (item.prodi && item.prodi !== "-") {
            const cohortStr = (item.angkatan && item.angkatan !== "-") ? ` (Angkatan ${item.angkatan})` : "";
            lines.push(`• *Jurusan / Prodi:* ${item.prodi}${cohortStr}`);
        }
        if (item.email && item.email !== "-") {
            lines.push(`• *Email Form:* ${item.email}`);
        }
        if (item.timestamp && item.timestamp !== "-") {
            lines.push(`• *Waktu Submit:* ${item.timestamp} WIB`);
        }

        // Pola Sikap & Metrik Riset
        lines.push("");
        lines.push("📊 *POLA JAWABAN & METRIK*");
        lines.push(`• *Profil Sikap:* ${item.profile_display || item.profile || "Normal"}`);
        if (item.sus_score) {
            lines.push(`• *Skor SUS:* ${item.sus_score} / 100 (${item.sus_grade || "Grade B"})`);
        }
        if (item.scale_distribution && Object.keys(item.scale_distribution).length > 0) {
            const distStr = Object.entries(item.scale_distribution)
                .map(([k, v]) => `${k}: ${v}x`)
                .join(" | ");
            lines.push(`• *Sebaran Pilihan:* ${distStr}`);
        }

        // Rincian Pertanyaan & Jawaban
        const answers = item.answers || [];
        lines.push("");
        lines.push(`📝 *RINCIAN JAWABAN (${answers.length} Butir Pertanyaan)*`);
        answers.forEach((ans, idx) => {
            const num = String(idx + 1).padStart(2, "0");
            let label = (ans.label || `Pertanyaan ${idx + 1}`)
                .replace(/\r?\n|\r/g, " ")
                .replace(/\s+/g, " ")
                .trim();
            label = label.replace(/\s+\./g, ".");
            const val = Array.isArray(ans.value) ? ans.value.join(", ") : ans.value;
            lines.push(`[${num}] *${label}* ➔ "${val}"`);
        });

        lines.push("━━━━━━━━━━━━━━━━━━━━━━━");
        lines.push("✅ *Status:* Terverifikasi Berhasil Masuk Google Form (200 OK)");
        return lines.join("\n");
    }

    function showSubmissionDetail(item) {
        if (!item) return;
        currentDetailItem = item;
        const auditId = item.submission_id || `SUB-${item.nim}`;
        modalDetailTitle.textContent = `Tanggapan Responden: ${item.nama} (#${auditId})`;
        modalDetailSubtitle.textContent = `Formulir: ${item.form_title || 'Kuesioner Google'} • Disubmit: ${item.timestamp || '-'} WIB`;

        const chatText = formatSubmissionForChat(item);

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
            <!-- Section 1: Audit Trail & Spesifikasi Formulir (Standar Industri) -->
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(16, 185, 129, 0.06) 100%); border: 1px solid var(--border-dim); border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 14px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 8px;">
                    <div>
                        <span style="font-size:11px; text-transform:uppercase; letter-spacing:0.04em; color:var(--primary); font-weight:700;">AUDIT TRAIL FORMULIR GOOGLE</span>
                        <h4 style="margin:2px 0 0 0; font-size:13.5px; font-weight:600; color:var(--fg);">${escapeHtml(item.form_title || "KUESIONER PENGUJIAN SYSTEM USABILITY SCALE (SUS) APLIKASI AUGMENTED REALITY")}</h4>
                    </div>
                    <span class="badge badge-emerald" style="font-size:11px; flex-shrink:0;">
                        <i data-lucide="shield-check" style="width:13px; height:13px; margin-right:3px;"></i> ${escapeHtml(item.http_status || "HTTP 200 OK")}
                    </span>
                </div>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:8px; font-size:12px; margin-top:6px;">
                    <div><span class="text-muted">ID Transaksi Audit:</span> <strong class="font-mono">${escapeHtml(auditId)}</strong></div>
                    <div><span class="text-muted">Waktu Submisi:</span> <strong>${escapeHtml(item.timestamp || "-")} WIB</strong></div>
                    <div><span class="text-muted">Peran / Status:</span> <strong>${escapeHtml(item.status_responden || "Mahasiswa")}</strong></div>
                    <div><span class="text-muted">Total Butir Soal:</span> <strong>${(item.answers || []).length} Butir Terisi Penuh</strong></div>
                </div>
                ${item.form_url && item.form_url !== "-" ? `
                    <div style="margin-top:8px; border-top: 1px dashed var(--border-dim); padding-top:6px; font-size:11.5px;">
                        <span class="text-muted">URL Target Form:</span> 
                        <a href="${escapeHtml(item.form_url)}" target="_blank" rel="noopener noreferrer" style="color:var(--primary); word-break:break-all; text-decoration:underline;">
                            ${escapeHtml(item.form_url)} <i data-lucide="external-link" style="width:11px; height:11px; display:inline-block; vertical-align:middle;"></i>
                        </a>
                    </div>
                ` : ''}
            </div>

            <!-- Section 2: Data Responden & Demografi -->
            <div class="modal-detail-grid">
                <div class="modal-detail-item">
                    <span class="modal-detail-label">Nama Lengkap Responden</span>
                    <span class="modal-detail-val">${escapeHtml(item.nama)}</span>
                </div>
                <div class="modal-detail-item">
                    <span class="modal-detail-label">NIM / ID Mahasiswa</span>
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

            <!-- Section 3: Skor Metrik Riset (SUS) & Sentimen -->
            ${item.sus_score ? `
                <div style="background-color: var(--bg-surface); border: 1px solid var(--border-dim); border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 14px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:11px; text-transform:uppercase; font-weight:700; color:var(--fg-subtle);">SKOR SYSTEM USABILITY SCALE (SUS)</div>
                        <div style="font-size:20px; font-weight:800; color:var(--primary); margin:2px 0;">
                            ${item.sus_score} <span style="font-size:13px; font-weight:normal; color:var(--fg-muted);">/ 100</span>
                        </div>
                        <span class="badge badge-emerald" style="font-size:11px;">${escapeHtml(item.sus_grade || "Grade B - Sangat Baik")}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:11px; text-transform:uppercase; font-weight:700; color:var(--fg-subtle);">PROFIL SIKAP</div>
                        <div style="font-size:13px; font-weight:600; color:var(--fg); margin-top:3px;">${escapeHtml(item.profile || "Sangat Positif")}</div>
                    </div>
                </div>
            ` : ''}

            <!-- Section 4: Chat Format Preview (WhatsApp/Telegram) -->
            <div class="chat-preview-box">
                <div class="chat-preview-header">
                    <div class="chat-preview-header-title">
                        <i data-lucide="message-square"></i>
                        <span>Format Teks Chat Siap Kirim (WhatsApp / Telegram / IG)</span>
                    </div>
                    <button type="button" class="btn btn-xs btn-primary" id="btn-copy-preview-chat">
                        <i data-lucide="copy"></i> Salin Format Chat
                    </button>
                </div>
                <pre class="chat-preview-content">${escapeHtml(chatText)}</pre>
            </div>

            <div class="mt-4 mb-4">
                <div class="qa-section-title">
                    <span>Sebaran Pilihan Sikap / Skala</span>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    ${distBadges}
                </div>
            </div>

            <!-- Section 5: Daftar Jawaban Lengkap -->
            <div>
                <div class="qa-section-title">
                    <span>Daftar Input & Jawaban Lengkap (${(item.answers || []).length} Butir)</span>
                </div>
                <div class="qa-list">
                    ${qaRows || '<div class="text-muted text-center py-4">Tidak ada data jawaban tersimpan.</div>'}
                </div>
            </div>
        `;

        const btnCopyPreview = document.getElementById("btn-copy-preview-chat");
        if (btnCopyPreview) {
            btnCopyPreview.addEventListener("click", () => {
                navigator.clipboard.writeText(chatText).then(() => {
                    showToast(`✓ Format chat untuk ${item.nama} berhasil disalin! Siap dipaste ke WA/Telegram.`, "success");
                });
            });
        }

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

    function exportHistoryChat() {
        if (!historyData || historyData.length === 0) {
            showToast("Tidak ada riwayat untuk diekspor.", "info");
            return;
        }

        const itemsWithAnswers = historyData.filter(i => i.answers && i.answers.length > 0);
        if (itemsWithAnswers.length === 0) {
            showToast("Belum ada data rincian jawaban kuesioner yang tersimpan.", "info");
            return;
        }

        const blocks = itemsWithAnswers.map((item, idx) => {
            return `========================================\n` +
                   `RESPONDEN [${idx + 1}/${itemsWithAnswers.length}]: ${item.nama} (${item.nim})\n` +
                   `========================================\n\n` +
                   formatSubmissionForChat(item);
        });

        const fullContent = blocks.join("\n\n\n");
        const blob = new Blob([fullContent], { type: "text/plain;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `bukti_chat_kuesioner_${new Date().toISOString().slice(0, 10)}.txt`;
        link.click();
        showToast(`✓ File bukti chat (${itemsWithAnswers.length} responden) berhasil diunduh.`, "success");
    }

    function exportHistoryCSV() {
        if (!historyData || historyData.length === 0) {
            showToast("Tidak ada riwayat untuk diekspor.", "info");
            return;
        }

        let csv = "ID Audit,NIM,Nama,Peran Status,Formulir,Skor SUS,Grade SUS,Program Studi,Kampus,Waktu Submit,Status\n";
        historyData.forEach(item => {
            const auditId = item.submission_id || `SUB-${item.nim}`;
            const role = item.status_responden || "Mahasiswa";
            const form = (item.form_title || "Google Form").replace(/"/g, '""');
            const score = item.sus_score || "-";
            const grade = item.sus_grade || "-";
            const prodi = (item.prodi || "-").replace(/"/g, '""');
            const kampus = (item.universitas || item.dataset || "-").replace(/"/g, '""');
            const subTime = item.timestamp || "-";
            const status = item.http_status || "200 OK";
            csv += `"${auditId}","${item.nim}","${item.nama}","${role}","${form}","${score}","${grade}","${prodi}","${kampus}","${subTime}","${status}"\n`;
        });

        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `audit_responden_kuesioner_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
        showToast("File CSV audit riwayat berhasil diunduh.", "success");
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
