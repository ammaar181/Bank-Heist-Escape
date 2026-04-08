let currentState = null;

// ── UTILITIES ──────────────────────────────────────────────────────────────

function setMessage(type, text) {
    const box = document.getElementById("result");
    box.className = `message-box ${type}`;
    box.innerText = text;
}

function renderHints(hints) {
    const hintList = document.getElementById("hint-list");
    hintList.innerHTML = "";
    if (!hints || hints.length === 0) {
        const li = document.createElement("li");
        li.innerText = "No hints available.";
        hintList.appendChild(li);
        return;
    }
    hints.forEach((hint, i) => {
        const li = document.createElement("li");
        li.innerText = hint;
        li.style.animationDelay = `${i * 0.08}s`;
        hintList.appendChild(li);
    });
}

function updateProgress(progress, total) {
    const shown = Math.min(progress, total);
    const percent = Math.round((shown / total) * 100);
    document.getElementById("progress-text").innerText = `${shown} / ${total}`;
    document.getElementById("progress-percentage").innerText = `${percent}%`;
    document.getElementById("progress-fill").style.width = `${percent}%`;
}

function renderVaultFragments(fragments) {
    const target = document.getElementById("vault-fragments");
    if (!fragments || fragments.length === 0) {
        target.innerText = "None recovered yet";
        return;
    }
    target.innerHTML = fragments.map(f => `<span class="fragment-chip">${f}</span>`).join(" ");
}

function renderRecoveredEvidence(answers) {
    const target = document.getElementById("recovered-evidence");
    if (!answers || Object.keys(answers).length === 0) {
        target.innerText = "No evidence recovered yet.";
        return;
    }
    const parts = [];
    if (answers.phase_1) parts.push(`<div class="evidence-row"><span class="ev-label">Phase 1 password</span><span class="ev-value">${answers.phase_1}</span></div>`);
    if (answers.phase_2) parts.push(`<div class="evidence-row"><span class="ev-label">Phase 2 intrusion</span><span class="ev-value">${answers.phase_2}</span></div>`);
    if (answers.phase_3) parts.push(`<div class="evidence-row"><span class="ev-label">Phase 3 token</span><span class="ev-value">${answers.phase_3}</span></div>`);
    if (answers.phase_4) parts.push(`<div class="evidence-row"><span class="ev-label">Phase 4 vault code</span><span class="ev-value">${answers.phase_4}</span></div>`);
    target.innerHTML = parts.join("");
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

// ── PHASE 1: Password Audit ────────────────────────────────────────────────

function renderPhase1(state) {
    const tested = state.phase1.tested_candidates || [];

    const tableRows = tested.length
        ? tested.map(c => {
            // Mark the last tested as match if match_found is newly true
            const isMatchRow = state.phase1.match_found && c === tested[tested.length - 1];
            return `
              <tr class="hash-row ${isMatchRow ? 'hash-match' : ''}">
                <td class="hash-cell candidate-cell">${escapeHtml(c)}</td>
                <td class="hash-cell result-cell">${isMatchRow
                    ? '<span class="match-badge">✓ MATCH</span>'
                    : '<span class="nomatch-badge">✗ No match</span>'}</td>
              </tr>`;
        }).join("")
        : `<tr><td colspan="2" class="hash-cell muted-cell">No candidates tested yet — enter a candidate below.</td></tr>`;

    return `
        <div class="brief-box">
            <div class="brief-label">Leaked Credential</div>
            <div class="brief-text">
                <div class="cred-row"><span class="cred-key">Username</span><span class="cred-val">${state.phase1.username}</span></div>
                <div class="cred-row"><span class="cred-key">Hash Type</span><span class="cred-val">${state.phase1.hash_type}</span></div>
                <div class="cred-row">
                    <span class="cred-key">Target Hash</span>
                    <span class="cred-val hash-mono">${state.phase1.hash}</span>
                </div>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Recovered Wordlist</div>
            <div class="brief-text wordlist-grid">
                ${state.phase1.candidates.map(c => `<span class="wordlist-item">${escapeHtml(c)}</span>`).join("")}
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Hash Tester</div>
            <div class="brief-text">
                <p class="tester-note">Type a candidate password below. The server will compute its MD5 and compare against the target hash.</p>
                <div class="tester-row">
                    <input type="text" id="candidate-input" placeholder="Enter candidate password..." autocomplete="off" spellcheck="false" />
                    <button class="sec-btn" onclick="testTypedCandidate()">Test Hash</button>
                </div>
                <div id="live-hash-display" class="live-hash-box" style="display:none;"></div>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Test Results <span class="count-badge">${tested.length} tested</span></div>
            <table class="hash-table">
                <thead><tr><th class="hash-cell">Candidate</th><th class="hash-cell">Result</th></tr></thead>
                <tbody>${tableRows}</tbody>
            </table>
        </div>

        ${state.phase1.match_found ? `
        <div class="alert-box success-alert">
            Hash match confirmed. Enter the exact plaintext password in the submission field below.
        </div>` : ""}
    `;
}

// ── PHASE 2: Log Analysis ──────────────────────────────────────────────────

function renderPhase2(state) {
    const rows = state.phase2.rows || [];
    const selected = state.phase2.selected_rows || [];

    const tableRows = rows.map(row => {
        const isSelected = selected.includes(row.id);
        const isExternal = row.dept === "External";
        return `
            <tr onclick="toggleLogRow(${row.id})"
                class="log-row ${isSelected ? 'log-selected' : ''} ${isExternal ? 'log-external-row' : ''}"
                title="Click to select/deselect">
                <td class="log-cell sel-cell">${isSelected ? '<span class="sel-tick">✓</span>' : '<span class="sel-dot">·</span>'}</td>
                <td class="log-cell mono-cell">${row.time}</td>
                <td class="log-cell">${row.user}</td>
                <td class="log-cell mono-cell">${row.ip}</td>
                <td class="log-cell event-cell ${row.event === 'LOGIN_FAILED' ? 'ev-fail' : 'ev-success'}">${row.event}</td>
                <td class="log-cell dept-cell ${isExternal ? 'dept-ext' : 'dept-int'}">${row.dept}</td>
            </tr>`;
    }).join("");

    return `
        <div class="brief-box">
            <div class="brief-label">IP Range Reference</div>
            <div class="brief-text ip-ref-grid">
                <div class="ip-ref-item"><span class="ip-range int-range">10.0.0.0/8</span><span class="ip-desc">Bank internal infrastructure</span></div>
                <div class="ip-ref-item"><span class="ip-range int-range">172.16.0.0/12</span><span class="ip-desc">Bank internal infrastructure</span></div>
                <div class="ip-ref-item"><span class="ip-range ext-range">All other ranges</span><span class="ip-desc">External / untrusted</span></div>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Authentication Log — ${rows.length} entries <span class="sel-count">${selected.length} selected</span></div>
            <div class="log-scroll">
                <table class="log-table">
                    <thead>
                        <tr>
                            <th class="log-cell sel-cell"></th>
                            <th class="log-cell">Time</th>
                            <th class="log-cell">User</th>
                            <th class="log-cell">Source IP</th>
                            <th class="log-cell">Event</th>
                            <th class="log-cell">Network</th>
                        </tr>
                    </thead>
                    <tbody>${tableRows}</tbody>
                </table>
            </div>
            <p class="log-note">Click rows to mark the breach sequence. Select only the rows that form the attack pattern.</p>
        </div>

        ${state.phase2.analysis_unlocked
            ? `<div class="alert-box success-alert">Breach pattern confirmed. Submit: <strong>AttackerIP|username</strong></div>`
            : `<div class="alert-box neutral-alert">Select rows forming the intrusion pattern: rapid failures from one external IP leading to success on the same account.</div>`}
    `;
}

// ── PHASE 3: Encoded Transmission ─────────────────────────────────────────

function renderPhase3(state) {
    const attempts = state.phase3.decode_attempts || [];

    const attemptsHtml = attempts.length
        ? attempts.map(a => `
            <div class="decode-attempt ${a.is_correct ? 'decode-correct' : 'decode-wrong'}">
                <div class="decode-method-label">${a.method.toUpperCase()} ${a.is_correct
                    ? '<span class="match-badge">✓ READABLE</span>'
                    : '<span class="nomatch-badge">✗ GARBLED</span>'}</div>
                <div class="decode-output">${escapeHtml(a.output)}</div>
            </div>`).join("")
        : `<div class="muted-cell">No decode attempts yet.</div>`;

    return `
        <div class="brief-box">
            <div class="brief-label">Intercepted Message (Encoded)</div>
            <div class="brief-text">
                <div class="encoded-display">${escapeHtml(state.phase3.encoded)}</div>
                <p class="tester-note">This uses a common text-safe encoding scheme. Select a decoder below and judge the output.</p>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Available Decoders</div>
            <div class="brief-text decode-btn-row">
                <button class="sec-btn" onclick="decodeWithMethod('base64')">Base64</button>
                <button class="sec-btn" onclick="decodeWithMethod('hex')">Hex</button>
                <button class="sec-btn" onclick="decodeWithMethod('rot13')">ROT13</button>
                <button class="sec-btn" onclick="decodeWithMethod('caesar')">Caesar</button>
                <button class="sec-btn" onclick="decodeWithMethod('url')">URL Decode</button>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Decoder Output History <span class="count-badge">${attempts.length} tried</span></div>
            <div class="decode-history">${attemptsHtml}</div>
        </div>

        ${state.phase3.correct_method_found ? `
        <div class="alert-box success-alert">
            Readable output confirmed. Extract the token word from the decoded message and submit it below in lowercase.
        </div>` : ""}
    `;
}

// ── PHASE 4: Vault Assembly ────────────────────────────────────────────────

function renderPhase4(state) {
    const password = state.phase_answers.phase_1 || "";
    const passwordLength = password.length;
    const fragments = state.vault_fragments || [];

    return `
        <div class="brief-box">
            <div class="brief-label">Assembly Instructions</div>
            <div class="brief-text">
                <div class="rule-step"><span class="rule-num">1</span><span>Concatenate vault fragments in phase order: Phase 1 → Phase 2 → Phase 3</span></div>
                <div class="rule-step"><span class="rule-num">2</span><span>Append the exact character count of the Phase 1 plaintext password</span></div>
                <div class="rule-step"><span class="rule-num">3</span><span>No separators — submit the full numeric string</span></div>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Recovered Evidence</div>
            <div class="brief-text">
                <div class="evidence-row"><span class="ev-label">Phase 1 password</span><span class="ev-value">${state.phase_answers.phase_1 || '<span class="muted-val">Not recovered</span>'}</span></div>
                <div class="evidence-row"><span class="ev-label">Password character count</span><span class="ev-value">${passwordLength ? passwordLength + ' characters' : '<span class="muted-val">Unknown</span>'}</span></div>
                <div class="evidence-row"><span class="ev-label">Phase 2 intrusion</span><span class="ev-value">${state.phase_answers.phase_2 || '<span class="muted-val">Not recovered</span>'}</span></div>
                <div class="evidence-row"><span class="ev-label">Phase 3 relay token</span><span class="ev-value">${state.phase_answers.phase_3 || '<span class="muted-val">Not recovered</span>'}</span></div>
                <div class="evidence-row"><span class="ev-label">Vault fragments</span><span class="ev-value">${fragments.length ? fragments.map(f => `<span class="fragment-chip">${f}</span>`).join(" ") : '<span class="muted-val">None</span>'}</span></div>
            </div>
        </div>
    `;
}

function renderCompleted() {
    return `
        <div class="brief-box complete-box">
            <div class="brief-label">Operation Complete</div>
            <div class="brief-text">
                The final vault door unlocks with a deep mechanical click. The chamber is open.
            </div>
        </div>
        <div class="completion-grid">
            <div class="completion-stat"><span class="cs-label">Password Auditing</span><span class="cs-val">✓</span></div>
            <div class="completion-stat"><span class="cs-label">Log Analysis</span><span class="cs-val">✓</span></div>
            <div class="completion-stat"><span class="cs-label">Data Decoding</span><span class="cs-val">✓</span></div>
            <div class="completion-stat"><span class="cs-label">Evidence Synthesis</span><span class="cs-val">✓</span></div>
        </div>
    `;
}

function renderPhaseContent(state) {
    const container = document.getElementById("phase-content");

    if (state.completed) {
        container.innerHTML = renderCompleted();
        document.getElementById("answer-section").style.display = "none";
        return;
    }

    document.getElementById("answer-section").style.display = "block";

    if (state.progress === 1) {
        container.innerHTML = renderPhase1(state);
        attachCandidateInputListeners();
    } else if (state.progress === 2) {
        container.innerHTML = renderPhase2(state);
    } else if (state.progress === 3) {
        container.innerHTML = renderPhase3(state);
    } else if (state.progress === 4) {
        container.innerHTML = renderPhase4(state);
    }
}

function attachCandidateInputListeners() {
    const input = document.getElementById("candidate-input");
    if (!input) return;
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") testTypedCandidate();
    });
}

// ── LOAD STATE ─────────────────────────────────────────────────────────────

function loadGameState() {
    fetch("/get_game_state")
        .then(r => r.json())
        .then(data => {
            currentState = data;
            updateProgress(data.progress, data.total);
            document.getElementById("challenge-title").innerText = data.title;
            document.getElementById("challenge-desc").innerText = data.description;
            document.getElementById("objective-text").innerText = data.objective;
            document.getElementById("task-brief").innerText = data.task_brief;
            document.getElementById("answer-label").innerText = data.answer_label || "";
            document.getElementById("status-pill").innerText = data.completed
                ? "Vault Opened"
                : `Phase ${Math.min(data.progress, data.total)} Active`;

            renderHints(data.hints);
            renderVaultFragments(data.vault_fragments);
            renderRecoveredEvidence(data.phase_answers);
            renderPhaseContent(data);

            if (data.completed) {
                setMessage("success", "HEIST COMPLETE — VAULT ENTERED");
                document.getElementById("status-pill").classList.add("status-complete");
            } else {
                const inp = document.getElementById("answer-input");
                if (inp) inp.disabled = false;
                setMessage("neutral", "Awaiting answer...");
            }
        })
        .catch(() => setMessage("error", "Failed to load challenge data."));
}

// ── ACTIONS ────────────────────────────────────────────────────────────────

function testTypedCandidate() {
    const input = document.getElementById("candidate-input");
    if (!input) return;
    const candidate = input.value.trim();

    if (!candidate) {
        setMessage("error", "Enter a candidate password to test.");
        return;
    }

    fetch("/phase1_test_candidate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate })
    })
        .then(r => r.json())
        .then(data => {
            if (!data.success) { setMessage("error", data.message); return; }

            const display = document.getElementById("live-hash-display");
            if (display) {
                display.style.display = "block";
                display.innerHTML = `
                    <div class="hash-compare">
                        <div class="hc-row"><span class="hc-label">Candidate</span><span class="hc-val mono">${escapeHtml(data.candidate)}</span></div>
                        <div class="hc-row"><span class="hc-label">Computed MD5</span><span class="hc-val mono ${data.is_match ? 'match-text' : ''}">${data.candidate_hash}</span></div>
                        <div class="hc-row"><span class="hc-label">Target Hash&nbsp;&nbsp;</span><span class="hc-val mono">${data.target_hash}</span></div>
                        <div class="hc-row"><span class="hc-label">Result</span><span class="hc-val ${data.is_match ? 'match-text' : 'nomatch-text'}">${data.message}</span></div>
                    </div>`;
            }

            if (data.is_match) {
                setMessage("success", "Hash match found. Enter the exact plaintext password below to submit.");
            } else {
                setMessage("neutral", `No match for '${escapeHtml(data.candidate)}'. Try the next candidate.`);
            }

            input.value = "";
            setTimeout(loadGameState, 250);
        })
        .catch(() => setMessage("error", "Candidate test failed."));
}

function toggleLogRow(rowId) {
    fetch("/phase2_toggle_row", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ row_id: rowId })
    })
        .then(r => r.json())
        .then(data => {
            if (!data.success) { setMessage("error", data.message); return; }
            if (data.analysis_unlocked) {
                setMessage("success", "Correct breach pattern identified. Submit: AttackerIP|username");
            } else {
                setMessage("neutral", "Row selection updated. Keep building the breach sequence.");
            }
            loadGameState();
        })
        .catch(() => setMessage("error", "Failed to update log selection."));
}

function decodeWithMethod(method) {
    fetch("/phase3_decode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method })
    })
        .then(r => r.json())
        .then(data => {
            if (!data.success) { setMessage("error", data.message); return; }
            if (data.correct_method_found) {
                setMessage("success", "Readable output confirmed. Extract the relay token and submit below.");
            } else {
                setMessage("neutral", `${method.toUpperCase()} produced garbled output. Try another method.`);
            }
            setTimeout(loadGameState, 250);
        })
        .catch(() => setMessage("error", "Decoder failed."));
}

function submitAnswer() {
    const input = document.getElementById("answer-input");
    const answer = input.value.trim();

    if (!answer) { setMessage("error", "Enter an answer before submitting."); return; }

    fetch("/submit_answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                input.value = "";
                setMessage("success", data.message);
                setTimeout(loadGameState, 500);
            } else {
                setMessage("error", data.message);
            }
        })
        .catch(() => setMessage("error", "Submission failed."));
}

window.onload = function () {
    loadGameState();
};