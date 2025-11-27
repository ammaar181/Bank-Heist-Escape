function typeToTerminal(text) {
    const box = document.getElementById("terminal-output");
    box.innerHTML += text + "<br>";
    box.scrollTop = box.scrollHeight;
}

async function loadPuzzle(type) {
    if (type === "password") {
        typeToTerminal("Opening keypad door system...");
        const res = await fetch("/api/puzzle/password");
        const puzzle = await res.json();
        renderPasswordPuzzle(puzzle);
    } else {
        typeToTerminal("System '" + type + "' not wired up yet.");
        const area = document.getElementById("puzzle-area");
        area.innerHTML = "<p>This system’s puzzle will be added later.</p>";
    }
}

function renderPasswordPuzzle(puzzle) {
    const area = document.getElementById("puzzle-area");
    area.innerHTML = `
      <h3>${puzzle.title}</h3>
      <pre style="white-space:pre-wrap;">${puzzle.description}</pre>
      <label>Enter 4-digit code:</label>
      <input id="password-answer" maxlength="4" />
      <button onclick="submitPassword()">Submit Code</button>
      <div id="password-result" style="margin-top:6px;"></div>
    `;
}

async function submitPassword() {
    const val = document.getElementById("password-answer").value;
    const res = await fetch("/api/submit/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: val })
    });
    const data = await res.json();
    const resultDiv = document.getElementById("password-result");
    if (data.correct) {
        resultDiv.textContent = data.message;
        resultDiv.style.color = "#22c55e";
        typeToTerminal("[OK] " + data.message);
        // later: mark puzzle complete, maybe change vault, etc.
    } else {
        resultDiv.textContent = data.message || "Incorrect.";
        resultDiv.style.color = "#f97316";
        typeToTerminal("[X] " + (data.message || "Incorrect code."));
    }
}

// vault click logs a message for now
document.getElementById("vault").onclick = function () {
    typeToTerminal("Vault accessed. You’ll need all codes to open it.");
};
