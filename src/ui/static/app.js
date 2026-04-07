(function () {
    const config = window.PETRA_UI_CONFIG || {};
    const apiPrefix = config.apiPrefix || "/api/v1";

    const fileInput = document.getElementById("file-input");
    const dropZone = document.getElementById("drop-zone");
    const resultsEl = document.getElementById("results");
    const rulesListEl = document.getElementById("rules-list");
    const selectedRuleCountEl = document.getElementById("selected-rule-count");
    const selectAllRulesBtn = document.getElementById("select-all-rules");
    const refreshRulesBtn = document.getElementById("refresh-rules");
    const statusPill = document.getElementById("status-pill");
    const stopAnalysisBtn = document.getElementById("stop-analysis");
    const documentIdEl = document.getElementById("document-id");
    const sourceTabEl = document.getElementById("tab-source");
    const extractedTabEl = document.getElementById("tab-extracted");
    const textAnalysisTabEl = document.getElementById("tab-text-analysis");
    const visualAnalysisTabEl = document.getElementById("tab-visual-analysis");
    const textAnalysisPanelEl = document.getElementById("text-analysis-panel");
    const visualAnalysisPanelEl = document.getElementById("visual-analysis-panel");
    const tabTriggers = Array.from(document.querySelectorAll(".tab-trigger"));

    let currentDocumentId = null;
    let currentJobId = null;
    let currentPollTimer = null;
    let currentSourcePreviewUrl = null;
    let currentSourceFilename = null;
    let availableRules = [];

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function setStatus(text, tone, isLoading) {
        statusPill.innerHTML = isLoading
            ? `<span class="inline-flex items-center gap-2"><span class="spinner h-4 w-4"></span><span>${escapeHtml(text)}</span></span>`
            : escapeHtml(text);
        statusPill.className = "rounded-full px-3 py-1.5 text-sm font-medium";
        if (tone === "error") {
            statusPill.classList.add("bg-rose-100", "text-rose-700");
            return;
        }
        if (tone === "success") {
            statusPill.classList.add("bg-emerald-100", "text-emerald-700");
            return;
        }
        if (tone === "working") {
            statusPill.classList.add("bg-amber-100", "text-amber-700");
            return;
        }
        statusPill.classList.add("bg-slate-100", "text-slate-600");
    }

    function setBusy(isBusy, message) {
        dropZone.classList.toggle("is-busy", isBusy);
        fileInput.disabled = isBusy;
        stopAnalysisBtn.classList.toggle("hidden", !isBusy);
        if (isBusy && message) {
            setStatus(message, "working", true);
        }
    }

    function stopPolling() {
        if (currentPollTimer) {
            window.clearTimeout(currentPollTimer);
            currentPollTimer = null;
        }
    }

    function updateSelectedRuleCount() {
        const count = document.querySelectorAll(".rule-checkbox:checked").length;
        selectedRuleCountEl.textContent = String(count);
    }

    function formatRuleType(type) {
        return String(type || "text").toUpperCase();
    }

    function verdictTone(verdict) {
        if (verdict === "pass") return "bg-emerald-100 text-emerald-700";
        if (verdict === "fail") return "bg-rose-100 text-rose-700";
        if (verdict === "not_applicable") return "bg-slate-200 text-slate-700";
        return "bg-amber-100 text-amber-700";
    }

    function ruleTypeTone(type) {
        if (type === "vision") return "bg-violet-100 text-violet-700";
        return "bg-cyan-100 text-cyan-700";
    }

    function renderRules(rules) {
        availableRules = Array.isArray(rules) ? rules : [];
        if (!availableRules.length) {
            rulesListEl.innerHTML = '<p class="text-sm text-slate-500">No rules available.</p>';
            updateSelectedRuleCount();
            return;
        }
        rulesListEl.innerHTML = availableRules.map((rule, index) => `
            <label class="flex cursor-pointer items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <input type="checkbox" class="rule-checkbox mt-1 h-4 w-4 rounded border-slate-300 text-slate-950 focus:ring-slate-500" data-rule-id="${escapeHtml(rule.id)}" checked />
                <div class="min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                        <h3 class="text-sm font-semibold text-slate-900">${escapeHtml(rule.name || rule.id)}</h3>
                        <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">${escapeHtml(rule.severity || "rule")}</span>
                        <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${ruleTypeTone(rule.analysis_type)}">${escapeHtml(formatRuleType(rule.analysis_type))}</span>
                    </div>
                    <p class="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">${escapeHtml(rule.id || "")}</p>
                    <p class="mt-3 text-sm leading-6 text-slate-600">${escapeHtml(rule.description || "")}</p>
                </div>
            </label>
        `).join("");
        document.querySelectorAll(".rule-checkbox").forEach((checkbox) => {
            checkbox.addEventListener("change", updateSelectedRuleCount);
        });
        updateSelectedRuleCount();
    }

    async function fetchRules() {
        try {
            const response = await fetch(`${apiPrefix}/rules`);
            if (!response.ok) throw new Error("Failed to load rules");
            const data = await response.json();
            renderRules(data.rules || []);
        } catch (error) {
            rulesListEl.innerHTML = `<p class="text-sm text-rose-600">${escapeHtml(error.message)}</p>`;
            updateSelectedRuleCount();
        }
    }

    function getSelectedRules() {
        const checkedIds = new Set(
            Array.from(document.querySelectorAll(".rule-checkbox:checked")).map((input) => input.dataset.ruleId)
        );
        return availableRules.filter((rule) => checkedIds.has(rule.id));
    }

    function renderEmptyState() {
        resultsEl.innerHTML = `
            <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center shadow-panel">
                <h2 class="text-lg font-semibold text-slate-900">No extraction yet</h2>
                <p class="mt-2 text-sm text-slate-500">Upload a PDF to inspect extracted page text.</p>
            </article>
        `;
    }

    function renderSourceTab(data) {
        const previewUrl = currentSourcePreviewUrl;
        const sourceFilename = (data && data.source_filename) || currentSourceFilename || "Source PDF";
        if (!previewUrl) {
            sourceTabEl.innerHTML = `
                <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center">
                    <h2 class="text-lg font-semibold text-slate-900">Original PDF unavailable</h2>
                    <p class="mt-2 text-sm text-slate-500">Upload a PDF to preview the local browser copy here.</p>
                </article>
            `;
            return;
        }

        sourceTabEl.innerHTML = `
            <div class="space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-3 rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                        <p class="text-sm font-semibold text-slate-900">${escapeHtml(sourceFilename)}</p>
                        <p class="text-xs text-slate-500">Local browser preview</p>
                    </div>
                    <a href="${escapeHtml(previewUrl)}" target="_blank" rel="noreferrer" class="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                        Open PDF
                    </a>
                </div>
                <iframe src="${escapeHtml(previewUrl)}" class="h-[900px] w-full rounded-[1.5rem] border border-slate-200 bg-white"></iframe>
            </div>
        `;
    }

    function renderRuleCards(rules, emptyMessage) {
        if (!rules.length) {
            return `
                <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5 text-sm text-slate-500">
                    ${escapeHtml(emptyMessage)}
                </article>
            `;
        }
        return rules.map((rule) => `
            <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5">
                <div class="flex flex-wrap items-center gap-3">
                    <h4 class="text-base font-semibold text-slate-950">${escapeHtml(rule.rule_name || rule.rule_id)}</h4>
                    <span class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${ruleTypeTone(rule.analysis_type)}">${escapeHtml(formatRuleType(rule.analysis_type))}</span>
                    <span class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${verdictTone(rule.verdict)}">${escapeHtml(rule.verdict || "needs_review")}</span>
                    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">${escapeHtml(rule.execution_status || "completed")}</span>
                    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">${escapeHtml((rule.matched_pages || []).length)} page match${(rule.matched_pages || []).length === 1 ? "" : "es"}</span>
                </div>
                <p class="mt-4 text-sm font-medium text-slate-900">${escapeHtml(rule.summary || "")}</p>
                <p class="mt-3 text-sm leading-6 text-slate-600">${escapeHtml(rule.reasoning || "")}</p>
                ${(rule.findings || []).length ? `
                    <div class="mt-4">
                        <h5 class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Findings</h5>
                        <ul class="mt-3 space-y-2">
                            ${(rule.findings || []).map((finding) => `
                                <li class="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">${escapeHtml(finding)}</li>
                            `).join("")}
                        </ul>
                    </div>
                ` : ""}
                ${(rule.citations || []).length ? `
                    <div class="mt-4">
                        <h5 class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Citations</h5>
                        <ul class="mt-3 space-y-2">
                            ${(rule.citations || []).map((citation) => `
                                <li class="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">Page ${escapeHtml(citation.page)}: ${escapeHtml(citation.evidence || "")}</li>
                            `).join("")}
                        </ul>
                    </div>
                ` : ""}
                ${(rule.notes || []).length ? `
                    <div class="mt-4">
                        <h5 class="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Notes</h5>
                        <ul class="mt-3 space-y-2">
                            ${(rule.notes || []).map((note) => `
                                <li class="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">${escapeHtml(note)}</li>
                            `).join("")}
                        </ul>
                    </div>
                ` : ""}
            </article>
        `).join("");
    }

    function renderPageRuleCards(items, emptyMessage) {
        if (!items.length) {
            return `
                <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5 text-sm text-slate-500">
                    ${escapeHtml(emptyMessage)}
                </article>
            `;
        }

        const groups = new Map();
        items.forEach((item) => {
            const key = String(item.page || 0);
            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key).push(item);
        });

        return Array.from(groups.entries())
            .sort((a, b) => Number(a[0]) - Number(b[0]))
            .map(([page, pageItems]) => `
                <section class="space-y-4 rounded-[1.5rem] border border-slate-200 bg-white p-5">
                    <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-4">
                        <h3 class="text-base font-semibold text-slate-950">Page ${escapeHtml(page)}</h3>
                        <span class="text-sm text-slate-500">${escapeHtml(pageItems.length)} rule result(s)</span>
                    </div>
                    <div class="space-y-4">
                        ${renderRuleCards(pageItems, "")}
                    </div>
                </section>
            `)
            .join("");
    }

    function renderAnalysisTabs(data) {
        const analysis = data && data.analysis ? data.analysis : null;
        if (!analysis) {
            textAnalysisPanelEl.innerHTML = `
                <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center">
                    <h2 class="text-lg font-semibold text-slate-900">No text analysis yet</h2>
                    <p class="mt-2 text-sm text-slate-500">Upload a PDF to see text/content rule results.</p>
                </article>
            `;
            visualAnalysisPanelEl.innerHTML = `
                <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center">
                    <h2 class="text-lg font-semibold text-slate-900">No visual analysis yet</h2>
                    <p class="mt-2 text-sm text-slate-500">Upload a PDF to inspect visual-rule status.</p>
                </article>
            `;
            return;
        }

        const textPageResults = Array.isArray(analysis.text_page_results) ? analysis.text_page_results : [];
        const visualPageResults = Array.isArray(analysis.visual_page_results) ? analysis.visual_page_results : [];
        textAnalysisPanelEl.innerHTML = `
            <section class="space-y-6">
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-base font-semibold text-slate-950">Text Rule Assessments By Page</h3>
                        <span class="text-sm text-slate-500">${escapeHtml(textPageResults.length)} page-rule result(s)</span>
                    </div>
                    ${renderPageRuleCards(textPageResults, "No text rules were selected for this run.")}
                </div>
            </section>
        `;

        visualAnalysisPanelEl.innerHTML = `
            <section class="space-y-6">
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-base font-semibold text-slate-950">Visual Rule Assessments By Page</h3>
                        <span class="text-sm text-slate-500">${escapeHtml(visualPageResults.length)} page-rule result(s)</span>
                    </div>
                    ${renderPageRuleCards(visualPageResults, "No visual rules were selected for this run.")}
                </div>
            </section>
        `;
    }

    function setActiveTab(name) {
        const mapping = {
            source: sourceTabEl,
            extracted: extractedTabEl,
            "text-analysis": textAnalysisTabEl,
            "visual-analysis": visualAnalysisTabEl
        };
        Object.entries(mapping).forEach(([key, element]) => {
            element.classList.toggle("hidden", key !== name);
        });
        tabTriggers.forEach((button) => {
            const active = button.dataset.tab === name;
            button.classList.toggle("bg-slate-950", active);
            button.classList.toggle("text-white", active);
            button.classList.toggle("bg-slate-100", !active);
            button.classList.toggle("text-slate-600", !active);
        });
    }

    function renderResults(pages) {
        if (!pages || !pages.length) {
            renderEmptyState();
            return;
        }

        resultsEl.innerHTML = pages.map((page) => {
            const tables = Array.isArray(page.tables) ? page.tables : [];
            const tableBlocks = tables.length ? tables.map((table) => `
                <article class="rounded-[1.25rem] border border-slate-200 bg-slate-50 p-4">
                    <div class="mb-3 flex items-center justify-between">
                        <h4 class="text-sm font-semibold text-slate-900">Table ${escapeHtml(table.index)}</h4>
                        <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">${escapeHtml((table.rows || []).length)} rows</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="min-w-full border-separate border-spacing-0 overflow-hidden rounded-xl">
                            <tbody>
                                ${(table.rows || []).map((row) => `
                                    <tr>
                                        ${(row || []).map((cell) => `<td class="border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">${escapeHtml(cell)}</td>`).join("")}
                                    </tr>
                                `).join("")}
                            </tbody>
                        </table>
                    </div>
                </article>
            `).join("") : '<p class="text-sm text-slate-500">No tables detected on this page.</p>';

            return `
                <section class="result-card p-6">
                    <div class="border-b border-slate-200 pb-5">
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Page ${escapeHtml(page.page)}</p>
                            <h3 class="mt-2 text-xl font-semibold text-slate-950">${escapeHtml(page.char_count || 0)} extracted characters</h3>
                            <p class="mt-2 text-sm text-slate-500">${tables.length} detected table${tables.length === 1 ? "" : "s"} on this page.</p>
                        </div>
                    </div>
                    <div class="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
                        <article class="rounded-[1.25rem] border border-slate-200 bg-slate-50 p-4">
                            <h4 class="text-sm font-semibold text-slate-900">Extracted Text</h4>
                            <pre class="mt-3 whitespace-pre-wrap break-words rounded-xl bg-white p-4 text-sm leading-6 text-slate-700">${escapeHtml(page.text || "") || "No text extracted."}</pre>
                        </article>
                        <div class="space-y-4">
                            <h4 class="text-sm font-semibold text-slate-900">Extracted Tables</h4>
                            ${tableBlocks}
                        </div>
                    </div>
                </section>
            `;
        }).join("");
    }

    function renderJobResult(data) {
        if (!data) {
            return;
        }
        currentDocumentId = data.document_id;
        documentIdEl.textContent = `Document ID: ${data.document_id}`;
        renderSourceTab(data);
        renderResults(data.pages || []);
        renderAnalysisTabs(data);
    }

    async function pollJob(jobId) {
        try {
            const response = await fetch(`${apiPrefix}/validations/jobs/${jobId}`);
            if (!response.ok) {
                throw new Error("Failed to fetch validation job status");
            }
            const data = await response.json();
            if (data.result) {
                renderJobResult(data.result);
            }

            const progressSuffix = data.progress_total
                ? ` (${data.progress_current}/${data.progress_total})`
                : "";

            if (data.status === "queued" || data.status === "running") {
                setBusy(true, `${data.message || "Analyzing PDF"}${progressSuffix}`);
                currentPollTimer = window.setTimeout(() => pollJob(jobId), 900);
                return;
            }

            stopPolling();
            setBusy(false);
            if (data.status === "completed") {
                setStatus("Analysis complete", "success", false);
                setActiveTab("text-analysis");
                return;
            }
            if (data.status === "cancelled") {
                setStatus("Analysis stopped", "error", false);
                return;
            }
            setStatus(data.error || data.message || "Analysis failed", "error", false);
        } catch (error) {
            stopPolling();
            setBusy(false);
            setStatus(error.message, "error", false);
        }
    }

    async function uploadPdf(file) {
        if (!file) return;
        stopPolling();
        currentJobId = null;
        if (currentSourcePreviewUrl) {
            URL.revokeObjectURL(currentSourcePreviewUrl);
        }
        currentSourcePreviewUrl = URL.createObjectURL(file);
        currentSourceFilename = file.name;
        setBusy(true, `Uploading ${file.name}`);
        documentIdEl.textContent = "";
        renderSourceTab({ source_filename: file.name });
        const formData = new FormData();
        formData.append("pdf", file);
        formData.append("rules_json", JSON.stringify({ rules: getSelectedRules() }));

        try {
            const response = await fetch(`${apiPrefix}/validations/jobs`, {
                method: "POST",
                body: formData
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Validation failed");
            }
            const data = await response.json();
            currentJobId = data.job_id;
            setStatus(data.message || `Analyzing ${file.name}`, "working", true);
            await pollJob(currentJobId);
        } catch (error) {
            setStatus(error.message, "error", false);
            renderSourceTab(null);
            renderEmptyState();
            renderAnalysisTabs(null);
        } finally {
            setBusy(false);
        }
    }

    dropZone.addEventListener("click", function () {
        fileInput.click();
    });

    fileInput.addEventListener("change", function (event) {
        const file = event.target.files && event.target.files[0];
        if (file && file.type === "application/pdf") {
            uploadPdf(file);
        }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            dropZone.classList.add("drop-active");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            dropZone.classList.remove("drop-active");
        });
    });

    dropZone.addEventListener("drop", function (event) {
        const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
        if (file && file.type === "application/pdf") {
            uploadPdf(file);
        }
    });

    tabTriggers.forEach((button) => {
        button.addEventListener("click", function () {
            setActiveTab(button.dataset.tab);
        });
    });

    selectAllRulesBtn.addEventListener("click", function () {
        const checkboxes = Array.from(document.querySelectorAll(".rule-checkbox"));
        const shouldSelectAll = checkboxes.some((checkbox) => !checkbox.checked);
        checkboxes.forEach((checkbox) => {
            checkbox.checked = shouldSelectAll;
        });
        updateSelectedRuleCount();
    });

    stopAnalysisBtn.addEventListener("click", async function () {
        if (!currentJobId) {
            return;
        }
        try {
            await fetch(`${apiPrefix}/validations/jobs/${currentJobId}/cancel`, {
                method: "POST"
            });
            setStatus("Stopping analysis...", "working", true);
        } catch (error) {
            setStatus(error.message, "error", false);
        }
    });

    refreshRulesBtn.addEventListener("click", fetchRules);

    renderSourceTab(null);
    renderEmptyState();
    renderAnalysisTabs(null);
    setActiveTab("source");
    fetchRules();
    window.addEventListener("beforeunload", function () {
        if (currentSourcePreviewUrl) {
            URL.revokeObjectURL(currentSourcePreviewUrl);
        }
    });
})();
