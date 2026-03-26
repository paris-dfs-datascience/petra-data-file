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
    const documentIdEl = document.getElementById("document-id");
    const analysisPanelEl = document.getElementById("analysis-panel");
    const sourceTabEl = document.getElementById("tab-source");
    const extractedTabEl = document.getElementById("tab-extracted");
    const analysisTabEl = document.getElementById("tab-analysis");
    const tabTriggers = Array.from(document.querySelectorAll(".tab-trigger"));

    let currentDocumentId = null;
    let availableRules = [];

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function setStatus(text, tone) {
        statusPill.textContent = text;
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

    function updateSelectedRuleCount() {
        const count = document.querySelectorAll(".rule-checkbox:checked").length;
        selectedRuleCountEl.textContent = String(count);
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
                <input type="checkbox" class="rule-checkbox mt-1 h-4 w-4 rounded border-slate-300 text-slate-950 focus:ring-slate-500" data-rule-id="${escapeHtml(rule.id)}" ${index < 3 ? "checked" : ""} />
                <div class="min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                        <h3 class="text-sm font-semibold text-slate-900">${escapeHtml(rule.name || rule.id)}</h3>
                        <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">${escapeHtml(rule.severity || "rule")}</span>
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
                <p class="mt-2 text-sm text-slate-500">Upload a PDF to inspect extracted text and table structures.</p>
            </article>
        `;
    }

    function renderSourceTab(data) {
        if (!data || !data.source_pdf_url) {
            sourceTabEl.innerHTML = `
                <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center">
                    <h2 class="text-lg font-semibold text-slate-900">Original PDF unavailable</h2>
                    <p class="mt-2 text-sm text-slate-500">A public URL is not available for this storage backend.</p>
                </article>
            `;
            return;
        }

        sourceTabEl.innerHTML = `
            <div class="space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-3 rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                        <p class="text-sm font-semibold text-slate-900">${escapeHtml(data.source_filename || "Source PDF")}</p>
                        <p class="text-xs text-slate-500">${escapeHtml(data.source_pdf_url)}</p>
                    </div>
                    <a href="${escapeHtml(data.source_pdf_url)}" target="_blank" rel="noreferrer" class="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white">
                        Open PDF
                    </a>
                </div>
                <iframe src="${escapeHtml(data.source_pdf_url)}" class="h-[900px] w-full rounded-[1.5rem] border border-slate-200 bg-white"></iframe>
            </div>
        `;
    }

    function renderAnalysisTab(data) {
        const analysis = data && data.analysis ? data.analysis : null;
        if (!analysis) {
            analysisPanelEl.innerHTML = `
                <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center">
                    <h2 class="text-lg font-semibold text-slate-900">No analysis yet</h2>
                    <p class="mt-2 text-sm text-slate-500">Upload a PDF to see analysis derived from the extracted content.</p>
                </article>
            `;
            return;
        }

        const overview = Array.isArray(analysis.overview) ? analysis.overview : [];
        const observations = Array.isArray(analysis.page_observations) ? analysis.page_observations : [];
        const ruleAssessments = Array.isArray(analysis.rule_assessments) ? analysis.rule_assessments : [];

        analysisPanelEl.innerHTML = `
            <section class="space-y-6">
                <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    ${overview.map((metric) => `
                        <article class="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
                            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">${escapeHtml(metric.label)}</p>
                            <p class="mt-3 text-3xl font-semibold tracking-tight text-slate-950">${escapeHtml(metric.value)}</p>
                            <p class="mt-3 text-sm leading-6 text-slate-500">${escapeHtml(metric.detail || "")}</p>
                        </article>
                    `).join("")}
                </div>
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-base font-semibold text-slate-950">Rule Assessments</h3>
                        <span class="text-sm text-slate-500">${escapeHtml(analysis.selected_rule_count || 0)} selected</span>
                    </div>
                    ${ruleAssessments.length ? ruleAssessments.map((rule) => `
                        <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5">
                            <div class="flex flex-wrap items-center gap-3">
                                <h4 class="text-base font-semibold text-slate-950">${escapeHtml(rule.rule_name || rule.rule_id)}</h4>
                                <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600">${escapeHtml((rule.matched_pages || []).length)} page match${(rule.matched_pages || []).length === 1 ? "" : "es"}</span>
                            </div>
                            <ul class="mt-4 space-y-2">
                                ${(rule.notes || []).map((note) => `
                                    <li class="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">${escapeHtml(note)}</li>
                                `).join("")}
                            </ul>
                        </article>
                    `).join("") : `
                        <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5 text-sm text-slate-500">
                            No rules were selected for this run.
                        </article>
                    `}
                </div>
                <div class="space-y-4">
                    ${observations.map((item) => `
                        <article class="rounded-[1.5rem] border border-slate-200 bg-white p-5">
                            <div class="flex items-center justify-between gap-3">
                                <h3 class="text-base font-semibold text-slate-950">Page ${escapeHtml(item.page)}</h3>
                            </div>
                            <ul class="mt-4 space-y-2">
                                ${(item.observations || []).map((observation) => `
                                    <li class="rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-600">${escapeHtml(observation)}</li>
                                `).join("")}
                            </ul>
                        </article>
                    `).join("")}
                </div>
            </section>
        `;
    }

    function setActiveTab(name) {
        const mapping = {
            source: sourceTabEl,
            extracted: extractedTabEl,
            analysis: analysisTabEl
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

    async function uploadPdf(file) {
        if (!file) return;
        setStatus(`Uploading ${file.name}`, "working");
        documentIdEl.textContent = "";
        const formData = new FormData();
        formData.append("pdf", file);
        formData.append("rules_json", JSON.stringify({ rules: getSelectedRules() }));

        try {
            const response = await fetch(`${apiPrefix}/validations`, {
                method: "POST",
                body: formData
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Validation failed");
            }
            const data = await response.json();
            currentDocumentId = data.document_id;
            documentIdEl.textContent = `Document ID: ${data.document_id}`;
            setStatus("Extraction complete", "success");
            renderSourceTab(data);
            renderResults(data.pages || []);
            renderAnalysisTab(data);
            setActiveTab("analysis");
        } catch (error) {
            setStatus(error.message, "error");
            renderSourceTab(null);
            renderEmptyState();
            renderAnalysisTab(null);
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

    refreshRulesBtn.addEventListener("click", fetchRules);

    renderSourceTab(null);
    renderEmptyState();
    renderAnalysisTab(null);
    setActiveTab("source");
    fetchRules();
})();
