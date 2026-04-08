"use strict";

let currentState = null;

// ── UTILITIES ───────────────────────────────────────────────────────────────

function setMessage(type, text) {
    const box = document.getElementById("result");
    box.className = `message-box ${type}`;
    box.innerHTML = text;
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderHints(hints) {
    const hintList = document.getElementById("hint-list");
    hintList.innerHTML = "";
    (hints || []).forEach((hint, i) => {
        const li = document.createElement("li");
        li.innerHTML = hint;
        li.style.animationDelay = `${i * 0.07}s`;
        hintList.appendChild(li);
    });
}

function updateProgress(progress, total) {
    const shown = Math.min(progress, total);
    const pct = Math.round((shown / total) * 100);
    document.getElementById("progress-text").textContent = `${shown} / ${total}`;
    document.getElementById("progress-percentage").textContent = `${pct}%`;
    document.getElementById("progress-fill").style.width = `${pct}%`;
}

function renderVaultFragments(fragments) {
    const target = document.getElementById("vault-fragments");
    if (!fragments || !fragments.length) {
        target.textContent = "None recovered yet";
        return;
    }
    target.innerHTML = fragments.map(f =>
        `<span class="fragment-chip">${escapeHtml(f)}</span>`
    ).join(" ");
}

function renderRecoveredEvidence(answers) {
    const target = document.getElementById("recovered-evidence");
    if (!answers || !Object.keys(answers).length) {
        target.textContent = "No evidence recovered yet.";
        return;
    }
    const labels = {
        phase_1: "Phase 1 — plaintext password",
        phase_2: "Phase 2 — breach details",
        phase_3: "Phase 3 — codename token",
        phase_4: "Phase 4 — vault code",
    };
    target.innerHTML = Object.entries(answers).map(([k, v]) =>
        `<div class="evidence-row">
           <span class="ev-label">${labels[k] || k}</span>
           <span class="ev-value">${escapeHtml(v)}</span>
         </div>`
    ).join("");
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function renderWrongCounter(count, phaseNum) {
    if (!count) return "";
    const danger = count >= 5 ? "counter-danger" : count >= 3 ? "counter-warn" : "";
    return `<div class="wrong-counter ${danger}">⚠ ${count} failed attempt${count !== 1 ? "s" : ""} on Phase ${phaseNum}</div>`;
}

// ── PHASE 1: SALTED SHA-256 CRACKER ─────────────────────────────────────────

function renderPhase1(state) {
    const p1 = state.phase1;
    const tested = p1.tested_candidates || [];

    // Build hash comparison table
    let tableBody;
    if (tested.length === 0) {
        tableBody = `<tr><td colspan="3" class="hash-cell muted-cell">
            No candidates tested — select from wordlist or type manually below.
        </td></tr>`;
    } else {
        tableBody = tested.map((c, idx) => {
            const isLast = idx === tested.length - 1;
            const isMatch = p1.match_found && isLast;
            return `<tr class="hash-row ${isMatch ? "hash-match" : ""}">
                <td class="hash-cell candidate-cell mono-sm">${escapeHtml(c)}</td>
                <td class="hash-cell hash-mono mono-xs">
                    ${isMatch
                        ? `<span class="match-badge">✓ MATCH</span>`
                        : `<span class="nomatch-badge">✗ mismatch</span>`
                    }
                </td>
                <td class="hash-cell mono-xs computed-hash-cell" id="computed-${idx}">
                    — (click Compute to reveal)
                </td>
            </tr>`;
        }).join("");
    }

    // Wordlist grid — paginated to 30 per page for readability
    const perPage = 30;
    const candidates = p1.candidates || [];
    const testedSet = new Set(tested);

    const wordlistItems = candidates.map(c => {
        const done = testedSet.has(c);
        const isMatchCand = p1.match_found && tested.includes(c) && tested[tested.length - 1] === c;
        return `<span
            class="wordlist-item ${done ? "tested" : ""} ${isMatchCand ? "matched" : ""}"
            onclick="quickTestCandidate('${escapeHtml(c)}')"
            title="${done ? "Already tested" : "Click to test"}"
        >${escapeHtml(c)}</span>`;
    }).join("");

    return `
    <!-- Leaked credential block -->
    <div class="brief-box">
        <div class="brief-label">RECOVERED CREDENTIAL DUMP — e.mercer</div>
        <div class="brief-text">
            <div class="cred-row">
                <span class="cred-key">Username</span>
                <span class="cred-val">${escapeHtml(p1.username)}</span>
            </div>
            <div class="cred-row">
                <span class="cred-key">Hash Algorithm</span>
                <span class="cred-val">${escapeHtml(p1.hash_type)}</span>
            </div>
            <div class="cred-row">
                <span class="cred-key">Config Comment</span>
                <span class="cred-val hint-amber">${escapeHtml(p1.salt_hint)}</span>
            </div>
            <div class="cred-row">
                <span class="cred-key">Target Hash</span>
                <span class="cred-val hash-mono hash-break">${escapeHtml(p1.hash)}</span>
            </div>
        </div>
    </div>

    <!-- Algorithm note -->
    <div class="brief-box algo-note">
        <div class="brief-label">HASH FORMULA</div>
        <div class="brief-text mono-sm">
            SHA-256( <span class="hint-amber">salt</span> + <span class="hint-green">candidate</span> ) → 64-char hex digest<br>
            The salt is prepended. Reverse engineering is computationally infeasible — use the wordlist.
        </div>
    </div>

    <!-- Wordlist -->
    <div class="brief-box">
        <div class="brief-label">WORDLIST — ${candidates.length} CANDIDATES
            <span class="tested-badge">${tested.length} tested</span>
        </div>
        <div class="wordlist-grid">${wordlistItems}</div>
    </div>

    <!-- Hash comparison table -->
    <div class="brief-box">
        <div class="brief-label">HASH COMPARISON LOG</div>
        <table class="hash-table">
            <thead>
                <tr>
                    <th>Candidate</th>
                    <th>Result</th>
                    <th>Computed Hash</th>
                </tr>
            </thead>
            <tbody id="hash-table-body">${tableBody}</tbody>
        </table>
    </div>

    <!-- Manual tester -->
    <div class="brief-box">
        <div class="brief-label">MANUAL CANDIDATE TESTER</div>
        <div class="tester-row">
            <input type="text" id="candidate-input" placeholder="Type candidate password..."
                   class="input-field mono-sm" onkeydown="if(event.key==='Enter') testCandidate()" />
            <button class="btn-action" onclick="testCandidate()">▶ Test Hash</button>
        </div>
        <div id="tester-output" class="tester-output hidden"></div>
    </div>

    ${renderWrongCounter(p1.wrong_submits, 1)}
    `;
}

async function testCandidate() {
    const input = document.getElementById("candidate-input");
    const candidate = input.value.trim();
    if (!candidate) {
        setMessage("error", "Enter a candidate password to test.");
        return;
    }

    const outDiv = document.getElementById("tester-output");
    outDiv.className = "tester-output";
    outDiv.innerHTML = `<span class="computing">⟳ Computing SHA-256(salt + "${escapeHtml(candidate)}")...</span>`;

    try {
        const res = await fetch("/phase1_test_candidate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate }),
        });
        const data = await res.json();

        if (!data.success) {
            outDiv.innerHTML = `<span class="error-text">${escapeHtml(data.message)}</span>`;
            return;
        }

        const matchClass = data.is_match ? "match-result" : "nomatch-result";
        outDiv.innerHTML = `
            <div class="${matchClass}">
                <div class="hash-line">
                    <span class="hl-label">Candidate:</span>
                    <span class="hl-value mono-sm">${escapeHtml(data.candidate)}</span>
                </div>
                <div class="hash-line">
                    <span class="hl-label">Computed:</span>
                    <span class="hl-value hash-mono mono-xs">${escapeHtml(data.candidate_hash)}</span>
                </div>
                <div class="hash-line">
                    <span class="hl-label">Target:</span>
                    <span class="hl-value hash-mono mono-xs">${escapeHtml(data.target_hash)}</span>
                </div>
                <div class="hash-verdict ${data.is_match ? 'verdict-match' : 'verdict-miss'}">
                    ${data.is_match ? "✓ HASH MATCH — credential confirmed" : "✗ Hash mismatch"}
                </div>
                <div class="attempt-count">Total tested: ${data.attempts_used}</div>
            </div>
        `;

        if (data.is_match) {
            setMessage("success", `Hash match confirmed for candidate. If this is correct, submit it above.`);
        }

        input.value = "";
        loadGameState(); // Refresh to update table
    } catch (err) {
        outDiv.innerHTML = `<span class="error-text">Network error — ${err.message}</span>`;
    }
}

async function quickTestCandidate(candidate) {
    document.getElementById("candidate-input").value = candidate;
    await testCandidate();
}

// ── PHASE 2: SIEM LOG ANALYSIS ───────────────────────────────────────────────

function renderPhase2(state) {
    const p2 = state.phase2;
    const rows = p2.rows || [];
    const selected = new Set(p2.selected_rows || []);

    const tableRows = rows.map(row => {
        const isSelected = selected.has(row.id);
        const isExternal = row.dept === "External";
        const isFailure = row.event === "LOGIN_FAILED";
        const isSuccess = row.event === "LOGIN_SUCCESS";
        const isDownload = row.event === "FILE_DOWNLOAD";

        let rowClass = "log-row";
        if (isSelected) rowClass += " log-selected";
        if (isExternal && !isSelected) rowClass += " log-external-hint";

        const eventClass = isFailure ? "event-fail"
            : isSuccess ? "event-success"
            : isDownload ? "event-download"
            : "event-neutral";

        return `<tr class="${rowClass}" onclick="toggleLogRow(${row.id})" title="Click to select/deselect">
            <td class="log-cell log-id">${row.id}</td>
            <td class="log-cell log-time mono-sm">${escapeHtml(row.time)}</td>
            <td class="log-cell log-user mono-sm">${escapeHtml(row.user)}</td>
            <td class="log-cell log-ip mono-sm">${escapeHtml(row.ip)}</td>
            <td class="log-cell log-event"><span class="event-badge ${eventClass}">${escapeHtml(row.event)}</span></td>
            <td class="log-cell log-resource mono-xs">${escapeHtml(row.resource)}</td>
            <td class="log-cell log-bytes">${row.bytes.toLocaleString()}</td>
            <td class="log-cell log-dept dept-${row.dept.toLowerCase()}">${escapeHtml(row.dept)}</td>
            <td class="log-cell log-select">${isSelected ? "✓" : ""}</td>
        </tr>`;
    }).join("");

    const selCount = selected.size;
    const analysisStatus = p2.analysis_unlocked
        ? `<div class="analysis-unlocked">✓ Breach sequence confirmed (${selCount} entries selected)</div>`
        : `<div class="analysis-pending">${selCount} entr${selCount !== 1 ? "ies" : "y"} selected — breach sequence not yet confirmed</div>`;

    return `
    <!-- Security bulletin — false positive notice -->
    <div class="brief-box bulletin-box">
        <div class="brief-label">⚠ SECURITY BULLETIN</div>
        <div class="brief-text bulletin-text">${escapeHtml(p2.bulletin)}</div>
    </div>

    <!-- Selection status -->
    <div class="brief-box">
        <div class="brief-label">BREACH SEQUENCE SELECTION</div>
        <div class="brief-text">
            ${analysisStatus}
            <div class="selection-hint">
                Click log entries to select them. Select only the rows comprising the breach sequence.<br>
                Correct selection unlocks the submit form.
            </div>
            <div class="legend-row">
                <span class="legend-item event-fail">LOGIN_FAILED</span>
                <span class="legend-item event-success">LOGIN_SUCCESS</span>
                <span class="legend-item event-download">FILE_DOWNLOAD</span>
                <span class="legend-item dept-external">External IP</span>
            </div>
        </div>
    </div>

    <!-- SIEM Log table -->
    <div class="brief-box siem-box">
        <div class="brief-label">SIEM LOG — ${rows.length} ENTRIES (WINDOW: 00:00 – 04:00)</div>
        <div class="table-scroll">
            <table class="siem-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>TIME</th>
                        <th>USER</th>
                        <th>SOURCE IP</th>
                        <th>EVENT</th>
                        <th>RESOURCE</th>
                        <th>BYTES</th>
                        <th>SCOPE</th>
                        <th>SEL</th>
                    </tr>
                </thead>
                <tbody>${tableRows}</tbody>
            </table>
        </div>
    </div>

    ${renderWrongCounter(p2.wrong_submits, 2)}
    `;
}

async function toggleLogRow(rowId) {
    try {
        const res = await fetch("/phase2_toggle_row", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ row_id: rowId }),
        });
        const data = await res.json();

        if (data.message) {
            const msgType = data.analysis_unlocked ? "success" : "info";
            setMessage(msgType, data.message);
        }

        loadGameState();
    } catch (err) {
        setMessage("error", `Request failed: ${err.message}`);
    }
}

// ── PHASE 3: MULTI-LAYER DECODER ─────────────────────────────────────────────

function renderPhase3(state) {
    const p3 = state.phase3;
    const attempts = p3.decode_attempts || [];
    const layers = p3.layers_completed || 0;

    const layerStatus = [
        `<div class="layer-status ${layers >= 1 ? 'layer-done' : 'layer-pending'}">
            ${layers >= 1 ? "✓" : "○"} Layer 1 — Outer encoding
        </div>`,
        `<div class="layer-status ${layers >= 2 ? 'layer-done' : 'layer-pending'}">
            ${layers >= 2 ? "✓" : "○"} Layer 2 — Inner cipher
        </div>`,
    ].join("");

    // Build attempt history
    const attemptRows = attempts.length === 0
        ? `<div class="no-attempts">No decode attempts yet. Use the tools below.</div>`
        : attempts.map((a, i) => `
            <div class="attempt-entry ${a.is_correct_method ? 'attempt-good' : 'attempt-bad'}">
                <div class="attempt-header">
                    <span class="attempt-num">#${i + 1}</span>
                    <span class="attempt-method">${escapeHtml(a.method.toUpperCase())}</span>
                    <span class="attempt-time">${escapeHtml(a.timestamp || "")}</span>
                    ${a.input_preview ? `<span class="attempt-input">input: ${escapeHtml(a.input_preview)}</span>` : ""}
                </div>
                <div class="attempt-output mono-xs">${escapeHtml(a.output.substring(0, 300))}${a.output.length > 300 ? "..." : ""}</div>
                ${a.layer_info ? `<div class="attempt-layer-info">${escapeHtml(a.layer_info)}</div>` : ""}
            </div>
        `).join("");

    return `
    <!-- Intercepted transmission -->
    <div class="brief-box">
        <div class="brief-label">INTERCEPTED TRANSMISSION</div>
        <div class="brief-text">
            <div class="encoded-blob mono-xs">${escapeHtml(p3.encoded)}</div>
            <div class="blob-meta">Length: ${p3.encoded.length} chars | Charset: A-Z a-z 0-9 +/= (Base64 alphabet)</div>
        </div>
    </div>

    <!-- Layer progress tracker -->
    <div class="brief-box">
        <div class="brief-label">ENCODING LAYER TRACKER</div>
        <div class="brief-text">${layerStatus}
            <div class="layer-hint">Two encoding layers must be removed in sequence.</div>
        </div>
    </div>

    <!-- Decoding tools -->
    <div class="brief-box">
        <div class="brief-label">DECODE TOOLKIT</div>
        <div class="brief-text">
            <div class="tool-note">
                Apply tools to the original transmission OR paste intermediate output to chain decode steps.
            </div>
            <div class="tool-input-row">
                <textarea id="decode-input"
                    placeholder="Leave empty to decode the original transmission. Paste intermediate output here to chain."
                    class="decode-textarea mono-xs" rows="3"></textarea>
            </div>
            <div class="tool-buttons">
                <button class="btn-tool" onclick="runDecoder('base64')" title="Base64 decode">⟳ Base64 Decode</button>
                <button class="btn-tool" onclick="runDecoder('rot13')"  title="ROT13 substitution">⟳ ROT13</button>
                <button class="btn-tool" onclick="runDecoder('caesar3')" title="Caesar shift -3">⟳ Caesar-3</button>
                <button class="btn-tool" onclick="runDecoder('hex')"    title="Hex decode">⟳ Hex Decode</button>
                <button class="btn-tool" onclick="runDecoder('url')"    title="URL decode">⟳ URL Decode</button>
            </div>
            <div id="decoder-live-output" class="decoder-live hidden"></div>
        </div>
    </div>

    <!-- Attempt history -->
    <div class="brief-box">
        <div class="brief-label">DECODE ATTEMPT HISTORY (${attempts.length})</div>
        <div class="attempt-history">${attemptRows}</div>
    </div>

    ${renderWrongCounter(p3.wrong_submits, 3)}
    `;
}

async function runDecoder(method) {
    const inputEl = document.getElementById("decode-input");
    const inputText = inputEl ? inputEl.value.trim() : "";
    const liveOut = document.getElementById("decoder-live-output");

    liveOut.className = "decoder-live";
    liveOut.innerHTML = `<span class="computing">⟳ Applying ${method.toUpperCase()}...</span>`;

    try {
        const res = await fetch("/phase3_decode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ method, input_text: inputText || null }),
        });
        const data = await res.json();

        const resultClass = data.is_correct_method ? "decode-correct" : "decode-incorrect";
        liveOut.innerHTML = `
            <div class="${resultClass}">
                <div class="decode-method-label">${method.toUpperCase()} result:</div>
                <div class="decode-output-text mono-xs">${escapeHtml(data.output)}</div>
                ${data.layer_info ? `<div class="decode-layer-info">${escapeHtml(data.layer_info)}</div>` : ""}
                <button class="btn-mini" onclick="copyToDecodeInput('${escapeHtml(data.output).replace(/'/g, "\\'")}')">
                    ↓ Use as input for next step
                </button>
            </div>
        `;

        if (data.layers_completed >= 2) {
            setMessage("success", "Transmission fully decoded. Extract the codename and submit.");
        }

        loadGameState();
    } catch (err) {
        liveOut.innerHTML = `<span class="error-text">Error: ${err.message}</span>`;
    }
}

function copyToDecodeInput(text) {
    const el = document.getElementById("decode-input");
    if (el) {
        el.value = text;
        el.focus();
        setMessage("info", "Output copied to input field. Apply next decode step.");
    }
}

// ── PHASE 4: VAULT SYNTHESIS ─────────────────────────────────────────────────

function renderPhase4(state) {
    const fragments = state.vault_fragments || [];
    const answers = state.phase_answers || {};
    const p4 = state.phase4 || {};

    const phase1pwd = answers.phase_1 || "—";
    const phase2details = answers.phase_2 || "—";
    const phase3token = answers.phase_3 || "—";

    const fragDisplay = fragments.length
        ? fragments.map(f => `<span class="fragment-large">${escapeHtml(f)}</span>`).join("")
        : `<span class="muted-text">No fragments recovered</span>`;

    return `
    <!-- Recovered intelligence summary -->
    <div class="brief-box">
        <div class="brief-label">OPERATION INTELLIGENCE SUMMARY</div>
        <div class="brief-text">
            <div class="intel-row">
                <span class="intel-key">Phase 1 — Recovered password:</span>
                <span class="intel-val mono-sm hint-green">${escapeHtml(phase1pwd)}</span>
            </div>
            <div class="intel-row">
                <span class="intel-key">Phase 2 — Breach details:</span>
                <span class="intel-val mono-sm hint-amber">${escapeHtml(phase2details)}</span>
            </div>
            <div class="intel-row">
                <span class="intel-key">Phase 3 — Codename:</span>
                <span class="intel-val mono-sm hint-blue">${escapeHtml(phase3token)}</span>
            </div>
        </div>
    </div>

    <!-- Vault fragments -->
    <div class="brief-box">
        <div class="brief-label">VAULT FRAGMENTS (in phase order)</div>
        <div class="fragment-display">${fragDisplay}</div>
    </div>

    <!-- Synthesis formula -->
    <div class="brief-box formula-box">
        <div class="brief-label">SYNTHESIS FORMULA</div>
        <div class="brief-text formula-text mono-sm">
            <div class="formula-step">
                <span class="step-num">1.</span> Concatenate fragments: 
                <span class="hint-green">Fragment₁ + Fragment₂ + Fragment₃</span>
            </div>
            <div class="formula-step">
                <span class="step-num">2.</span> Append: 
                <span class="hint-amber">character count of Phase 1 plaintext password</span>
            </div>
            <div class="formula-step">
                <span class="step-num">3.</span> Append: 
                <span class="hint-blue">count of unique attacker IPs confirmed in Phase 2</span>
            </div>
            <div class="formula-step formula-step-final">
                <span class="step-num">4.</span> 
                <span class="hint-red">REVERSE the entire assembled numeric string</span>
            </div>
            <div class="formula-example">
                Example (not actual values): fragments "1","2","3" + pwLen=8 + ipCount=2 
                → "12382" → reversed → <strong>"28321"</strong>
            </div>
        </div>
    </div>

    ${renderWrongCounter(p4.wrong_submits, 4)}
    `;
}

// ── MAIN GAME LOADER ─────────────────────────────────────────────────────────

async function loadGameState() {
    try {
        const res = await fetch("/get_game_state");
        const state = await res.json();
        currentState = state;

        updateProgress(state.progress, state.total);
        renderVaultFragments(state.vault_fragments);
        renderRecoveredEvidence(state.phase_answers);
        renderHints(state.hints || []);

        document.getElementById("phase-title").innerHTML = state.title || "";
        document.getElementById("phase-description").innerHTML = state.description || "";
        document.getElementById("phase-objective").textContent = state.objective || "";
        document.getElementById("phase-task-brief").innerHTML = state.task_brief || "";
        document.getElementById("answer-label").textContent = state.answer_label || "";

        const phaseUI = document.getElementById("phase-ui");

        // Lockout warning banner
        const lockoutBanner = document.getElementById("lockout-banner");
        if (lockoutBanner) {
            lockoutBanner.style.display = state.lockout_warned ? "block" : "none";
        }

        if (state.completed) {
            phaseUI.innerHTML = `
                <div class="vault-open-screen">
                    <div class="vault-icon">🏦</div>
                    <h2 class="vault-title">VAULT OPENED</h2>
                    <p class="vault-sub">All four security layers successfully breached.</p>
                    <div class="debrief-block">
                        ${(state.hints || []).map(h => `<div class="debrief-line">${escapeHtml(h)}</div>`).join("")}
                    </div>
                    <button class="btn-reset-final" onclick="resetGame()">↺ Run Again</button>
                </div>`;
            document.getElementById("answer-form").style.display = "none";
            return;
        }

        document.getElementById("answer-form").style.display = "block";
        document.getElementById("answer-input").value = "";

        // Render phase-specific UI
        const p = state.progress;
        if (p === 1) {
            phaseUI.innerHTML = renderPhase1(state);
        } else if (p === 2) {
            phaseUI.innerHTML = renderPhase2(state);
        } else if (p === 3) {
            phaseUI.innerHTML = renderPhase3(state);
        } else if (p === 4) {
            phaseUI.innerHTML = renderPhase4(state);
        } else {
            phaseUI.innerHTML = "";
        }

    } catch (err) {
        console.error("loadGameState error:", err);
        setMessage("error", `State load failed: ${err.message}. Try refreshing.`);
    }
}

// ── ANSWER SUBMISSION ─────────────────────────────────────────────────────────

async function submitAnswer() {
    const input = document.getElementById("answer-input");
    const answer = input.value.trim();

    if (!answer) {
        setMessage("error", "Enter an answer before submitting.");
        return;
    }

    const btn = document.getElementById("submit-btn");
    btn.disabled = true;
    btn.textContent = "Verifying...";

    try {
        const res = await fetch("/submit_answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answer }),
        });
        const data = await res.json();

        if (data.success) {
            if (data.completed) {
                setMessage("success", `🔓 ${data.message}`);
            } else {
                setMessage("success", data.message);
            }
            input.value = "";
            loadGameState();
        } else {
            const penaltyClass = data.penalty ? "penalty" : "error";
            setMessage(penaltyClass, data.message || "Incorrect answer.");
        }
    } catch (err) {
        setMessage("error", `Submission failed: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.textContent = "Submit";
    }
}

async function resetGame() {
    if (!confirm("Reset the game? All progress will be lost.")) return;
    await fetch("/reset", { method: "POST" });
    setMessage("info", "Session reset. Starting from Phase 1.");
    loadGameState();
}

// ── HINT TOGGLE ───────────────────────────────────────────────────────────────

function toggleHints() {
    const panel = document.getElementById("hint-panel");
    const btn = document.getElementById("hint-toggle-btn");
    const isHidden = panel.style.display === "none" || !panel.style.display;
    panel.style.display = isHidden ? "block" : "none";
    btn.textContent = isHidden ? "▲ Hide Intel" : "▼ View Intel (Hints)";
}

// ── KEYBOARD SHORTCUTS ────────────────────────────────────────────────────────

document.addEventListener("keydown", e => {
    if (e.key === "Enter" && document.activeElement.id === "answer-input") {
        submitAnswer();
    }
});

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", loadGameState);