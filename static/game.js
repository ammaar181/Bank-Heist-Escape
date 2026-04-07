let currentState = null;

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

    hints.forEach((hint) => {
        const li = document.createElement("li");
        li.innerText = hint;
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
        target.innerText = "None yet";
        return;
    }
    target.innerText = fragments.join(" • ");
}

function renderRecoveredEvidence(answers) {
    const target = document.getElementById("recovered-evidence");
    if (!answers || Object.keys(answers).length === 0) {
        target.innerText = "No evidence recovered yet.";
        return;
    }

    const parts = [];
    if (answers.phase_1) parts.push(`Phase 1 password: ${answers.phase_1}`);
    if (answers.phase_2) parts.push(`Phase 2 intrusion: ${answers.phase_2}`);
    if (answers.phase_3) parts.push(`Phase 3 relay token: ${answers.phase_3}`);
    if (answers.phase_4) parts.push(`Phase 4 vault code: ${answers.phase_4}`);

    target.innerHTML = parts.join("<br>");
}

function renderPhase1(state) {
    const tested = state.phase1.tested_candidates || [];
    const testedHtml = tested.length
        ? tested.map(c => `<div>${c}</div>`).join("")
        : "No candidates tested yet.";

    return `
        <div class="brief-box">
            <div class="brief-label">Leaked Credentials</div>
            <div class="brief-text">
                Username: <strong>${state.phase1.username}</strong><br>
                Hash Type: <strong>${state.phase1.hash_type}</strong><br>
                Hash: <strong>${state.phase1.hash}</strong>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Candidate Wordlist</div>
            <div class="brief-text">
                ${state.phase1.candidates.map(candidate => `
                    <button class="main-btn" style="margin: 4px;" onclick="testCandidate('${candidate}')">${candidate}</button>
                `).join("")}
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Tested Candidates</div>
            <div class="brief-text">${testedHtml}</div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Hash Test Output</div>
            <div class="brief-text" id="phase1-output">
                ${state.phase1.match_found ? "A valid hash match has been found. Submit the cracked password." : "Test candidate passwords against the leaked hash."}
            </div>
        </div>
    `;
}

function renderPhase2(state) {
    const rows = state.phase2.rows || [];
    const selected = state.phase2.selected_rows || [];

    const tableRows = rows.map(row => {
        const isSelected = selected.includes(row.id);
        return `
            <tr onclick="toggleLogRow(${row.id})" style="cursor:pointer; background:${isSelected ? 'rgba(0,240,168,0.12)' : 'transparent'};">
                <td style="padding:8px;">${isSelected ? "✓" : ""}</td>
                <td style="padding:8px;">${row.time}</td>
                <td style="padding:8px;">${row.user}</td>
                <td style="padding:8px;">${row.ip}</td>
                <td style="padding:8px;">${row.event}</td>
                <td style="padding:8px;">${row.status}</td>
            </tr>
        `;
    }).join("");

    return `
        <div class="brief-box">
            <div class="brief-label">Authentication Logs</div>
            <div class="brief-text">
                Click rows to mark the suspicious intrusion sequence.
                ${state.phase2.analysis_unlocked ? "<br><br><strong>Correct breach pattern identified. You may now submit IP|username.</strong>" : ""}
            </div>
            <div style="overflow-x:auto; margin-top:12px;">
                <table style="width:100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align:left; padding:8px;">Sel</th>
                            <th style="text-align:left; padding:8px;">Time</th>
                            <th style="text-align:left; padding:8px;">User</th>
                            <th style="text-align:left; padding:8px;">IP</th>
                            <th style="text-align:left; padding:8px;">Event</th>
                            <th style="text-align:left; padding:8px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>${tableRows}</tbody>
                </table>
            </div>
        </div>
    `;
}

function renderPhase3(state) {
    const attempts = state.phase3.decode_attempts || [];
    const attemptsHtml = attempts.length
        ? attempts.map(a => `<div><strong>${a.method}</strong>: ${a.output}</div><br>`).join("")
        : "No decode attempts yet.";

    return `
        <div class="brief-box">
            <div class="brief-label">Captured Message</div>
            <div class="brief-text">${state.phase3.encoded}</div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Decode Methods</div>
            <div class="brief-text">
                <button class="main-btn" style="margin:4px;" onclick="decodeWithMethod('base64')">Base64</button>
                <button class="main-btn" style="margin:4px;" onclick="decodeWithMethod('hex')">Hex</button>
                <button class="main-btn" style="margin:4px;" onclick="decodeWithMethod('rot13')">ROT13</button>
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Decoder Output</div>
            <div class="brief-text" id="phase3-output">
                ${attemptsHtml}
                ${state.phase3.correct_method_found ? "<strong>Correct decode method found. Extract the token and submit it.</strong>" : ""}
            </div>
        </div>
    `;
}

function renderPhase4(state) {
    const password = state.phase_answers.phase_1 || "";
    const passwordLength = password.length;

    return `
        <div class="brief-box">
            <div class="brief-label">Vault Assembly Rules</div>
            <div class="brief-text">
                Build the final code using:
                <br>1. The three recovered vault fragments in phase order
                <br>2. The length of the cracked password from Phase 1
            </div>
        </div>

        <div class="brief-box">
            <div class="brief-label">Recovered Evidence</div>
            <div class="brief-text">
                Phase 1 password: <strong>${state.phase_answers.phase_1 || "Not found"}</strong><br>
                Phase 1 password length: <strong>${passwordLength || "Unknown"}</strong><br>
                Phase 2 intrusion: <strong>${state.phase_answers.phase_2 || "Not found"}</strong><br>
                Phase 3 relay token: <strong>${state.phase_answers.phase_3 || "Not found"}</strong><br>
                Vault fragments: <strong>${(state.vault_fragments || []).join(" • ") || "None"}</strong>
            </div>
        </div>
    `;
}

function renderCompleted() {
    return `
        <div class="brief-box">
            <div class="brief-label">Vault Entry</div>
            <div class="brief-text">
                The final vault door unlocks with a deep mechanical click. The chamber is open.
                You successfully completed the cyber bank heist.
            </div>
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
    } else if (state.progress === 2) {
        container.innerHTML = renderPhase2(state);
    } else if (state.progress === 3) {
        container.innerHTML = renderPhase3(state);
    } else if (state.progress === 4) {
        container.innerHTML = renderPhase4(state);
    }
}

function loadGameState() {
    fetch("/get_game_state")
        .then(response => response.json())
        .then(data => {
            currentState = data;

            updateProgress(data.progress, data.total);
            document.getElementById("challenge-title").innerText = data.title;
            document.getElementById("challenge-desc").innerText = data.description;
            document.getElementById("objective-text").innerText = data.objective;
            document.getElementById("task-brief").innerText = data.task_brief;
            document.getElementById("answer-label").innerText = data.answer_label || "";
            document.getElementById("status-pill").innerText = data.completed ? "Vault Opened" : `Phase ${data.progress} Active`;

            renderHints(data.hints);
            renderVaultFragments(data.vault_fragments);
            renderRecoveredEvidence(data.phase_answers);
            renderPhaseContent(data);

            if (data.completed) {
                setMessage("success", "HEIST COMPLETE — VAULT ENTERED");
            } else {
                document.getElementById("answer-input").disabled = false;
                setMessage("neutral", "Awaiting answer...");
            }
        })
        .catch(() => {
            setMessage("error", "Failed to load challenge data.");
        });
}

function testCandidate(candidate) {
    fetch("/phase1_test_candidate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ candidate: candidate })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                setMessage("error", data.message);
                return;
            }

            const output = document.getElementById("phase1-output");
            output.innerHTML = `
                Candidate: <strong>${data.candidate}</strong><br>
                MD5: <strong>${data.candidate_hash}</strong><br>
                Result: <strong>${data.message}</strong>
            `;

            if (data.is_match) {
                setMessage("success", "Correct candidate found. Now submit the cracked password.");
            } else {
                setMessage("neutral", "No match. Test another candidate.");
            }

            setTimeout(loadGameState, 250);
        })
        .catch(() => {
            setMessage("error", "Candidate test failed.");
        });
}

function toggleLogRow(rowId) {
    fetch("/phase2_toggle_row", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ row_id: rowId })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                setMessage("error", data.message);
                return;
            }

            if (data.analysis_unlocked) {
                setMessage("success", "Correct intrusion pattern identified. Submit IP|username.");
            } else {
                setMessage("neutral", "Log selection updated.");
            }

            loadGameState();
        })
        .catch(() => {
            setMessage("error", "Failed to update log selection.");
        });
}

function decodeWithMethod(method) {
    fetch("/phase3_decode", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ method: method })
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                setMessage("error", data.message);
                return;
            }

            const output = document.getElementById("phase3-output");
            output.innerHTML += `<div><strong>${data.method}</strong>: ${data.output}</div><br>`;

            if (data.correct_method_found) {
                setMessage("success", "Correct decode method found. Extract the token and submit it.");
            } else {
                setMessage("neutral", "Wrong method. Try another decoder.");
            }

            setTimeout(loadGameState, 250);
        })
        .catch(() => {
            setMessage("error", "Decoder failed.");
        });
}

function submitAnswer() {
    const input = document.getElementById("answer-input");
    const answer = input.value.trim();

    if (!answer) {
        setMessage("error", "Enter an answer before submitting.");
        return;
    }

    fetch("/submit_answer", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ answer: answer })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                input.value = "";
                setMessage("success", data.message);
                setTimeout(loadGameState, 500);
            } else {
                setMessage("error", data.message);
            }
        })
        .catch(() => {
            setMessage("error", "Submission failed.");
        });
}

window.onload = function () {
    loadGameState();
};