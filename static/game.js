function term(msg) {
  const t = document.getElementById("terminal");
  t.innerHTML += msg + "<br>";
  t.scrollTop = t.scrollHeight;
}

// Load puzzle by id
async function loadPuzzle(id) {
  term("Loading puzzle: " + id + " …");

  const res = await fetch("/api/puzzle/" + id);
  if (!res.ok) {
    term("[X] Failed to load puzzle.");
    return;
  }
  const p = await res.json();
  renderPuzzle(p);
}

function renderPuzzle(p) {
  const area = document.getElementById("puzzle-area");

  // RSA
  if (p.id === "hash") {
    area.innerHTML = `
      <h3>${p.title}</h3>
      <pre style="white-space:pre-wrap;">${p.description}</pre>
      <label>Enter the recovered 4-letter metal word (ANSWER, e.g. GOLD):</label>
      <input id="answer-input" placeholder="GOLD" />
      <button onclick="submitAnswer('${p.id}')">Submit Answer</button>
      <div id="result-msg" style="margin-top:6px;"></div>
    `;
    return;
  }

  // Phishing
  if (p.id === "phishing") {
    area.innerHTML = `
      <h3>${p.title}</h3>
      <pre style="white-space:pre-wrap;">${p.email}</pre>
      <pre style="white-space:pre-wrap;">${p.description}</pre>
      <label>Enter your analysis (ANSWER, e.g. 'punycode attack'):</label>
      <input id="answer-input" placeholder="punycode attack" />
      <button onclick="submitAnswer('${p.id}')">Submit Answer</button>
      <div id="result-msg" style="margin-top:6px;"></div>
    `;
    return;
  }

  // JS reverse engineering
  if (p.id === "encrypt") {
    area.innerHTML = `
      <h3>${p.title}</h3>
      <p style="font-size:0.9rem;">Reverse this JavaScript to find the ONE input string that validate() accepts.</p>
      <pre style="white-space:pre-wrap; font-size:0.8rem; background:#020617; padding:6px; border-radius:4px; border:1px solid #1f2937;">
${p.js_code}
      </pre>
      <pre style="white-space:pre-wrap;">${p.description}</pre>
      <label>Enter the input string that passes validate (ANSWER):</label>
      <input id="answer-input" placeholder="FLAG{...}" />
      <button onclick="submitAnswer('${p.id}')">Submit Answer</button>
      <div id="result-msg" style="margin-top:6px;"></div>
    `;
    return;
  }

  // PNG forensics
  if (p.id === "logs") {
    area.innerHTML = `
      <h3>${p.title}</h3>
      <pre style="white-space:pre-wrap;">${p.description}</pre>
      <p style="font-size:0.9rem;">Corrupted PNG (Base64):</p>
      <textarea readonly style="width:100%;height:120px;background:#020617;color:#e5e7eb;border:1px solid #1f2937;font-size:0.8rem;">${p.png_b64}</textarea>
      <label>Enter the flag you recover from the PNG (ANSWER):</label>
      <input id="answer-input" placeholder="FLAG{...}" />
      <button onclick="submitAnswer('${p.id}')">Submit Answer</button>
      <div id="result-msg" style="margin-top:6px;"></div>
    `;
    return;
  }

  // Session prediction
  if (p.id === "firewall") {
    area.innerHTML = `
      <h3>${p.title}</h3>
      <pre style="white-space:pre-wrap;">${p.description}</pre>
      <label>Enter the predicted admin session ID (ANSWER), e.g. sess_900050:</label>
      <input id="answer-input" placeholder="sess_...." />
      <button onclick="submitAnswer('${p.id}')">Submit Answer</button>
      <div id="result-msg" style="margin-top:6px;"></div>
    `;
    return;
  }

  area.innerHTML = "<p>Unknown puzzle type.</p>";
}

// Submit ANSWER to /api/submit_answer/<id>
async function submitAnswer(id) {
  const inputEl = document.getElementById("answer-input");
  const val = inputEl ? inputEl.value.trim() : "";
  if (!val) {
    alert("Please enter an answer first.");
    return;
  }

  const res = await fetch("/api/submit_answer/" + id, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer: val })
  });

  if (!res.ok) {
    term("[X] Submission error.");
    return;
  }

  const data = await res.json();
  const resultDiv = document.getElementById("result-msg");

  if (data.correct) {
    const flag = data.reward_flag;
    resultDiv.textContent = "Correct! Reward flag: " + flag + " (enter this in the Flag Console on the left).";
    resultDiv.style.color = "#22c55e";
    term("[✔] Correct answer for " + id + ". Reward flag: " + flag);
  } else {
    resultDiv.textContent = "Incorrect. Try again.";
    resultDiv.style.color = "#f97316";
    term("[X] Incorrect answer for " + id + ".");
  }
}

// Submit FLAG to /api/submit_flag
async function submitFlag() {
  const input = document.getElementById("flag-input");
  const val = input.value.trim();
  if (!val) {
    alert("Enter a flag first.");
    return;
  }

  const res = await fetch("/api/submit_flag", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ flag: val })
  });

  if (!res.ok) {
    term("[X] Flag submission error.");
    return;
  }

  const data = await res.json();
  if (data.valid) {
    if (data.already) {
      term("[i] Flag already registered: " + data.flag);
      alert("Flag already registered.");
    } else {
      term("[✔] Flag accepted: " + data.flag);
      alert("Flag accepted!");
      input.value = "";
    }
  } else {
    term("[X] Invalid flag: " + val);
    alert("Invalid flag.");
  }
}

// Vault button
async function attemptVault() {
  term("Attempting vault unlock…");
  const res = await fetch("/api/check_vault");
  const data = await res.json();

  if (data.opened) {
    term("VAULT OPENED!");
    term("FINAL FLAG: " + data.final_flag);
    document.getElementById("vault-status").textContent = "VAULT OPEN";
  } else {
    term("Vault still locked. Missing flags:");
    (data.missing || []).forEach(f => term("- " + f));
  }
}
