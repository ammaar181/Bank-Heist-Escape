from flask import Flask, render_template, request, jsonify, session
import os
import base64
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "bank-heist-escape", "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

app.secret_key = "supersecretkey"


def get_initial_state():
    return {
        "progress": 1,
        "vault_fragments": [],
        "phase_answers": {},
        "phase1_tested_candidates": [],
        "phase1_match_found": False,
        "phase2_selected_rows": [],
        "phase2_analysis_unlocked": False,
        "phase3_decode_attempts": [],
        "phase3_correct_method_found": False,
        "phase4_wrong_attempts": 0,
    }


def get_state():
    if "game_state" not in session:
        session["game_state"] = get_initial_state()
    return session["game_state"]


def save_state(state):
    session["game_state"] = state
    session.modified = True


# ── PHASE 1 ──────────────────────────────────────────────────────────────────
# Players must TYPE candidates into the tester — no click-to-win buttons.
# A near-miss (VaultRunner9 vs vaultrunner9) forces genuine case-sensitivity reasoning.
PHASE1 = {
    "username": "e.mercer",
    "hash_type": "MD5",
    "password": "vaultrunner9",
    "hash": hashlib.md5("vaultrunner9".encode()).hexdigest(),
    "candidates": [
        "welcome1",
        "banksecure",
        "winter2024",
        "VaultRunner9",
        "vaultrunner9",
        "letmein123"
    ]
}

# ── PHASE 2 ──────────────────────────────────────────────────────────────────
# Status column REMOVED — players read raw logs and reason from IP, timing, pattern.
# Extra noise rows added. Internal IPs (10.x, 172.16.x) are safe infrastructure.
PHASE2_LOG_ROWS = [
    {"id": 1,  "time": "00:47:12", "user": "svc.backup",  "ip": "10.0.4.12",     "event": "LOGIN_SUCCESS", "dept": "Internal"},
    {"id": 2,  "time": "01:13:42", "user": "r.turner",    "ip": "10.0.5.33",     "event": "LOGIN_SUCCESS", "dept": "Internal"},
    {"id": 3,  "time": "02:31:08", "user": "j.finch",     "ip": "10.0.6.21",     "event": "LOGIN_FAILED",  "dept": "Internal"},
    {"id": 4,  "time": "02:44:11", "user": "a.hayes",     "ip": "185.217.92.14", "event": "LOGIN_FAILED",  "dept": "External"},
    {"id": 5,  "time": "02:44:16", "user": "a.hayes",     "ip": "185.217.92.14", "event": "LOGIN_FAILED",  "dept": "External"},
    {"id": 6,  "time": "02:44:21", "user": "a.hayes",     "ip": "185.217.92.14", "event": "LOGIN_FAILED",  "dept": "External"},
    {"id": 7,  "time": "02:44:29", "user": "a.hayes",     "ip": "185.217.92.14", "event": "LOGIN_SUCCESS", "dept": "External"},
    {"id": 8,  "time": "02:50:04", "user": "j.finch",     "ip": "172.16.2.44",   "event": "LOGIN_FAILED",  "dept": "Internal"},
    {"id": 9,  "time": "03:01:08", "user": "svc.payroll", "ip": "10.0.8.44",     "event": "LOGIN_SUCCESS", "dept": "Internal"},
    {"id": 10, "time": "03:09:51", "user": "j.finch",     "ip": "10.0.6.21",     "event": "LOGIN_FAILED",  "dept": "Internal"},
]

PHASE2_CORRECT_ROW_IDS = [4, 5, 6, 7]
PHASE2_CORRECT_IP = "185.217.92.14"
PHASE2_CORRECT_USER = "a.hayes"

# ── PHASE 3 ──────────────────────────────────────────────────────────────────
# Wrong decoders produce plausibly-structured but meaningless output — not obvious errors.
# Players must judge readability themselves.
PHASE3_ENCODED = base64.b64encode(
    b"Relay archive note: secondary transfer authorised. vault relay token = NIGHTGLASS. destroy after reading."
).decode("utf-8")
PHASE3_CORRECT_METHOD = "base64"
PHASE3_TOKEN = "nightglass"

PHASE3_WRONG_OUTPUTS = {
    "hex":    "526c596c5972636d5976 6e206e72766572206e6f 74653a2073...[malformed stream, decode failed]",
    "rot13":  "Erynl nepuvcr abgr: frpbaqnel genafsre nhgubevfrq. inhyg erynl gbxra = AVTUGTYNJF.",
    "caesar": "Pdjdb xabirob slod: vhfrqgdub wudqvihu dxwkrulvhg. ydxow uhodb wrnhq = QLJKWJODVV.",
    "url":    "%52%65%6c%61%79%20%61%72%63%68%69%76%65%20%6e%6f%74%65%3a%20[partial decode — encoding mismatch]",
}

# ── CHALLENGES ────────────────────────────────────────────────────────────────
CHALLENGES = {
    1: {
        "title": "Phase 1: Password Audit",
        "description": (
            "A password hash has been recovered from a compromised credential dump. "
            "The hash type is MD5. A wordlist of candidate passwords has also been recovered. "
            "Your job is to identify which candidate produces a matching hash."
        ),
        "objective": "Recover the plaintext password from the leaked MD5 hash.",
        "task_brief": (
            "Use the candidate tester to compute and compare MD5 hashes against the leaked hash. "
            "MD5 is case-sensitive — 'Password' and 'password' produce entirely different digests. "
            "Type each candidate into the tester to see its computed hash. "
            "Once you find a match, submit the exact plaintext password."
        ),
        "answer": "vaultrunner9",
        "answer_label": "Enter the cracked password (exact case)",
        "vault_fragment": "7",
        "hints": [
            "Hint 1: MD5 produces a fixed 32-character hex digest regardless of input length.",
            "Hint 2: Hashing is one-way — you cannot reverse it, only compare candidates against the target.",
            "Hint 3: Watch for near-matches. 'VaultRunner9' and 'vaultrunner9' hash to completely different values.",
            "Hint 4: The wordlist was sourced from a known credential breach database — common formats apply."
        ]
    },
    2: {
        "title": "Phase 2: Log Analysis",
        "description": (
            "Raw authentication logs from the bank's access control server have been intercepted. "
            "One sequence of entries reveals a real intrusion. The rest is normal traffic or isolated failures. "
            "No events are pre-labelled — identify the attack pattern from the data alone."
        ),
        "objective": "Identify the attacker's IP address and the compromised account.",
        "task_brief": (
            "Examine the logs. A brute-force attack leaves a distinct signature: rapid repeated login failures "
            "on the same account from the same source IP, followed by a successful login. "
            "Internal IPs (10.x.x.x, 172.16.x.x) are bank infrastructure. External IPs are suspicious. "
            "Select the rows forming the breach sequence, then submit: AttackerIP|username"
        ),
        "answer": f"{PHASE2_CORRECT_IP}|{PHASE2_CORRECT_USER}",
        "answer_label": "Submit as: AttackerIP|username  (e.g. 1.2.3.4|j.doe)",
        "vault_fragment": "3",
        "hints": [
            "Hint 1: Brute-force attacks involve many rapid failures before a success — count the attempts.",
            "Hint 2: External IPs (not 10.x or 172.16.x) accessing internal accounts are inherently suspicious.",
            "Hint 3: A single failed login from an internal IP is normal — focus on volume and source.",
            "Hint 4: Timestamps matter. Failures within 5–10 seconds of each other indicate automation."
        ]
    },
    3: {
        "title": "Phase 3: Encoded Transmission",
        "description": (
            "An intercepted relay message has been captured in transit. "
            "It appears encoded using a common text-safe scheme. "
            "Multiple decode methods are available — only one will yield coherent English."
        ),
        "objective": "Decode the message and extract the relay token.",
        "task_brief": (
            "Try each decode method. Wrong methods produce garbled or structured-but-unreadable output. "
            "The correct method yields readable English. Read the decoded message carefully — "
            "the relay token is a single word embedded within it. Submit the token in lowercase."
        ),
        "answer": "nightglass",
        "answer_label": "Enter the relay token (lowercase)",
        "vault_fragment": "9",
        "hints": [
            "Hint 1: Base64 is the most common scheme for transmitting binary-safe data over text channels.",
            "Hint 2: ROT13 and Caesar produce word-like output — but the words won't be coherent English.",
            "Hint 3: The token is a single capitalised word inside the decoded sentence.",
            "Hint 4: Encoding obscures data for transit safety — it is not encryption and offers no real security."
        ]
    },
    4: {
        "title": "Phase 4: Vault Code Assembly",
        "description": (
            "All three security layers have been breached. The vault requires a final composite access code "
            "assembled from the evidence recovered across the operation. "
            "This is the synthesis step — draw from everything you have found."
        ),
        "objective": "Construct and submit the final vault code.",
        "task_brief": (
            "Combine your recovered vault fragments in phase order (Phase 1 → Phase 2 → Phase 3), "
            "then append the exact character length of the Phase 1 plaintext password. "
            "No separators. Submit the complete numeric string."
        ),
        "answer": "73912",
        "answer_label": "Enter the final vault code",
        "vault_fragment": None,
        "hints": [
            "Hint 1: Three fragments recovered in order: Phase 1, Phase 2, Phase 3.",
            "Hint 2: After the fragments, append the length of the Phase 1 password — count every character.",
            "Hint 3: Count 'vaultrunner9' carefully. Every letter and digit counts.",
            "Hint 4: No spaces, no dashes. Just the raw digits concatenated in sequence."
        ]
    }
}


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    session["game_state"] = get_initial_state()
    return render_template("index.html")


@app.route("/game")
def game():
    get_state()
    return render_template("game.html")


@app.route("/get_game_state")
def get_game_state():
    state = get_state()
    progress = state["progress"]
    total = len(CHALLENGES)

    base_payload = {
        "vault_fragments": state["vault_fragments"],
        "phase_answers": state["phase_answers"],
        "phase1": {
            "username": PHASE1["username"],
            "hash_type": PHASE1["hash_type"],
            "hash": PHASE1["hash"],
            "candidates": PHASE1["candidates"],
            "tested_candidates": state["phase1_tested_candidates"],
            "match_found": state["phase1_match_found"]
        },
        "phase2": {
            "rows": PHASE2_LOG_ROWS,
            "selected_rows": state["phase2_selected_rows"],
            "analysis_unlocked": state["phase2_analysis_unlocked"]
        },
        "phase3": {
            "encoded": PHASE3_ENCODED,
            "decode_attempts": state["phase3_decode_attempts"],
            "correct_method_found": state["phase3_correct_method_found"]
        }
    }

    if progress > total:
        return jsonify({
            **base_payload,
            "completed": True,
            "progress": total,
            "total": total,
            "title": "Vault Entered",
            "description": "The final vault door unlocks and the chamber opens.",
            "objective": "Operation Complete",
            "task_brief": "All four phases completed successfully.",
            "answer_label": "",
            "hints": [
                "Inside Man: Clean breach. Grab the reserves and disappear.",
                "All security layers bypassed."
            ],
        })

    challenge = CHALLENGES[progress]

    return jsonify({
        **base_payload,
        "completed": False,
        "progress": progress,
        "total": total,
        "title": challenge["title"],
        "description": challenge["description"],
        "objective": challenge["objective"],
        "task_brief": challenge["task_brief"],
        "answer_label": challenge["answer_label"],
        "hints": challenge["hints"],
    })


@app.route("/phase1_test_candidate", methods=["POST"])
def phase1_test_candidate():
    state = get_state()

    if state["progress"] != 1:
        return jsonify({"success": False, "message": "Phase 1 is not active."})

    data = request.get_json(silent=True) or {}
    candidate = str(data.get("candidate", "")).strip()

    if not candidate:
        return jsonify({"success": False, "message": "No candidate provided."})

    candidate_hash = hashlib.md5(candidate.encode()).hexdigest()
    is_match = candidate_hash == PHASE1["hash"]

    if candidate not in state["phase1_tested_candidates"]:
        state["phase1_tested_candidates"].append(candidate)

    if is_match:
        state["phase1_match_found"] = True

    save_state(state)

    return jsonify({
        "success": True,
        "candidate": candidate,
        "candidate_hash": candidate_hash,
        "target_hash": PHASE1["hash"],
        "is_match": is_match,
        "message": "HASH MATCH — credential confirmed." if is_match else "No match. Continue testing."
    })


@app.route("/phase2_toggle_row", methods=["POST"])
def phase2_toggle_row():
    state = get_state()

    if state["progress"] != 2:
        return jsonify({"success": False, "message": "Phase 2 is not active."})

    data = request.get_json(silent=True) or {}
    row_id = data.get("row_id")

    if not isinstance(row_id, int):
        return jsonify({"success": False, "message": "Invalid row id."})

    selected = state["phase2_selected_rows"]

    if row_id in selected:
        selected.remove(row_id)
    else:
        selected.append(row_id)

    selected.sort()

    state["phase2_analysis_unlocked"] = selected == PHASE2_CORRECT_ROW_IDS
    save_state(state)

    return jsonify({
        "success": True,
        "selected_rows": selected,
        "analysis_unlocked": state["phase2_analysis_unlocked"],
        "message": "Breach pattern confirmed — submit the attacker IP and username." if state["phase2_analysis_unlocked"] else "Selection updated."
    })


@app.route("/phase3_decode", methods=["POST"])
def phase3_decode():
    state = get_state()

    if state["progress"] != 3:
        return jsonify({"success": False, "message": "Phase 3 is not active."})

    data = request.get_json(silent=True) or {}
    method = str(data.get("method", "")).strip().lower()

    output = ""
    is_correct = False

    if method == "base64":
        output = base64.b64decode(PHASE3_ENCODED.encode()).decode()
        is_correct = True
        state["phase3_correct_method_found"] = True
    elif method in PHASE3_WRONG_OUTPUTS:
        output = PHASE3_WRONG_OUTPUTS[method]
    else:
        output = "Decoder error: unsupported method."

    already_tried = any(a["method"] == method for a in state["phase3_decode_attempts"])
    if not already_tried:
        state["phase3_decode_attempts"].append({
            "method": method,
            "output": output,
            "is_correct": is_correct
        })

    save_state(state)

    return jsonify({
        "success": True,
        "method": method,
        "output": output,
        "is_correct": is_correct,
        "correct_method_found": state["phase3_correct_method_found"]
    })


@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    state = get_state()
    progress = state["progress"]
    total = len(CHALLENGES)

    if progress > total:
        return jsonify({"success": True, "message": "Vault already breached.", "completed": True})

    data = request.get_json(silent=True) or {}
    answer = str(data.get("answer", "")).strip().lower()
    challenge = CHALLENGES[progress]
    correct = challenge["answer"].strip().lower()

    # Phase-specific pre-flight checks
    if progress == 1 and not state["phase1_match_found"]:
        return jsonify({
            "success": False,
            "message": "You haven't confirmed a hash match yet. Test your candidates first.",
            "completed": False
        })

    if progress == 2 and not state["phase2_analysis_unlocked"]:
        return jsonify({
            "success": False,
            "message": "Incorrect row selection. Identify the full breach sequence before submitting.",
            "completed": False
        })

    if progress == 3 and not state["phase3_correct_method_found"]:
        return jsonify({
            "success": False,
            "message": "The message hasn't been decoded yet. Try all available methods.",
            "completed": False
        })

    if answer != correct:
        # Format hint for Phase 2
        if progress == 2 and "|" not in answer:
            return jsonify({
                "success": False,
                "message": "Format error — use: AttackerIP|username (pipe character, no spaces).",
                "completed": False
            })
        # Length hint for Phase 4 on second wrong attempt
        if progress == 4:
            state["phase4_wrong_attempts"] = state.get("phase4_wrong_attempts", 0) + 1
            save_state(state)
            if state["phase4_wrong_attempts"] >= 2:
                return jsonify({
                    "success": False,
                    "message": "Wrong code. Fragments in phase order, then password length. Recount your characters.",
                    "completed": False
                })
        return jsonify({
            "success": False,
            "message": "Incorrect — review the task brief and try again.",
            "completed": False
        })

    # Correct
    state["phase_answers"][f"phase_{progress}"] = challenge["answer"]

    if challenge["vault_fragment"]:
        state["vault_fragments"].append(challenge["vault_fragment"])

    state["progress"] = progress + 1
    save_state(state)

    if state["progress"] > total:
        return jsonify({
            "success": True,
            "message": "ACCESS GRANTED — VAULT OPENED",
            "completed": True
        })

    return jsonify({
        "success": True,
        "message": "Correct — next phase unlocked.",
        "completed": False
    })


@app.route("/reset", methods=["POST"])
def reset():
    session["game_state"] = get_initial_state()
    return jsonify({"success": True, "message": "Game reset."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)