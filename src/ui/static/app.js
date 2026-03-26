(function () {
    const config = window.PETRA_UI_CONFIG || {};
    const apiPrefix = config.apiPrefix || "/api/v1";

    const fileInput = document.getElementById("file-input");
    const dropZone = document.getElementById("drop-zone");
    const resultsEl = document.getElementById("results");
    const rulesListEl = document.getElementById("rules-list");
    const statusPill = document.getElementById("status-pill");
    const documentIdEl = document.getElementById("document-id");
    const refreshRulesBtn = document.getElementById("refresh-rules");
    const sendFeedbackBtn = document.getElementById("send-feedback");
    const feedbackStatusEl = document.getElementById("feedback-status");

    let currentDocumentId = null;

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

    async function fetchRules() {
        try {
            const response = await fetch(`${apiPrefix}/rules`);
            if (!response.ok) throw new Error("Failed to load rules");
            const data = await response.json();
            const rules = data.rules || [];
            if (!rules.length) {
                rulesListEl.innerHTML = '<p class="text-sm text-slate-500">No rules configured.</p>';
                return;
            }
            rulesListEl.innerHTML = rules.map((rule) => `
                <article class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div class="flex items-start justify-between gap-3">
                        <h3 class="text-sm font-semibold text-slate-900">${escapeHtml(rule.name || rule.id)}</h3>
                        <span class="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">${escapeHtml(rule.severity || "rule")}</span>
                    </div>
                    <p class="mt-2 text-xs uppercase tracking-[0.18em] text-slate-400">${escapeHtml(rule.id || "")}</p>
                    <p class="mt-3 text-sm leading-6 text-slate-600">${escapeHtml(rule.description || "")}</p>
                </article>
            `).join("");
        } catch (error) {
            rulesListEl.innerHTML = `<p class="text-sm text-rose-600">${escapeHtml(error.message)}</p>`;
        }
    }

    function renderEmptyState() {
        resultsEl.innerHTML = `
            <article class="rounded-[1.75rem] border border-slate-200 bg-white p-10 text-center shadow-panel">
                <h2 class="text-lg font-semibold text-slate-900">No validation yet</h2>
                <p class="mt-2 text-sm text-slate-500">Upload a PDF to inspect results, citations, and feedback controls.</p>
            </article>
        `;
    }

    function renderResults(pages) {
        if (!pages || !pages.length) {
            renderEmptyState();
            return;
        }

        resultsEl.innerHTML = pages.map((page) => {
            const rules = Array.isArray(page.rules) ? page.rules : [];
            const ruleCards = rules.map((rule) => {
                const citations = Array.isArray(rule.citations) ? rule.citations : [];
                const tone = rule.status === "pass" ? "emerald" : "rose";
                const feedbackKey = `fb_${page.page}_${rule.rule_id}`;
                return `
                    <article class="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
                        <div class="flex flex-col gap-4 xl:flex-row xl:justify-between">
                            <div class="min-w-0 flex-1">
                                <div class="flex flex-wrap items-center gap-3">
                                    <h4 class="text-base font-semibold text-slate-950">${escapeHtml(rule.rule_name || rule.rule_id)}</h4>
                                    <span class="rounded-full bg-${tone}-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-${tone}-700">${escapeHtml(rule.status)}</span>
                                </div>
                                <p class="mt-3 text-sm leading-6 text-slate-600">${escapeHtml(rule.reasoning || "")}</p>
                                ${citations.length ? `
                                    <ul class="mt-4 space-y-2 text-sm text-slate-500">
                                        ${citations.map((citation) => `<li class="rounded-xl bg-white px-3 py-2">Page ${escapeHtml(citation.page)}${citation.evidence ? ` · ${escapeHtml(citation.evidence)}` : ""}</li>`).join("")}
                                    </ul>
                                ` : ""}
                            </div>
                            <div class="min-w-[220px] rounded-[1.25rem] border border-slate-200 bg-white p-4">
                                <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Reviewer feedback</p>
                                <div class="mt-3 grid gap-2">
                                    <label class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-600">
                                        <input type="radio" name="${feedbackKey}" value="confirm" />
                                        Confirm
                                    </label>
                                    <label class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-600">
                                        <input type="radio" name="${feedbackKey}" value="flag" />
                                        Flag
                                    </label>
                                </div>
                                <textarea data-rule-id="${escapeHtml(rule.rule_id)}" data-page="${escapeHtml(page.page)}" class="feedback-note mt-3 min-h-[88px] w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-slate-400" placeholder="Optional note"></textarea>
                            </div>
                        </div>
                    </article>
                `;
            }).join("");

            return `
                <section class="result-card p-6">
                    <div class="flex flex-col gap-5 border-b border-slate-200 pb-5 md:flex-row md:items-start">
                        <img src="${escapeHtml(page.image_data_url)}" alt="Page ${escapeHtml(page.page)}" class="h-56 w-40 rounded-[1.25rem] border border-slate-200 object-cover bg-slate-100" />
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Page ${escapeHtml(page.page)}</p>
                            <h3 class="mt-2 text-xl font-semibold text-slate-950">${rules.length} rule result${rules.length === 1 ? "" : "s"}</h3>
                            <p class="mt-2 text-sm text-slate-500">Each rule is evaluated independently against the rendered page image.</p>
                        </div>
                    </div>
                    <div class="mt-6 space-y-4">${ruleCards}</div>
                </section>
            `;
        }).join("");
    }

    async function uploadPdf(file) {
        if (!file) return;
        setStatus(`Uploading ${file.name}`, "working");
        documentIdEl.textContent = "";
        feedbackStatusEl.textContent = "";
        const formData = new FormData();
        formData.append("pdf", file);

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
            setStatus("Validation complete", "success");
            renderResults(data.pages || []);
        } catch (error) {
            setStatus(error.message, "error");
            renderEmptyState();
        }
    }

    function collectFeedback() {
        const items = [];
        document.querySelectorAll(".feedback-note").forEach((noteEl) => {
            const ruleId = noteEl.dataset.ruleId;
            const page = Number(noteEl.dataset.page);
            const selected = document.querySelector(`input[name="fb_${page}_${CSS.escape(ruleId)}"]:checked`);
            const note = noteEl.value.trim();
            if (!selected && !note) return;
            items.push({
                rule_id: ruleId,
                page: page,
                verdict: selected ? selected.value : "note",
                note: note
            });
        });
        return items;
    }

    async function sendFeedback() {
        const items = collectFeedback();
        if (!items.length) {
            feedbackStatusEl.textContent = "No feedback to send.";
            feedbackStatusEl.className = "mt-3 text-sm text-rose-600";
            return;
        }

        sendFeedbackBtn.disabled = true;
        feedbackStatusEl.textContent = "";

        try {
            const response = await fetch(`${apiPrefix}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    document_id: currentDocumentId || "unknown",
                    items: items
                })
            });
            if (!response.ok) throw new Error("Failed to send feedback");
            const data = await response.json();
            feedbackStatusEl.textContent = data.message || "Feedback sent.";
            feedbackStatusEl.className = "mt-3 text-sm text-emerald-600";
        } catch (error) {
            feedbackStatusEl.textContent = error.message;
            feedbackStatusEl.className = "mt-3 text-sm text-rose-600";
        } finally {
            sendFeedbackBtn.disabled = false;
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

    refreshRulesBtn.addEventListener("click", fetchRules);
    sendFeedbackBtn.addEventListener("click", sendFeedback);

    renderEmptyState();
    fetchRules();
})();
