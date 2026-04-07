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
        "phase3_correct_method_found": False
    }


def get_state():
    if "game_state" not in session:
        session["game_state"] = get_initial_state()
    return session["game_state"]


def save_state(state):
    session["game_state"] = state
    session.modified = True


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

PHASE2_LOG_ROWS = [
    {"id": 1, "time": "01:11:03", "user": "svc.backup", "ip": "10.0.4.12", "event": "LOGIN_SUCCESS", "status": "Normal"},
    {"id": 2, "time": "01:13:42", "user": "r.turner", "ip": "10.0.5.33", "event": "LOGIN_SUCCESS", "status": "Normal"},
    {"id": 3, "time": "02:44:11", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_FAILED", "status": "Suspicious"},
    {"id": 4, "time": "02:44:16", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_FAILED", "status": "Suspicious"},
    {"id": 5, "time": "02:44:21", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_FAILED", "status": "Suspicious"},
    {"id": 6, "time": "02:44:29", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_SUCCESS", "status": "Critical"},
    {"id": 7, "time": "02:50:04", "user": "j.finch", "ip": "172.16.2.44", "event": "LOGIN_FAILED", "status": "Normal"},
    {"id": 8, "time": "03:01:08", "user": "svc.payroll", "ip": "10.0.8.44", "event": "LOGIN_SUCCESS", "status": "Normal"},
    {"id": 9, "time": "03:09:51", "user": "j.finch", "ip": "10.0.6.21", "event": "LOGIN_FAILED", "status": "Normal"}
]

PHASE2_CORRECT_ROW_IDS = [3, 4, 5, 6]
PHASE2_CORRECT_IP = "185.217.92.14"
PHASE2_CORRECT_USER = "a.hayes"

PHASE3_ENCODED = base64.b64encode(
    b"Relay archive note: secondary transfer authorised. vault relay token = NIGHTGLASS. destroy after reading."
).decode("utf-8")
PHASE3_CORRECT_METHOD = "base64"
PHASE3_TOKEN = "nightglass"

CHALLENGES = {
    1: {
        "title": "Phase 1: Password Cracking",
        "description": "A leaked employee hash has been recovered. Test candidate passwords against the hash and find the real credential.",
        "objective": "Recover the employee password.",
        "task_brief": (
            "You are not being handed the answer. Use the candidate tester to compare password guesses against the leaked hash. "
            "Only one candidate is a valid match."
        ),
        "answer": "vaultrunner9",
        "answer_label": "Enter the cracked password",
        "vault_fragment": "7",
        "hints": [
            "One candidate has the exact MD5 hash match.",
            "Case matters when hashing.",
            "A near-match is included to catch lazy players."
        ]
    },
    2: {
        "title": "Phase 2: Log Analysis",
        "description": "Authentication logs show one real intrusion sequence hidden among normal traffic and harmless failures.",
        "objective": "Identify the attacker IP and compromised user.",
        "task_brief": (
            "Select the suspicious log rows that form the breach pattern: repeated failed attempts followed by a successful login on the same account. "
            "Then submit both the attacker IP and compromised username."
        ),
        "answer": f"{PHASE2_CORRECT_IP}|{PHASE2_CORRECT_USER}",
        "answer_label": "Enter answer as: IP|username",
        "vault_fragment": "3",
        "hints": [
            "The key pattern is repeated failure followed by success.",
            "The attacker is external, not internal bank traffic.",
            "You need both the IP and the username."
        ]
    },
    3: {
        "title": "Phase 3: Encoded Internal Message",
        "description": "An intercepted internal relay note is encoded. Choose the correct decoder and extract the relay token.",
        "objective": "Recover the relay token.",
        "task_brief": (
            "Test decode methods until the output becomes readable English. "
            "Once decoded, extract the token from the message and submit it."
        ),
        "answer": "nightglass",
        "answer_label": "Enter the relay token",
        "vault_fragment": "9",
        "hints": [
            "This is a common text-safe encoding method.",
            "Wrong decode methods should produce useless output.",
            "The answer is a token inside the decoded sentence, not the whole sentence."
        ]
    },
    4: {
        "title": "Phase 4: Final Vault Access",
        "description": "Use the evidence gathered so far to construct the final vault code.",
        "objective": "Build the final vault code.",
        "task_brief": (
            "Take the three vault fragments in phase order, then append the length of the cracked password from Phase 1. "
            "Submit the combined code."
        ),
        "answer": "73912",
        "answer_label": "Enter the final vault code",
        "vault_fragment": None,
        "hints": [
            "The three fragments come first.",
            "Use phase order.",
            "Then append the Phase 1 password length."
        ]
    }
}


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

    if progress > total:
        return jsonify({
            "completed": True,
            "progress": total,
            "total": total,
            "title": "Vault Entered",
            "description": "The final vault door unlocks and the chamber opens.",
            "objective": "Operation Complete",
            "task_brief": "All four phases were completed successfully.",
            "answer_label": "",
            "hints": [
                "Inside Man: Clean breach. Grab the reserves and disappear.",
                "All security layers bypassed."
            ],
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
        })

    challenge = CHALLENGES[progress]

    return jsonify({
        "completed": False,
        "progress": progress,
        "total": total,
        "title": challenge["title"],
        "description": challenge["description"],
        "objective": challenge["objective"],
        "task_brief": challenge["task_brief"],
        "answer_label": challenge["answer_label"],
        "hints": challenge["hints"],
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
        "is_match": is_match,
        "message": "Hash match found." if is_match else "No match."
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
        "message": "Correct intrusion pattern identified." if state["phase2_analysis_unlocked"] else "Selection updated."
    })


@app.route("/phase3_decode", methods=["POST"])
def phase3_decode():
    state = get_state()

    if state["progress"] != 3:
        return jsonify({"success": False, "message": "Phase 3 is not active."})

    data = request.get_json(silent=True) or {}
    method = str(data.get("method", "")).strip().lower()

    output = ""

    if method == "base64":
        output = base64.b64decode(PHASE3_ENCODED.encode()).decode()
        state["phase3_correct_method_found"] = True
    elif method == "hex":
        output = "5661756c742072656c617920746f6b656e3f3f3f20496e76616c6964207061796c6f6164"
    elif method == "rot13":
        output = "IzSn1ODtpezLtqT9VRAWE0uHE0KOHF="
    else:
        output = "Decoder error: unsupported method."

    state["phase3_decode_attempts"].append({
        "method": method,
        "output": output
    })

    save_state(state)

    return jsonify({
        "success": True,
        "method": method,
        "output": output,
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

    if progress == 1 and not state["phase1_match_found"]:
        return jsonify({
            "success": False,
            "message": "You have not found a valid password match yet.",
            "completed": False
        })

    if progress == 2 and not state["phase2_analysis_unlocked"]:
        return jsonify({
            "success": False,
            "message": "You must first identify the full intrusion pattern in the logs.",
            "completed": False
        })

    if progress == 3 and not state["phase3_correct_method_found"]:
        return jsonify({
            "success": False,
            "message": "You have not decoded the message correctly yet.",
            "completed": False
        })

    if answer != correct:
        return jsonify({
            "success": False,
            "message": "Incorrect answer — try again.",
            "completed": False
        })

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