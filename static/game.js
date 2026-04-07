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
    if (answers.phase_2) parts.push(`Phase 2 attacker IP: ${answers.phase_2}`);
    if (answers.phase_3) parts.push(`Phase 3 relay token: ${answers.phase_3}`);
    if (answers.phase_4) parts.push(`Phase 4 vault code: ${answers.phase_4}`);

    target.innerHTML = parts.join("<br>");
}

function renderPhaseContent(state) {
    const container = document.getElementById("phase-content");
    container.innerHTML = "";

    if (state.completed) {
        container.innerHTML = `
            <div class="brief-box">
                <div class="brief-label">Vault Entry</div>
                <div class="brief-text">
                    The final vault door unlocks with a deep mechanical click. The chamber is open.
                    You successfully completed the cyber bank heist.
                </div>
            </div>
        `;
        document.getElementById("answer-section").style.display = "none";
        return;
    }

    document.getElementById("answer-section").style.display = "block";

    if (state.progress === 1) {
        container.innerHTML = `
            <div class="brief-box">
                <div class="brief-label">Leaked Credentials</div>
                <div class="brief-text">
                    Username: <strong>e.mercer</strong><br>
                    Hash Type: <strong>MD5</strong><br>
                    Hash: <strong>6f2ebf3c1f19f8c6e5953e8a0d31a59f</strong><br><br>
                    Wordlist:<br>
                    - welcome1<br>
                    - banksecure<br>
                    - winter2024<br>
                    - vaultrunner9<br>
                    - letmein123
                </div>
            </div>

            <div class="answer-row" style="margin-bottom: 14px;">
                <button class="main-btn" onclick="runCrack()">Run Crack Simulator</button>
            </div>

            <div class="brief-box">
                <div class="brief-label">Crack Terminal</div>
                <div class="brief-text" id="crack-terminal">Terminal idle. Run the simulator to begin.</div>
            </div>
        `;
    }

    if (state.progress === 2) {
        container.innerHTML = `
            <div class="answer-row" style="margin-bottom: 14px;">
                <button class="main-btn" onclick="loadLogs('ALL')">All Logs</button>
                <button class="main-btn" onclick="loadLogs('FAILED')">Failed Logins</button>
                <button class="main-btn" onclick="loadLogs('SUCCESS')">Successful Logins</button>
            </div>

            <div class="brief-box">
                <div class="brief-label">Authentication Logs</div>
                <div class="brief-text" id="log-viewer">Loading logs...</div>
            </div>
        `;
        loadLogs("ALL");
    }

    if (state.progress === 3) {
        container.innerHTML = `
            <div class="brief-box">
                <div class="brief-label">Captured Encoded Message</div>
                <div class="brief-text">
                    VmF1bHQgcmVsYXkgdG9rZW46IE5JR0hUR0xBU1M=
                </div>
            </div>

            <div class="answer-row" style="margin-bottom: 14px;">
                <button class="main-btn" onclick="decodeMessage()">Run Decoder</button>
            </div>

            <div class="brief-box">
                <div class="brief-label">Decoder Output</div>
                <div class="brief-text" id="decoder-output">Decoder idle. Run the decoder to reveal the message.</div>
            </div>
        `;
    }

    if (state.progress === 4) {
        container.innerHTML = `
            <div class="brief-box">
                <div class="brief-label">Vault Assembly Rules</div>
                <div class="brief-text">
                    Build the final vault code using:
                    <br>1. The three recovered vault fragments in phase order
                    <br>2. The length of the cracked password from Phase 1
                    <br><br>
                    Example format: [fragments][password length]
                </div>
            </div>

            <div class="brief-box">
                <div class="brief-label">Evidence Summary</div>
                <div class="brief-text">
                    Cracked Password: <strong>${state.phase_answers.phase_1 || "Not found"}</strong><br>
                    Attacker IP: <strong>${state.phase_answers.phase_2 || "Not found"}</strong><br>
                    Relay Token: <strong>${state.phase_answers.phase_3 || "Not found"}</strong><br>
                    Vault Fragments: <strong>${(state.vault_fragments || []).join(" • ") || "None"}</strong>
                </div>
            </div>
        `;
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

function runCrack() {
    fetch("/run_crack", {
        method: "POST"
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                setMessage("error", data.message);
                return;
            }

            const terminal = document.getElementById("crack-terminal");
            terminal.innerHTML = "";

            let index = 0;
            const lines = data.lines;

            const timer = setInterval(() => {
                if (index >= lines.length) {
                    clearInterval(timer);
                    setMessage("success", "Password recovered. Submit it to continue.");
                    return;
                }

                terminal.innerHTML += `${lines[index]}<br>`;
                index++;
            }, 500);
        })
        .catch(() => {
            setMessage("error", "Crack simulator failed.");
        });
}

function loadLogs(filterType) {
    fetch(`/get_logs?filter=${filterType}`)
        .then(response => response.json())
        .then(data => {
            const viewer = document.getElementById("log-viewer");

            if (!data.success) {
                viewer.innerText = "Unable to load logs.";
                return;
            }

            if (!data.rows || data.rows.length === 0) {
                viewer.innerText = "No logs found.";
                return;
            }

            let html = `
                <table style="width:100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="text-align:left; padding:8px;">Time</th>
                            <th style="text-align:left; padding:8px;">User</th>
                            <th style="text-align:left; padding:8px;">IP</th>
                            <th style="text-align:left; padding:8px;">Event</th>
                            <th style="text-align:left; padding:8px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.rows.forEach(row => {
                html += `
                    <tr>
                        <td style="padding:8px;">${row.time}</td>
                        <td style="padding:8px;">${row.user}</td>
                        <td style="padding:8px;">${row.ip}</td>
                        <td style="padding:8px;">${row.event}</td>
                        <td style="padding:8px;">${row.status}</td>
                    </tr>
                `;
            });

            html += `</tbody></table>`;
            viewer.innerHTML = html;
        })
        .catch(() => {
            const viewer = document.getElementById("log-viewer");
            if (viewer) viewer.innerText = "Failed to load logs.";
        });
}

function decodeMessage() {
    fetch("/decode_message", {
        method: "POST"
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                setMessage("error", data.message);
                return;
            }

            const output = document.getElementById("decoder-output");
            output.innerHTML = `
                Encoded: <strong>${data.encoded}</strong><br><br>
                Decoded: <strong>${data.decoded}</strong>
            `;

            setMessage("success", "Message decoded. Extract the relay token and submit it.");
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

                setTimeout(() => {
                    loadGameState();
                }, 700);
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