from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import typer
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, Response
from pydantic import BaseModel

from src.pipeline.graph import build_graph
from src.schemas import DocumentResult
from src.config import load_app_yaml, project_paths


# ========== Feedback Models ==========
class FeedbackItem(BaseModel):
    rule_id: str
    page: int
    verdict: str  # "confirm" | "flag"
    note: Optional[str] = ""


class FeedbackRequest(BaseModel):
    document_id: str
    items: List[FeedbackItem]


cli = typer.Typer(help="RAG Vision Pipeline CLI")
app = FastAPI(title="RAG Vision Pipeline")


def _load_rules(rules_json_path: Optional[str] = None, rules_json_str: Optional[str] = None) -> list[dict]:
    if rules_json_str:
        return json.loads(rules_json_str)["rules"]
    path = rules_json_path or "rules/rules.json"
    return json.loads(Path(path).read_text(encoding="utf-8"))["rules"]


def _run_pipeline(pdf_path: str, rules_json_path: Optional[str] = None, rules_json_str: Optional[str] = None):
    rules = _load_rules(rules_json_path=rules_json_path, rules_json_str=rules_json_str)

    graph = build_graph()
    state = {
        "pdf_path": pdf_path,
        "rules": rules,
    }
    result = graph.invoke(state)
    # bundle with new page-based structure
    doc_res = DocumentResult(document_id=result["doc_id"], pages=result.get("pages", []))
    return doc_res.model_dump()


@cli.command("validate")
def cli_validate(
    pdf: str = typer.Option(..., help="Path to the PDF"),
    rules: Optional[str] = typer.Option(None, help="Path to rules JSON. Defaults to rules/rules.json"),
    out: Optional[str] = typer.Option(None, help="Where to write the results JSON. Default under data/reports"),
):
    data = _run_pipeline(pdf_path=pdf, rules_json_path=rules)
    if out is None:
        app_cfg = load_app_yaml()
        paths = project_paths(app_cfg)
        Path(paths["reports"]).mkdir(parents=True, exist_ok=True)
        out = str(paths["reports"] / f"{data['document_id']}.json")
    Path(out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(f"Wrote {out}")


@app.get("/rules")
async def api_rules(rules_path: Optional[str] = None):
    try:
        rules = _load_rules(rules_json_path=rules_path)
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "Rules file not found."})
    except json.JSONDecodeError as exc:
        return JSONResponse(status_code=400, content={"detail": f"Invalid rules JSON: {exc}"})
    return {"rules": rules}


@app.get("/", response_class=HTMLResponse)
async def ui_root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Petra Vision</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        :root {
            color-scheme: light dark;
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
            margin: 0;
            background: #0f172a;
            color: #f8fafc;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px 20px 48px;
        }
        h1 {
            margin-top: 0;
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .logo {
            height: 60px;
            width: auto;
            max-width: 200px;
            filter: brightness(0) invert(1);
        }
        .subtitle {
            margin-top: 0;
            color: #cbd5f5;
            margin-bottom: 32px;
        }
        .layout {
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }
        .panel {
            background: #131c34;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 20px;
            flex: 1 1 320px;
            min-width: 280px;
        }
        .panel h2 {
            margin: 0 0 16px;
            font-size: 1.2rem;
        }
        .panel.hidden {
            display: none;
        }
        .toggle-btn {
            background: linear-gradient(135deg, #475569, #64748b);
            border: none;
            color: #fff;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s ease, opacity 0.2s ease;
            margin-bottom: 16px;
        }
        .toggle-btn:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        #drop-zone {
            border: 2px dashed #475569;
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            cursor: pointer;
            transition: border-color 0.2s linear, background 0.2s linear;
            background: #0f172a;
        }
        #drop-zone.dragover {
            border-color: #38bdf8;
            background: rgba(56, 189, 248, 0.1);
        }
        #drop-zone input[type="file"] {
            display: none;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: linear-gradient(135deg, #38bdf8, #6366f1);
            border: none;
            color: #fff;
            border-radius: 999px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
            margin-top: 12px;
        }
        .btn:hover {
            transform: translateY(-1px);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
        }
        #download-btn-container {
            display: none;
            margin-top: 16px;
            margin-bottom: 8px;
        }
        #download-btn-container.visible {
            display: block;
        }
        #status {
            margin-top: 12px;
            font-size: 0.95rem;
            color: #cbd5f5;
        }
        #results {
            margin-top: 24px;
            display: grid;
            gap: 20px;
        }
        .rule-card {
            background: #0b1225;
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .rule-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }
        .rule-name {
            font-size: 1.05rem;
            font-weight: 600;
            margin: 0;
        }
        .rule-status {
            padding: 4px 12px;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        .status-pass {
            border: 1px solid rgba(74, 222, 128, 0.35);
            color: #4ade80;
            background: rgba(22, 101, 52, 0.35);
        }
        .status-fail {
            border: 1px solid rgba(248, 113, 113, 0.35);
            color: #f87171;
            background: rgba(127, 29, 29, 0.35);
        }
        .reasoning {
            line-height: 1.5;
            color: #e2e8f0;
            white-space: pre-wrap;
        }
        .citations {
            font-size: 0.9rem;
            color: #cbd5f5;
            margin: 0;
            padding-left: 18px;
        }
        .preview-gallery {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        .preview-gallery img {
            width: 160px;
            height: 220px;
            object-fit: cover;
            border-radius: 12px;
            border: 1px solid #1f2937;
            background: #111827;
        }
        .rules-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 6px;
        }
        .rule-item {
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 12px;
            background: #0b1225;
        }
        .rule-item h3 {
            margin: 0 0 6px;
            font-size: 1rem;
        }
        .rule-meta {
            font-size: 0.85rem;
            color: #94a3b8;
        }
        .empty-state {
            text-align: center;
            color: #94a3b8;
            font-size: 0.95rem;
            margin-top: 24px;
        }
        /* Feedback Section Styles */
        .rule-card-grid {
            display: grid;
            grid-template-columns: 1fr 160px;
            gap: 12px;
            align-items: start;
        }
        .rule-info {
            display: flex;
            flex-direction: column;
            gap: 12px;
            min-width: 0;
        }
        .feedback-section {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding-left: 12px;
            border-left: 1px solid #1f2937;
        }
        .feedback-label {
            font-size: 0.7rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 2px;
        }
        .feedback-toggles {
            display: flex;
            gap: 4px;
        }
        .fb-btn {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 4px 8px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 500;
            border: 1px solid #374151;
            background: #1f2937;
            color: #e2e8f0;
            transition: all 0.15s ease;
        }
        .fb-btn:hover {
            border-color: #4b5563;
        }
        .fb-btn.selected-confirm {
            background: rgba(22, 101, 52, 0.5);
            border-color: #4ade80;
            color: #4ade80;
        }
        .fb-btn.selected-flag {
            background: rgba(127, 29, 29, 0.5);
            border-color: #f87171;
            color: #f87171;
        }
        .fb-btn input[type="radio"] {
            display: none;
        }
        .feedback-note {
            width: 100%;
            min-height: 36px;
            max-height: 60px;
            padding: 6px 8px;
            border-radius: 6px;
            border: 1px solid #374151;
            background: #1f2937;
            color: #e2e8f0;
            font-size: 0.75rem;
            resize: vertical;
            font-family: inherit;
            box-sizing: border-box;
        }
        .feedback-note::placeholder {
            color: #6b7280;
        }
        .feedback-note:focus {
            outline: none;
            border-color: #6366f1;
        }
        /* Feedback Footer */
        #feedback-footer {
            display: none;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, #0f172a 80%, transparent);
            padding: 24px 20px 20px;
            z-index: 100;
        }
        #feedback-footer.visible {
            display: block;
        }
        #feedback-footer .footer-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            align-items: center;
        }
        #feedback-status {
            color: #4ade80;
            font-size: 0.9rem;
            margin-right: auto;
        }
        .btn-feedback {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        @media (max-width: 768px) {
            .preview-gallery img {
                width: 120px;
                height: 160px;
            }
            .rule-card-grid {
                grid-template-columns: 1fr;
            }
            .feedback-section {
                border-left: none;
                border-top: 1px solid #1f2937;
                padding-left: 0;
                padding-top: 12px;
            }
        }
        /* Centerline guide toggle (FMT-HEADINGS only) */
        .centerline-toggle {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            font-size: 0.75rem;
            color: #94a3b8;
        }
        .centerline-toggle label {
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .centerline-switch {
            position: relative;
            width: 32px;
            height: 18px;
            background: #374151;
            border-radius: 9px;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        .centerline-switch::after {
            content: "";
            position: absolute;
            top: 2px;
            left: 2px;
            width: 14px;
            height: 14px;
            background: #9ca3af;
            border-radius: 50%;
            transition: transform 0.2s ease, background 0.2s ease;
        }
        .centerline-toggle input {
            display: none;
        }
        .centerline-toggle input:checked + .centerline-switch {
            background: rgba(239, 68, 68, 0.5);
        }
        .centerline-toggle input:checked + .centerline-switch::after {
            transform: translateX(14px);
            background: #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Petra Vision</h1>
            <img src="/petra-logo.svg" alt="Petra Logo" class="logo" />
        </div>
        <p class="subtitle">Drag and drop a PDF to validate against the configured rules.</p>
        <button class="toggle-btn" type="button" id="toggle-rules">Hide Configured Rules</button>
        <div class="layout">
            <section class="panel" id="rules-panel" style="max-width: 360px;">
                <h2>Configured Rules</h2>
                <div id="rules-list" class="rules-list">
                    <div class="empty-state">Loading rules...</div>
                </div>
            </section>
            <section class="panel" style="flex: 2 1 520px;">
                <div id="drop-zone">
                    <strong>Drop PDF here</strong>
                    <p>or click to select a file</p>
                    <button class="btn" type="button" id="choose-file">Choose PDF</button>
                    <input type="file" id="file-input" accept=".pdf" />
                    <div id="status">No file uploaded yet.</div>
                </div>
                <div id="download-btn-container">
                    <button class="btn btn-secondary" type="button" id="download-pdf">
                        📄 Download Results as PDF
                    </button>
                </div>
                <div id="results"></div>
            </section>
        </div>
    </div>
    <!-- Feedback Footer -->
    <div id="feedback-footer">
        <div class="footer-inner">
            <span id="feedback-status"></span>
            <button class="btn btn-feedback" type="button" id="send-feedback-btn">
                Send Feedback
            </button>
        </div>
    </div>
    <script>
        const dropZone = document.getElementById("drop-zone");
        const fileInput = document.getElementById("file-input");
        const chooseFileBtn = document.getElementById("choose-file");
        const statusEl = document.getElementById("status");
        const resultsEl = document.getElementById("results");
        const rulesListEl = document.getElementById("rules-list");
        const downloadBtnContainer = document.getElementById("download-btn-container");
        const downloadBtn = document.getElementById("download-pdf");
        const toggleRulesBtn = document.getElementById("toggle-rules");
        const rulesPanel = document.getElementById("rules-panel");
        let currentDocumentId = null;

        // Toggle rules panel visibility
        toggleRulesBtn.addEventListener("click", () => {
            if (rulesPanel.classList.contains("hidden")) {
                rulesPanel.classList.remove("hidden");
                toggleRulesBtn.textContent = "Hide Configured Rules";
            } else {
                rulesPanel.classList.add("hidden");
                toggleRulesBtn.textContent = "Show Configured Rules";
            }
        });

        const fetchRules = async () => {
            try {
                const resp = await fetch("/rules");
                if (!resp.ok) {
                    throw new Error("Failed to load rules");
                }
                const data = await resp.json();
                renderRules(data.rules || []);
            } catch (err) {
                rulesListEl.innerHTML = `<div class="empty-state">${err.message}</div>`;
            }
        };

        const renderRules = (rules) => {
            if (!rules || rules.length === 0) {
                rulesListEl.innerHTML = '<div class="empty-state">No rules configured.</div>';
                return;
            }
            rulesListEl.innerHTML = "";
            rules.forEach((rule) => {
                const wrapper = document.createElement("article");
                wrapper.className = "rule-item";
                wrapper.innerHTML = `
                    <h3>${escapeHtml(rule.name || rule.id || "Untitled Rule")}</h3>
                    ${rule.description ? `<p>${escapeHtml(rule.description)}</p>` : ""}
                    <p class="rule-meta">
                        <strong>ID:</strong> ${escapeHtml(rule.id || "N/A")}
                        ${rule.severity ? ` - <strong>Severity:</strong> ${escapeHtml(rule.severity)}` : ""}
                    </p>
                    <p class="rule-meta"><strong>Query:</strong> ${escapeHtml(rule.query || "")}</p>
                `;
                rulesListEl.appendChild(wrapper);
            });
        };

        const escapeHtml = (value) => {
            if (value === undefined || value === null) {
                return "";
            }
            return value
                .toString()
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        };

        const uploadPdf = async (file) => {
            if (!file) {
                return;
            }
            statusEl.textContent = `Uploading ${file.name}.`;
            dropZone.classList.remove("dragover");
            resultsEl.innerHTML = "";
            downloadBtnContainer.classList.remove("visible");
            currentDocumentId = null;
            const formData = new FormData();
            formData.append("pdf", file);
            try {
                const response = await fetch("/validate", {
                    method: "POST",
                    body: formData,
                });
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(text || "Validation failed");
                }
                const data = await response.json();
                statusEl.textContent = `Validation complete for document ${data.document_id}.`;
                currentDocumentId = data.document_id;
                renderResults(data.pages || []);
                downloadBtnContainer.classList.add("visible");
            } catch (error) {
                statusEl.textContent = `Error: ${error.message}`;
            }
        };

        const feedbackFooter = document.getElementById("feedback-footer");
        const sendFeedbackBtn = document.getElementById("send-feedback-btn");
        const feedbackStatusEl = document.getElementById("feedback-status");

        const renderResults = (pages) => {
            if (!pages || pages.length === 0) {
                resultsEl.innerHTML = '<div class="empty-state">No validation results returned.</div>';
                feedbackFooter.classList.remove("visible");
                return;
            }
            resultsEl.innerHTML = "";
            pages.forEach((page) => {
                // Create a page section
                const pageSection = document.createElement("div");
                pageSection.style.marginBottom = "32px";
                
                // Page header with image preview
                const pageHeader = document.createElement("div");
                pageHeader.style.cssText = "display: flex; align-items: center; gap: 16px; margin-bottom: 16px; padding: 16px; background: #0b1225; border-radius: 12px; border: 1px solid #1f2937;";
                const pageImageId = `page-img-${page.page}`;
                pageHeader.innerHTML = `
                    <img id="${pageImageId}" src="${escapeAttribute(page.image_data_url)}" alt="Page ${escapeHtml(page.page)}" 
                         data-original="${escapeAttribute(page.image_data_url)}"
                         data-centerline="${escapeAttribute(page.image_data_url_centerline || page.image_data_url)}"
                         style="width: 120px; height: 160px; object-fit: cover; border-radius: 8px; border: 1px solid #1f2937;" />
                    <div>
                        <h2 style="margin: 0 0 8px; font-size: 1.25rem; color: #f8fafc;">Page ${escapeHtml(page.page)}</h2>
                        <p style="margin: 0; color: #94a3b8; font-size: 0.9rem;">${(page.rules || []).length} rule(s) evaluated</p>
                    </div>
                `;
                pageSection.appendChild(pageHeader);
                
                // Render each rule result for this page
                const rules = Array.isArray(page.rules) ? page.rules : [];
                rules.forEach((result) => {
                    const card = document.createElement("article");
                    card.className = "rule-card";
                    card.style.marginBottom = "12px";
                    const statusClass = result.status === "pass" ? "status-pass" : "status-fail";
                    const citations = Array.isArray(result.citations) ? result.citations : [];
                    const ruleId = escapeHtml(result.rule_id || result.rule_name || "unknown");
                    const pageNum = page.page;
                    const feedbackKey = `fb_${pageNum}_${ruleId}`;
                    
                    // Check if this is the FMT-HEADINGS rule (show centerline toggle)
                    const isFmtHeadings = result.rule_id === "FMT-HEADINGS";
                    const centerlineToggleHtml = isFmtHeadings ? `
                        <div class="centerline-toggle">
                            <label>
                                <input type="checkbox" class="centerline-checkbox" data-page="${pageNum}">
                                <span class="centerline-switch"></span>
                                <span>Center guide</span>
                            </label>
                        </div>
                    ` : "";
                    
                    card.innerHTML = `
                        <div class="rule-card-grid">
                            <div class="rule-info">
                                <header class="rule-header">
                                    <h3 class="rule-name">${ruleId}</h3>
                                    <span class="rule-status ${statusClass}">${escapeHtml(result.status || "unknown")}</span>
                                </header>
                                <div class="reasoning">${escapeHtml(result.reasoning || "")}</div>
                                ${citations.length > 0 ? `
                                    <div>
                                        <strong>Citations</strong>
                                        <ul class="citations">
                                            ${citations.map((c) => `<li>Page ${escapeHtml(c.page)}${c.evidence ? ` - ${escapeHtml(c.evidence)}` : ""}</li>`).join("")}
                                        </ul>
                                    </div>
                                ` : ""}
                                ${centerlineToggleHtml}
                            </div>
                            <div class="feedback-section" data-rule-id="${ruleId}" data-page="${pageNum}">
                                <div class="feedback-label">Your Feedback</div>
                                <div class="feedback-toggles">
                                    <label class="fb-btn" data-type="confirm">
                                        <input type="radio" name="${feedbackKey}" value="confirm">
                                        ✓ Confirm
                                    </label>
                                    <label class="fb-btn" data-type="flag">
                                        <input type="radio" name="${feedbackKey}" value="flag">
                                        ⚑ Flag
                                    </label>
                                </div>
                                <textarea class="feedback-note" placeholder="Add a note (optional)..."></textarea>
                            </div>
                        </div>
                    `;
                    pageSection.appendChild(card);
                });
                
                resultsEl.appendChild(pageSection);
            });
            
            // Show feedback footer and attach toggle listeners
            feedbackFooter.classList.add("visible");
            feedbackStatusEl.textContent = "";
            
            // Add click listeners to feedback toggle buttons
            document.querySelectorAll(".fb-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    const toggles = btn.closest(".feedback-toggles");
                    toggles.querySelectorAll(".fb-btn").forEach((b) => {
                        b.classList.remove("selected-confirm", "selected-flag");
                    });
                    const type = btn.getAttribute("data-type");
                    btn.classList.add(type === "confirm" ? "selected-confirm" : "selected-flag");
                    btn.querySelector("input").checked = true;
                });
            });
            
            // Add click listeners for centerline toggle (FMT-HEADINGS only)
            document.querySelectorAll(".centerline-checkbox").forEach((checkbox) => {
                checkbox.addEventListener("change", () => {
                    const pageNum = checkbox.getAttribute("data-page");
                    const pageImg = document.getElementById(`page-img-${pageNum}`);
                    if (pageImg) {
                        if (checkbox.checked) {
                            pageImg.src = pageImg.getAttribute("data-centerline");
                        } else {
                            pageImg.src = pageImg.getAttribute("data-original");
                        }
                    }
                });
            });
        };

        const escapeAttribute = (value) => {
            if (!value) return "";
            return value
                .toString()
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        };

        // Prevent browser from opening the file when dragged over the page
        document.addEventListener("dragenter", (event) => {
            event.preventDefault();
        });

        document.addEventListener("dragover", (event) => {
            event.preventDefault();
        });

        document.addEventListener("drop", (event) => {
            event.preventDefault();
        });

        dropZone.addEventListener("dragenter", (event) => {
            event.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragover", (event) => {
            event.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", (event) => {
            event.preventDefault();
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropZone.classList.remove("dragover");
            const file = event.dataTransfer.files[0];
            if (file && file.type === "application/pdf") {
                uploadPdf(file);
            } else {
                statusEl.textContent = "Please drop a valid PDF file.";
            }
        });

        chooseFileBtn.addEventListener("click", () => {
            fileInput.click();
        });

        fileInput.addEventListener("change", (event) => {
            const file = event.target.files[0];
            if (file && file.type === "application/pdf") {
                uploadPdf(file);
            } else {
                statusEl.textContent = "Please choose a valid PDF file.";
            }
        });

        const downloadAsPDF = async () => {
            if (!resultsEl || resultsEl.children.length === 0) {
                return;
            }
            
            downloadBtn.disabled = true;
            downloadBtn.textContent = "⏳ Generating PDF...";
            
            try {
                // Create a temporary container for PDF generation with proper styling
                const pdfContainer = document.createElement("div");
                pdfContainer.style.cssText = "background: #ffffff; color: #000000; padding: 40px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto;";
                
                // Add header
                const header = document.createElement("div");
                header.style.cssText = "margin-bottom: 30px; border-bottom: 2px solid #e5e7eb; padding-bottom: 20px;";
                header.innerHTML = `
                    <h1 style="margin: 0 0 8px; font-size: 2rem; color: #111827;">Petra Vision - Results Report</h1>
                    <p style="margin: 0; color: #6b7280; font-size: 0.95rem;">Document ID: ${escapeHtml(currentDocumentId || "N/A")}</p>
                    <p style="margin: 4px 0 0; color: #6b7280; font-size: 0.85rem;">Generated: ${new Date().toLocaleString()}</p>
                `;
                pdfContainer.appendChild(header);
                
                // Clone and style the results
                const resultsClone = resultsEl.cloneNode(true);
                const styleClone = resultsClone.style;
                styleClone.cssText = "margin: 0; padding: 0;";
                
                // Update styles for PDF (convert dark theme to light theme)
                const updateStylesForPDF = (element) => {
                    if (element.nodeType === 1) { // Element node
                        const computedStyle = window.getComputedStyle(element);
                        
                        // Update background colors
                        if (element.classList && element.classList.contains("rule-card")) {
                            element.style.background = "#f9fafb";
                            element.style.border = "1px solid #e5e7eb";
                            element.style.color = "#111827";
                            element.style.setProperty("page-break-inside", "avoid");
                            element.style.setProperty("break-inside", "avoid");
                            element.style.setProperty("-webkit-column-break-inside", "avoid");
                        }
                        
                        if (element.classList && element.classList.contains("status-pass")) {
                            element.style.background = "rgba(34, 197, 94, 0.1)";
                            element.style.color = "#16a34a";
                            element.style.border = "1px solid rgba(34, 197, 94, 0.3)";
                        }
                        
                        if (element.classList && element.classList.contains("status-fail")) {
                            element.style.background = "rgba(239, 68, 68, 0.1)";
                            element.style.color = "#dc2626";
                            element.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                        }
                        
                        // Update text colors
                        if (element.tagName === "H2" || element.tagName === "H3") {
                            element.style.color = "#111827";
                        }
                        
                        if (element.classList && (element.classList.contains("reasoning") || element.classList.contains("citations"))) {
                            element.style.color = "#374151";
                        }
                        
                        // Update page header styles
                        if (element.style && element.style.cssText && element.style.cssText.includes("background: #0b1225")) {
                            element.style.background = "#f3f4f6";
                            element.style.border = "1px solid #e5e7eb";
                            element.style.color = "#111827";
                        }
                        
                        // Recursively update children
                        Array.from(element.children).forEach(updateStylesForPDF);
                    }
                };
                
                Array.from(resultsClone.children).forEach(updateStylesForPDF);
                pdfContainer.appendChild(resultsClone);
                
                // Configure PDF options
                const opt = {
                    margin: [20, 20, 20, 20],
                    filename: `audit-results-${currentDocumentId || "report"}-${new Date().toISOString().split("T")[0]}.pdf`,
                    image: { type: "jpeg", quality: 0.98 },
                    html2canvas: { 
                        scale: 2,
                        useCORS: true,
                        logging: false,
                        backgroundColor: "#ffffff"
                    },
                    pagebreak: {
                        mode: ["css", "avoid-all"]
                    },
                    jsPDF: { 
                        unit: "mm", 
                        format: "a4", 
                        orientation: "portrait" 
                    }
                };
                
                await html2pdf().set(opt).from(pdfContainer).save();
                
            } catch (error) {
                console.error("Error generating PDF:", error);
                statusEl.textContent = `Error generating PDF: ${error.message}`;
            } finally {
                downloadBtn.disabled = false;
                downloadBtn.textContent = "📄 Download Results as PDF";
            }
        };
        
        downloadBtn.addEventListener("click", downloadAsPDF);

        // Send Feedback Logic
        const collectFeedback = () => {
            const items = [];
            document.querySelectorAll(".feedback-section").forEach((section) => {
                const ruleId = section.getAttribute("data-rule-id");
                const pageNum = parseInt(section.getAttribute("data-page"), 10);
                const selectedRadio = section.querySelector("input[type='radio']:checked");
                const noteEl = section.querySelector(".feedback-note");
                const note = noteEl ? noteEl.value.trim() : "";
                
                // Only include if user has interacted (selected or wrote a note)
                if (selectedRadio || note) {
                    items.push({
                        rule_id: ruleId,
                        page: pageNum,
                        verdict: selectedRadio ? selectedRadio.value : "none",
                        note: note,
                    });
                }
            });
            return items;
        };

        const sendFeedback = async () => {
            const items = collectFeedback();
            if (items.length === 0) {
                feedbackStatusEl.textContent = "No feedback to send. Select Confirm/Flag or add a note.";
                feedbackStatusEl.style.color = "#f87171";
                return;
            }
            
            sendFeedbackBtn.disabled = true;
            sendFeedbackBtn.textContent = "Sending...";
            feedbackStatusEl.textContent = "";
            
            try {
                const response = await fetch("/feedback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        document_id: currentDocumentId || "unknown",
                        items: items,
                    }),
                });
                
                if (!response.ok) {
                    throw new Error("Failed to send feedback");
                }
                
                const result = await response.json();
                feedbackStatusEl.style.color = "#4ade80";
                feedbackStatusEl.textContent = `✓ ${result.message}`;
                
            } catch (error) {
                feedbackStatusEl.style.color = "#f87171";
                feedbackStatusEl.textContent = `Error: ${error.message}`;
            } finally {
                sendFeedbackBtn.disabled = false;
                sendFeedbackBtn.textContent = "Send Feedback";
            }
        };

        sendFeedbackBtn.addEventListener("click", sendFeedback);

        fetchRules();
    </script>
</body>
</html>
    """


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.get("/petra-logo.svg")
async def petra_logo():
    logo_path = Path("petra-logo.svg")
    if logo_path.exists():
        return Response(content=logo_path.read_bytes(), media_type="image/svg+xml")
    return Response(status_code=404)


@app.post("/validate")
async def api_validate(
    pdf: UploadFile = File(..., description="PDF file"),
    rules_json: Optional[str] = Form(None, description="Rules JSON as a string (optional). If omitted, uses rules/rules.json"),
):
    # Save upload with original filename (sanitized)
    tmp_dir = Path("data/uploads/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize original filename: keep only alphanumeric, dash, underscore
    original_name = Path(pdf.filename or "document").stem
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", original_name)
    # Add a short unique suffix to avoid collisions if same file uploaded twice
    unique_suffix = uuid.uuid4().hex[:8]
    pdf_path = tmp_dir / f"{safe_name}_{unique_suffix}.pdf"
    
    with open(pdf_path, "wb") as f:
        f.write(await pdf.read())

    try:
        data = _run_pipeline(pdf_path=str(pdf_path), rules_json_str=rules_json)
        return JSONResponse(content=data)
    finally:
        # best-effort cleanup
        try:
            pdf_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/feedback")
async def api_feedback(data: FeedbackRequest):
    """Append user feedback to the feedback log file."""
    feedback_dir = Path("data/feedback")
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / "feedback.jsonl"
    
    # Build the log entry with server timestamp
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "document_id": data.document_id,
        "items": [item.model_dump() for item in data.items],
    }
    
    # Append as a single JSON line
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    
    return {"status": "ok", "message": f"Logged {len(data.items)} feedback item(s)."}


if __name__ == "__main__":
    cli()
