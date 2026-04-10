"use strict";
let currentState = null;

// ── UTILITIES ────────────────────────────────────────────────────────────────

function setMessage(type, text) {
    const box = document.getElementById("result");
    box.className = `message-box ${type}`;
    box.innerHTML = text;
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderHints(hints) {
    const list = document.getElementById("hint-list");
    list.innerHTML = "";
    (hints || []).forEach((h, i) => {
        const li = document.createElement("li");
        li.innerHTML = h;
        li.style.animationDelay = `${i * 0.07}s`;
        list.appendChild(li);
    });
}

function updateProgress(progress, total) {
    const pct = Math.round((Math.min(progress, total) / total) * 100);
    document.getElementById("progress-text").textContent = `${Math.min(progress, total)} / ${total}`;
    document.getElementById("progress-percentage").textContent = `${pct}%`;
    document.getElementById("progress-fill").style.width = `${pct}%`;
}

function renderVaultFragments(frags) {
    const el = document.getElementById("vault-fragments");
    if (!frags || !frags.length) { el.textContent = "None recovered yet"; return; }
    el.innerHTML = frags.map(f => `<span class="fragment-chip">${escapeHtml(f)}</span>`).join(" ");
}

function renderRecoveredEvidence(answers) {
    const el = document.getElementById("recovered-evidence");
    if (!answers || !Object.keys(answers).length) {
        el.textContent = "No evidence recovered yet."; return;
    }
    const labels = {
        phase_1: "Phase 1 — password",
        phase_2: "Phase 2 — breach",
        phase_3: "Phase 3 — codename",
        phase_4: "Phase 4 — vault code",
    };
    el.innerHTML = Object.entries(answers).map(([k, v]) =>
        `<div class="evidence-row">
           <span class="ev-label">${labels[k] || k}</span>
           <span class="ev-value">${escapeHtml(v)}</span>
         </div>`
    ).join("");
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function wrongCounter(count, phase) {
    if (!count) return "";
    const cls = count >= 5 ? "counter-danger" : count >= 3 ? "counter-warn" : "";
    return `<div class="wrong-counter ${cls}">⚠ ${count} failed attempt${count !== 1 ? "s" : ""} on Phase ${phase}</div>`;
}


// ── PHASE 1: SALTED SHA-256 ──────────────────────────────────────────────────

function renderPhase1(state) {
    const p1 = state.phase1;
    const tested = p1.tested_candidates || [];
    const testedSet = new Set(tested);

    // Hash comparison table
    let tbody;
    if (!tested.length) {
        tbody = `<tr><td colspan="3" class="hash-cell muted-cell">
            No candidates tested — select from the wordlist or type below.
        </td></tr>`;
    } else {
        tbody = tested.map((c, i) => {
            const isLast  = i === tested.length - 1;
            const isMatch = p1.match_found && isLast;
            return `<tr class="hash-row ${isMatch ? "hash-match" : ""}">
                <td class="hash-cell candidate-cell mono-sm">${escapeHtml(c)}</td>
                <td class="hash-cell">
                    ${isMatch
                        ? '<span class="match-badge">✓ MATCH</span>'
                        : '<span class="nomatch-badge">✗</span>'}
                </td>
                <td class="hash-cell hash-mono mono-xs computed-col" id="hc-${i}">—</td>
            </tr>`;
        }).join("");
    }

    // Wordlist grid
    const wordlistHtml = (p1.candidates || []).map(c => {
        const done = testedSet.has(c);
        const matched = p1.match_found && tested[tested.length - 1] === c && done;
        return `<span class="wordlist-item ${done ? "tested" : ""} ${matched ? "matched" : ""}"
                    onclick="quickTest('${escapeHtml(c).replace(/'/g, "\\'")}')"
                    title="${done ? "Tested" : "Click to test"}">${escapeHtml(c)}</span>`;
    }).join("");

    return `
    <div class="brief-box">
        <div class="brief-label">RECOVERED CREDENTIAL DUMP — e.mercer</div>
        <div class="brief-text">
            <div class="cred-row"><span class="cred-key">Username</span><span class="cred-val">${escapeHtml(p1.username)}</span></div>
            <div class="cred-row"><span class="cred-key">Hash type</span><span class="cred-val">${escapeHtml(p1.hash_type)}</span></div>
            <div class="cred-row"><span class="cred-key">Config comment</span><span class="cred-val hint-amber mono-sm">${escapeHtml(p1.salt_hint)}</span></div>
            <div class="cred-row"><span class="cred-key">Target hash</span><span class="cred-val hash-mono hash-break">${escapeHtml(p1.hash)}</span></div>
        </div>
    </div>
    <div class="brief-box algo-note">
        <div class="brief-label">HASH FORMULA</div>
        <div class="brief-text mono-sm">
            SHA-256( <span class="hint-amber">salt</span> + <span class="hint-green">candidate</span> )
            → 64-character hex digest
        </div>
    </div>
    <div class="brief-box">
        <div class="brief-label">WORDLIST — ${(p1.candidates || []).length} CANDIDATES
            <span class="tested-badge">${tested.length} tested</span>
        </div>
        <div class="wordlist-grid">${wordlistHtml}</div>
    </div>
    <div class="brief-box">
        <div class="brief-label">HASH COMPARISON LOG</div>
        <table class="hash-table">
            <thead><tr><th>Candidate</th><th>Result</th><th>Computed Hash</th></tr></thead>
            <tbody id="hash-tbody">${tbody}</tbody>
        </table>
    </div>
    <div class="brief-box">
        <div class="brief-label">MANUAL TESTER</div>
        <div class="tester-row">
            <input type="text" id="cand-input" class="input-field mono-sm"
                placeholder="Type candidate password…"
                onkeydown="if(event.key==='Enter') testCandidate()" />
            <button class="btn-action" onclick="testCandidate()">▶ Test</button>
        </div>
        <div id="tester-out" class="tester-output hidden"></div>
    </div>
    ${wrongCounter(p1.wrong_submits, 1)}`;
}

async function testCandidate() {
    const inp = document.getElementById("cand-input");
    const candidate = inp.value.trim();
    if (!candidate) { setMessage("error", "Enter a candidate to test."); return; }

    const out = document.getElementById("tester-out");
    out.className = "tester-output";
    out.innerHTML = `<span class="computing">⟳ Computing SHA-256(salt + "${escapeHtml(candidate)}")…</span>`;

    try {
        const res  = await fetch("/phase1_test_candidate", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ candidate }),
        });
        const data = await res.json();
        if (!data.success) { out.innerHTML = `<span class="error-text">${escapeHtml(data.message)}</span>`; return; }

        const cls = data.is_match ? "match-result" : "nomatch-result";
        out.innerHTML = `
            <div class="${cls}">
                <div class="hash-line"><span class="hl-label">Candidate:</span><span class="hl-value mono-sm">${escapeHtml(data.candidate)}</span></div>
                <div class="hash-line"><span class="hl-label">Computed: </span><span class="hl-value hash-mono mono-xs">${escapeHtml(data.computed_hash)}</span></div>
                <div class="hash-line"><span class="hl-label">Target:   </span><span class="hl-value hash-mono mono-xs">${escapeHtml(data.target_hash)}</span></div>
                <div class="hash-verdict ${data.is_match ? "verdict-match" : "verdict-miss"}">
                    ${data.is_match ? "✓ HASH MATCH" : "✗ No match"}
                </div>
                <div class="attempt-count">Tested: ${data.attempts_used}</div>
            </div>`;
        if (data.is_match) setMessage("success", "Hash match confirmed. Submit the plaintext password above.");
        inp.value = "";
        loadGameState();
    } catch (e) { out.innerHTML = `<span class="error-text">${e.message}</span>`; }
}

async function quickTest(candidate) {
    document.getElementById("cand-input").value = candidate;
    await testCandidate();
}


// ── PHASE 2: SIEM LOG ANALYSIS ───────────────────────────────────────────────
// Design intent: present the data for comparison — do not pre-label actors.
// The behaviour-comparison panel surfaces the timing and byte data side-by-side
// so students must draw the conclusion themselves.

function renderPhase2(state) {
    const p2  = state.phase2;
    const sel = new Set(p2.selected_rows || []);

    const rows = (p2.rows || []).map(row => {
        const isSel  = sel.has(row.id);
        const evtCls = {
            LOGIN_FAILED:  "event-fail",
            LOGIN_SUCCESS: "event-success",
            FILE_DOWNLOAD: "event-download",
            LOGOUT:        "event-logout",
        }[row.event] || "event-neutral";

        return `<tr class="log-row ${isSel ? "log-selected" : ""}"
                    onclick="toggleRow(${row.id})" title="Click to select/deselect">
            <td class="log-cell log-id">${row.id}</td>
            <td class="log-cell log-time mono-sm">${escapeHtml(row.time)}</td>
            <td class="log-cell log-user mono-sm">${escapeHtml(row.user)}</td>
            <td class="log-cell log-ip mono-sm">${escapeHtml(row.ip)}</td>
            <td class="log-cell"><span class="event-badge ${evtCls}">${escapeHtml(row.event)}</span></td>
            <td class="log-cell log-resource mono-xs">${escapeHtml(row.resource)}</td>
            <td class="log-cell log-bytes">${row.bytes.toLocaleString()}</td>
            <td class="log-cell dept-${row.dept.toLowerCase()} mono-xs">${escapeHtml(row.dept)}</td>
            <td class="log-cell log-sel">${isSel ? "✓" : ""}</td>
        </tr>`;
    }).join("");

    const selStatus = p2.analysis_unlocked
        ? `<div class="analysis-unlocked">✓ Breach sequence confirmed (${sel.size} rows)</div>`
        : `<div class="analysis-pending">${sel.size} row${sel.size !== 1 ? "s" : ""} selected</div>`;

    // Behaviour comparison panel — presents raw data, no labels
    const comparisonTable = `
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Indicator</th>
                <th>p.walsh / 185.92.73.18</th>
                <th>c.dreyfus / 91.108.4.77</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="cmp-label">Login endpoint</td>
                <td class="mono-xs">/portal/login</td>
                <td class="mono-xs">/vault/auth</td>
            </tr>
            <tr>
                <td class="cmp-label">Failure count</td>
                <td>3</td>
                <td>6</td>
            </tr>
            <tr>
                <td class="cmp-label">Failure interval</td>
                <td>12 s, 18 s, 18 s</td>
                <td>4 s, 4 s, 4 s, 3 s, 5 s</td>
            </tr>
            <tr>
                <td class="cmp-label">First resource after login</td>
                <td class="mono-xs">/reports/public</td>
                <td class="mono-xs">/vault/manifest</td>
            </tr>
            <tr>
                <td class="cmp-label">Post-login byte total</td>
                <td>3,400 B</td>
                <td>133,320 B</td>
            </tr>
            <tr>
                <td class="cmp-label">Time from login → first download</td>
                <td>18 s</td>
                <td>3 s</td>
            </tr>
            <tr>
                <td class="cmp-label">Sensitive resource access</td>
                <td>None</td>
                <td>/vault/keys.enc</td>
            </tr>
            <tr>
                <td class="cmp-label">Session end</td>
                <td>LOGOUT event</td>
                <td>No LOGOUT</td>
            </tr>
        </tbody>
    </table>`;

    return `
    <div class="brief-box bulletin-box">
        <div class="brief-label">⚠ SECURITY BULLETIN</div>
        <div class="brief-text bulletin-text">${escapeHtml(p2.bulletin)}</div>
    </div>
    <div class="brief-box">
        <div class="brief-label">EXTERNAL ACTOR COMPARISON</div>
        <div class="brief-text comparison-note">
            Two undocumented external sessions triggered alerts during this window.
            The table below aggregates their observable behaviour.
            Draw your conclusion from the data.
        </div>
        ${comparisonTable}
    </div>
    <div class="brief-box">
        <div class="brief-label">BREACH SEQUENCE SELECTION</div>
        <div class="brief-text">
            ${selStatus}
            <div class="selection-hint">
                Click log entries to mark them as part of the breach sequence.
                Select only the rows that constitute the actual intrusion.
            </div>
            <div class="legend-row">
                <span class="legend-item event-fail">FAILED</span>
                <span class="legend-item event-success">SUCCESS</span>
                <span class="legend-item event-download">DOWNLOAD</span>
                <span class="legend-item dept-external">External IP</span>
            </div>
        </div>
    </div>
    <div class="brief-box siem-box">
        <div class="brief-label">SIEM LOG — ${(p2.rows || []).length} ENTRIES</div>
        <div class="table-scroll">
            <table class="siem-table">
                <thead><tr>
                    <th>#</th><th>TIME</th><th>USER</th><th>SOURCE IP</th>
                    <th>EVENT</th><th>RESOURCE</th><th>BYTES</th><th>SCOPE</th><th>SEL</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    </div>
    ${wrongCounter(p2.wrong_submits, 2)}`;
}

async function toggleRow(id) {
    try {
        const res  = await fetch("/phase2_toggle_row", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ row_id: id }),
        });
        const data = await res.json();
        if (data.message) setMessage(data.analysis_unlocked ? "success" : "info", data.message);
        loadGameState();
    } catch (e) { setMessage("error", e.message); }
}


// ── PHASE 3: DECODE TOOL ─────────────────────────────────────────────────────
// Design intent: tool returns raw output only, no correct/incorrect labelling.
// Students read the output and chain steps manually.
// The layer tracker is shown but not explained — it confirms work done,
// not what to do next.

function renderPhase3(state) {
    const p3      = state.phase3;
    const layers  = p3.layers_completed || 0;
    const attempts = p3.decode_attempts || [];

    const layerDots = [1, 2].map(n =>
        `<span class="layer-dot ${layers >= n ? "layer-done" : ""}">${layers >= n ? "✓" : "○"} Layer ${n}</span>`
    ).join("");

    const historyHtml = attempts.length === 0
        ? `<div class="no-attempts">No decode attempts yet.</div>`
        : attempts.slice().reverse().map((a, i) => `
            <div class="attempt-entry">
                <div class="attempt-header">
                    <span class="attempt-num">#${attempts.length - i}</span>
                    <span class="attempt-method">${escapeHtml(a.method.toUpperCase())}</span>
                    <span class="attempt-time">${escapeHtml(a.timestamp || "")}</span>
                    ${a.input_preview ? `<span class="attempt-input-tag">from: ${escapeHtml(a.input_preview)}</span>` : ""}
                </div>
                <div class="attempt-output mono-xs">${escapeHtml(a.output.substring(0, 400))}${a.output.length > 400 ? "…" : ""}</div>
                ${a.note ? `<div class="attempt-note">${escapeHtml(a.note)}</div>` : ""}
            </div>`
        ).join("");

    return `
    <div class="brief-box">
        <div class="brief-label">INTERCEPTED TRANSMISSION</div>
        <div class="brief-text">
            <div class="encoded-blob mono-xs">${escapeHtml(p3.encoded)}</div>
            <div class="blob-meta">Length: ${p3.encoded.length} chars</div>
        </div>
    </div>
    <div class="brief-box">
        <div class="brief-label">DECODE PROGRESS</div>
        <div class="brief-text layer-tracker">${layerDots}
            <span class="layer-note">Two layers to remove. Work from outer to inner.</span>
        </div>
    </div>
    <div class="brief-box">
        <div class="brief-label">DECODE TOOLKIT</div>
        <div class="brief-text">
            <div class="tool-chain-note">
                To chain steps: apply a tool, then paste the output into the input field
                and apply the next tool. Leave the field empty to operate on the
                original transmitted blob.
            </div>
            <textarea id="decode-input" class="decode-textarea mono-xs" rows="3"
                placeholder="Leave empty to decode the original blob. Paste intermediate output here to continue."></textarea>
            <div class="tool-buttons">
                <button class="btn-tool" onclick="runDecode('base64')">Base64</button>
                <button class="btn-tool" onclick="runDecode('rot13')">ROT13</button>
                <button class="btn-tool" onclick="runDecode('caesar3')">Caesar-3</button>
                <button class="btn-tool" onclick="runDecode('hex')">Hex</button>
                <button class="btn-tool" onclick="runDecode('url')">URL</button>
            </div>
            <div id="decode-live" class="decoder-live hidden"></div>
        </div>
    </div>
    <div class="brief-box">
        <div class="brief-label">ATTEMPT HISTORY (newest first)</div>
        <div class="attempt-history">${historyHtml}</div>
    </div>
    ${wrongCounter(p3.wrong_submits, 3)}`;
}

async function runDecode(method) {
    const inputEl = document.getElementById("decode-input");
    const inputText = inputEl ? inputEl.value.trim() : "";
    const live = document.getElementById("decode-live");
    live.className = "decoder-live";
    live.innerHTML = `<span class="computing">⟳ Applying ${escapeHtml(method)}…</span>`;

    try {
        const res  = await fetch("/phase3_decode", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ method, input_text: inputText || null }),
        });
        const data = await res.json();

        live.innerHTML = `
            <div class="decode-result-block">
                <div class="decode-method-label">${escapeHtml(method.toUpperCase())} output:</div>
                <div class="decode-output-text mono-xs">${escapeHtml(data.output)}</div>
                ${data.note ? `<div class="decode-note">${escapeHtml(data.note)}</div>` : ""}
                <button class="btn-use-output" onclick="useAsInput(${JSON.stringify(data.output)})">
                    ↓ Use as input for next step
                </button>
            </div>`;

        loadGameState();
    } catch (e) {
        live.innerHTML = `<span class="error-text">${e.message}</span>`;
    }
}

function useAsInput(text) {
    const el = document.getElementById("decode-input");
    if (el) { el.value = text; el.focus(); }
}


// ── PHASE 4: VLT-7 VAULT SYNTHESIS ──────────────────────────────────────────

function renderPhase4(state) {
    const frags   = state.vault_fragments || [];
    const answers = state.phase_answers  || {};
    const p4      = state.phase4         || {};

    const fragDisplay = frags.length
        ? frags.map(f => `<span class="fragment-large">${escapeHtml(f)}</span>`).join("")
        : `<span class="muted-text">No fragments recovered</span>`;

    return `
    <div class="brief-box">
        <div class="brief-label">RECOVERED OPERATION DATA</div>
        <div class="brief-text">
            <div class="intel-row">
                <span class="intel-key">Phase 1 — password recovered:</span>
                <span class="intel-val mono-sm hint-green">${escapeHtml(answers.phase_1 || "—")}</span>
            </div>
            <div class="intel-row">
                <span class="intel-key">Phase 2 — confirmed breach:</span>
                <span class="intel-val mono-sm hint-amber">${escapeHtml(answers.phase_2 || "—")}</span>
            </div>
            <div class="intel-row">
                <span class="intel-key">Phase 3 — codename:</span>
                <span class="intel-val mono-sm hint-blue">${escapeHtml(answers.phase_3 || "—")}</span>
            </div>
        </div>
    </div>
    <div class="brief-box">
        <div class="brief-label">VAULT FRAGMENTS (phase order)</div>
        <div class="fragment-display">${fragDisplay}</div>
    </div>
    <div class="brief-box formula-box">
        <div class="brief-label">VLT-7 ASSEMBLY PROTOCOL</div>
        <div class="brief-text formula-text mono-sm">
            <div class="vlt-intro">
                Vault firmware protocol VLT-7 requires a reflected-entry sequence.
                Assemble the code, then reverse it before submission.
            </div>
            <div class="formula-step"><span class="step-num">1.</span>
                Concatenate vault fragments in phase order:
                <span class="hint-green">Fragment₁ + Fragment₂ + Fragment₃</span>
            </div>
            <div class="formula-step"><span class="step-num">2.</span>
                Append character count of the Phase 1 plaintext password.
            </div>
            <div class="formula-step"><span class="step-num">3.</span>
                Append count of unique malicious IPs confirmed in Phase 2.
            </div>
            <div class="formula-step formula-step-final"><span class="step-num">4.</span>
                <span class="hint-red">VLT-7 reflection: reverse the complete digit string.</span>
            </div>
            <div class="formula-example">
                Example: fragments "1","2","3" + pwLen=8 + ipCount=2 → "12382" → reversed → "28321"
            </div>
        </div>
    </div>
    ${wrongCounter(p4.wrong_submits, 4)}`;
}


// ── MAIN LOADER ───────────────────────────────────────────────────────────────

async function loadGameState() {
    try {
        const res   = await fetch("/get_game_state");
        const state = await res.json();
        currentState = state;

        updateProgress(state.progress, state.total);
        renderVaultFragments(state.vault_fragments);
        renderRecoveredEvidence(state.phase_answers);
        renderHints(state.hints || []);

        document.getElementById("phase-title").innerHTML       = state.title || "";
        document.getElementById("phase-description").innerHTML  = state.description || "";
        document.getElementById("phase-objective").textContent  = state.objective || "";
        document.getElementById("phase-task-brief").innerHTML   = state.task_brief || "";
        document.getElementById("answer-label").textContent     = state.answer_label || "";

        const banner = document.getElementById("lockout-banner");
        if (banner) banner.style.display = state.lockout_warned ? "block" : "none";

        const phaseUI  = document.getElementById("phase-ui");
        const answerFm = document.getElementById("answer-form");

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
            answerFm.style.display = "none";
            return;
        }

        answerFm.style.display = "block";
        document.getElementById("answer-input").value = "";

        const p = state.progress;
        if      (p === 1) phaseUI.innerHTML = renderPhase1(state);
        else if (p === 2) phaseUI.innerHTML = renderPhase2(state);
        else if (p === 3) phaseUI.innerHTML = renderPhase3(state);
        else if (p === 4) phaseUI.innerHTML = renderPhase4(state);
        else              phaseUI.innerHTML = "";

    } catch (e) {
        console.error("loadGameState:", e);
        setMessage("error", `State load failed: ${e.message}`);
    }
}


// ── SUBMIT ────────────────────────────────────────────────────────────────────

async function submitAnswer() {
    const input  = document.getElementById("answer-input");
    const answer = input.value.trim();
    if (!answer) { setMessage("error", "Enter an answer before submitting."); return; }

    const btn = document.getElementById("submit-btn");
    btn.disabled = true; btn.textContent = "Verifying…";

    try {
        const res  = await fetch("/submit_answer", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answer }),
        });
        const data = await res.json();

        if (data.success) {
            setMessage("success", data.message);
            input.value = "";
            loadGameState();
        } else {
            setMessage(data.penalty ? "penalty" : "error", data.message || "Incorrect.");
        }
    } catch (e) {
        setMessage("error", `Submission error: ${e.message}`);
    } finally {
        btn.disabled = false; btn.textContent = "Submit";
    }
}

async function resetGame() {
    if (!confirm("Reset all progress?")) return;
    await fetch("/reset", { method: "POST" });
    setMessage("info", "Session reset. Starting from Phase 1.");
    loadGameState();
}

function toggleHints() {
    const panel = document.getElementById("hint-panel");
    const btn   = document.getElementById("hint-toggle-btn");
    const show  = panel.style.display === "none" || !panel.style.display;
    panel.style.display = show ? "block" : "none";
    btn.textContent     = show ? "▲ Hide Intel" : "▼ View Intel (Hints)";
}

document.addEventListener("keydown", e => {
    if (e.key === "Enter" && document.activeElement.id === "answer-input") submitAnswer();
});

document.addEventListener("DOMContentLoaded", loadGameState);