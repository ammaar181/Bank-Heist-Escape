from flask import Flask, render_template, request, jsonify, session
import os
import base64

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
        "crack_completed": False,
        "decode_completed": False,
        "vault_fragments": [],
        "phase_answers": {}
    }


def get_state():
    if "game_state" not in session:
        session["game_state"] = get_initial_state()
    return session["game_state"]


def save_state(state):
    session["game_state"] = state
    session.modified = True


CHALLENGES = {
    1: {
        "title": "Phase 1: Password Cracking",
        "description": "A bank employee reused a weak password. Crack the leaked hash using the wordlist simulator.",
        "objective": "Recover the employee password.",
        "task_brief": (
            "Use the crack simulator to test the leaked wordlist against the employee hash. "
            "Once the password is revealed, submit it to unlock the next layer."
        ),
        "answer": "vaultrunner9",
        "answer_label": "Enter the cracked password",
        "vault_fragment": "7",
        "hints": [
            "You need to run the crack first.",
            "The answer is not shown until a password match is found.",
            "Watch the terminal output carefully."
        ]
    },
    2: {
        "title": "Phase 2: Log Analysis",
        "description": "Security logs show one hostile source probing the bank systems before gaining access.",
        "objective": "Identify the suspicious attacker IP address.",
        "task_brief": (
            "Inspect the authentication logs. Look for repeated failed login attempts followed by a successful breach. "
            "Submit the suspicious IP address."
        ),
        "answer": "185.217.92.14",
        "answer_label": "Enter the suspicious IP",
        "vault_fragment": "3",
        "hints": [
            "Look for a burst of failures before one success.",
            "The attacker IP is not internal bank traffic.",
            "One external address stands out clearly."
        ]
    },
    3: {
        "title": "Phase 3: Encoded Internal Message",
        "description": "An intercepted internal relay message contains the next access clue, but it is encoded.",
        "objective": "Decode the hidden relay token.",
        "task_brief": (
            "Use the in-game decoder on the captured message. Extract the relay token from the decoded text "
            "and submit it as your answer."
        ),
        "answer": "nightglass",
        "answer_label": "Enter the decoded relay token",
        "vault_fragment": "9",
        "hints": [
            "This is encoding, not encryption.",
            "Run the decoder first.",
            "The token appears in readable English after decoding."
        ]
    },
    4: {
        "title": "Phase 4: Final Vault Access",
        "description": "You have reached the core vault terminal. Reassemble the final access code using evidence recovered earlier.",
        "objective": "Construct the final vault code.",
        "task_brief": (
            "Use the three recovered vault fragments in phase order, then append the length of the cracked password "
            "from Phase 1. Submit the final vault code."
        ),
        "answer": "73912",
        "answer_label": "Enter the final vault code",
        "vault_fragment": None,
        "hints": [
            "You already collected everything you need.",
            "Fragments come first, in phase order.",
            "Then append the Phase 1 cracked password length."
        ]
    }
}


CRACK_SIM = {
    "username": "e.mercer",
    "hash_type": "MD5",
    "hash": "6f2ebf3c1f19f8c6e5953e8a0d31a59f",
    "wordlist": [
        "welcome1",
        "banksecure",
        "winter2024",
        "vaultrunner9",
        "letmein123"
    ],
    "correct_password": "vaultrunner9"
}

LOG_ROWS = [
    {"time": "01:11:03", "user": "svc.backup", "ip": "10.0.4.12", "event": "LOGIN_SUCCESS", "status": "Normal"},
    {"time": "01:13:42", "user": "r.turner", "ip": "10.0.5.33", "event": "LOGIN_SUCCESS", "status": "Normal"},
    {"time": "02:44:11", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_FAILED", "status": "Suspicious"},
    {"time": "02:44:16", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_FAILED", "status": "Suspicious"},
    {"time": "02:44:21", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_FAILED", "status": "Suspicious"},
    {"time": "02:44:29", "user": "a.hayes", "ip": "185.217.92.14", "event": "LOGIN_SUCCESS", "status": "Critical"},
    {"time": "03:01:08", "user": "svc.payroll", "ip": "10.0.8.44", "event": "LOGIN_SUCCESS", "status": "Normal"},
    {"time": "03:09:51", "user": "j.finch", "ip": "10.0.6.21", "event": "LOGIN_FAILED", "status": "Normal"}
]

ENCODED_TEXT = base64.b64encode(
    b"Vault relay token: NIGHTGLASS"
).decode("utf-8")


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
            "description": "The final vault door slides open. The bank reserves are exposed.",
            "objective": "Operation Complete",
            "task_brief": "You completed all four phases and breached the vault.",
            "answer_label": "",
            "hints": [
                "Inside Man: Clean job. Grab what you came for and get out.",
                "All security layers have been bypassed."
            ],
            "vault_fragments": state["vault_fragments"],
            "phase_answers": state["phase_answers"]
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
        "crack_completed": state["crack_completed"],
        "decode_completed": state["decode_completed"]
    })


@app.route("/run_crack", methods=["POST"])
def run_crack():
    state = get_state()

    if state["progress"] != 1:
        return jsonify({"success": False, "message": "Password cracking is not active right now."})

    state["crack_completed"] = True
    save_state(state)

    lines = [f"[*] Starting crack for user: {CRACK_SIM['username']}"]
    for word in CRACK_SIM["wordlist"]:
        if word == CRACK_SIM["correct_password"]:
            lines.append(f"[+] trying: {word}")
            lines.append(f"[MATCH FOUND] password = {word}")
            break
        lines.append(f"[-] trying: {word}")

    return jsonify({
        "success": True,
        "lines": lines,
        "password": CRACK_SIM["correct_password"]
    })


@app.route("/get_logs")
def get_logs():
    state = get_state()

    if state["progress"] != 2:
        return jsonify({"success": False, "rows": []})

    event_filter = request.args.get("filter", "ALL").upper()

    if event_filter == "FAILED":
        rows = [r for r in LOG_ROWS if r["event"] == "LOGIN_FAILED"]
    elif event_filter == "SUCCESS":
        rows = [r for r in LOG_ROWS if r["event"] == "LOGIN_SUCCESS"]
    else:
        rows = LOG_ROWS

    return jsonify({"success": True, "rows": rows})


@app.route("/decode_message", methods=["POST"])
def decode_message():
    state = get_state()

    if state["progress"] != 3:
        return jsonify({"success": False, "message": "Decoder is not active right now."})

    state["decode_completed"] = True
    save_state(state)

    decoded = base64.b64decode(ENCODED_TEXT.encode("utf-8")).decode("utf-8")

    return jsonify({
        "success": True,
        "encoded": ENCODED_TEXT,
        "decoded": decoded
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

    if progress == 1 and not state["crack_completed"]:
        return jsonify({
            "success": False,
            "message": "Run the crack simulator before submitting an answer.",
            "completed": False
        })

    if progress == 3 and not state["decode_completed"]:
        return jsonify({
            "success": False,
            "message": "Run the decoder before submitting an answer.",
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
            "completed": True,
            "vault_fragment": challenge["vault_fragment"]
        })

    return jsonify({
        "success": True,
        "message": "Correct — next phase unlocked.",
        "completed": False,
        "vault_fragment": challenge["vault_fragment"]
    })


@app.route("/reset", methods=["POST"])
def reset():
    session["game_state"] = get_initial_state()
    return jsonify({"success": True, "message": "Game reset."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)