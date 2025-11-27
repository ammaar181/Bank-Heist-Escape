from flask import Flask, send_from_directory, jsonify, request, session

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "CHANGE_THIS_TO_SOMETHING_RANDOM_AND_SECRET"

# ======================================================
# PUZZLES: each has a solution (answer) and a separate flag (reward)
# ======================================================

PUZZLES = {
    # 1) RSA (crypto) – button: hash
    "hash": {
        "id": "hash",
        "title": "RSA Entrance Override",
        "type": "hash",
        "description": (
            "The guard encrypted the entrance override code using RSA.\n"
            "Your goal: recover the underlying 4-letter metal word (all caps).\n"
            "Once you have that word, submit it here as the ANSWER (e.g. GOLD).\n"
            "If correct, you will be rewarded with a separate random flag.\n\n"
            "Public key parameters:\n"
            "  n  = 3811776253\n"
            "  e  = 65537\n"
            "Ciphertext:\n"
            "  c  = 1355013865\n"
        ),
        "solution": "GOLD",                       # what they type as answer
        "flag": "FLAG{rsa_door_breach_8f2c}"      # reward flag
    },

    # 2) Punycode phishing – button: phishing
    "phishing": {
        "id": "phishing",
        "title": "Punycode Phishing Alert",
        "type": "phishing",
        "description": (
            "A security alert email claims to come from YourBank.\n"
            "Inspect the URL carefully and analyse what kind of trick is used.\n"
            "Your ANSWER should be a short description such as 'punycode attack'.\n"
            "If you correctly identify the attack, you will be rewarded a flag.\n"
        ),
        "email": (
            "From: security@yourbank.com\n"
            "Subject: IMPORTANT: Verify your account immediately\n\n"
            "Dear customer,\n\n"
            "We detected unusual activity on your account.\n"
            "Please verify your identity using the secure link below:\n\n"
            "  https://www.xn--yourbnk-3ya.com/security/update\n\n"
            "If you do not respond within 24 hours, your account may be locked.\n\n"
            "Sincerely,\n"
            "YourBank Security Team\n"
        ),
        "solution": "punycode attack",                    # or similar phrase
        "flag": "FLAG{punycode_domain_trap_b13}"
    },

    # 3) JS reverse engineering – button: encrypt
    "encrypt": {
        "id": "encrypt",
        "title": "Keypad JavaScript Reverse Engineering",
        "type": "encrypt",
        "description": (
            "The keypad runs a validate(input) function in JavaScript.\n"
            "Reverse the code below to find the ONE input string that passes.\n"
            "Enter that string here as the ANSWER.\n"
            "If correct, you’ll be rewarded with a separate flag.\n"
        ),
        "js_code": (
            "(function(){\n"
            "  const x = atob(\"RkxBR3tyZXZlcnNlX2VuZ19qb3lfY29kZX0=\");\n"
            "  const y = [5,2,1,6,7];\n"
            "  function check(input){\n"
            "    let a=\"\";\n"
            "    for(let i=0;i<input.length;i++){\n"
            "      a += String.fromCharCode(input.charCodeAt(i) ^ y[i % y.length]);\n"
            "    }\n"
            "    return a === x;\n"
            "  }\n"
            "  window.validate = check;\n"
            "})();\n"
        ),
        "solution": "FLAG{reverse_eng_joy_code}",          # what validate expects
        "flag": "FLAG{js_reversed_9ad1}"                   # reward flag
    },

    # 4) PNG forensics – button: logs
    "logs": {
        "id": "logs",
        "title": "Security Camera Image Forensics",
        "type": "logs",
        "description": (
            "A camera snapshot was captured as a PNG file, but the header appears damaged.\n"
            "Below is the corrupted file in Base64 form.\n"
            "Decode it, repair the PNG header, and inspect the image/metadata locally.\n"
            "Your ANSWER is the flag string you recover from the PNG.\n"
            "If correct, you’ll receive a separate reward flag.\n"
        ),
        "png_b64": (
            "AAAAAAAAAAAAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAHnRFWHRmbGFnPUZMQUd7cG5nX2hl\n"
            "YWRlcl9yZXN0b3JlZH35Gtn/AAAADElEQVR4nGNgYGAAAAAEAAH2FzhVAAAAAElFTkSuQmCC\n"
        ),
        "solution": "FLAG{png_header_restored}",           # recovered from image
        "flag": "FLAG{forensic_png_mended_42}"
    },

    # 5) Session ID prediction – button: firewall
    "firewall": {
        "id": "firewall",
        "title": "Session Prediction – Vault Console",
        "type": "firewall",
        "description": (
            "The vault console uses session IDs of the form sess_<number>.\n"
            "From the logs you observed several user sessions:\n\n"
            "  [INFO] user login   session = sess_900010\n"
            "  [INFO] user login   session = sess_900020\n"
            "  [INFO] user login   session = sess_900030\n"
            "  [INFO] your login   session = sess_900040\n\n"
            "The admin login occurs directly after yours.\n"
            "Infer the admin's session ID and enter it here as the ANSWER\n"
            "(e.g. sess_900050). If correct, you will be rewarded a flag.\n"
        ),
        "solution": "sess_900050",                         # NOT printed anywhere
        "flag": "FLAG{session_predicted_7e0a}"
    },
}

# ======================================================
# FLAG STORAGE + VAULT
# ======================================================

def give_flag(flag_str: str):
    flags = session.get("flags", [])
    if flag_str not in flags:
        flags.append(flag_str)
        session["flags"] = flags

@app.route("/api/flags")
def api_flags():
    return jsonify(session.get("flags", []))

@app.route("/api/check_vault")
def api_check_vault():
    flags = session.get("flags", [])
    needed = [p["flag"] for p in PUZZLES.values()]
    opened = all(f in flags for f in needed)
    if opened:
        return jsonify({"opened": True, "final_flag": "FLAG{bank_heist_complete}"})
    else:
        missing = [f for f in needed if f not in flags]
        return jsonify({"opened": False, "missing": missing})

# ======================================================
# BASIC ROUTES (UI stays same)
# ======================================================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/game")
def game():
    return send_from_directory("static", "game.html")

# ======================================================
# PUZZLE API – sends description + artifacts (no solutions/flags)
# ======================================================

@app.route("/api/puzzle/<pid>")
def api_get_puzzle(pid):
    p = PUZZLES.get(pid)
    if not p:
        return jsonify({"error": "not found"}), 404

    data = {
        "id": p["id"],
        "title": p["title"],
        "type": p["type"],
        "description": p["description"],
    }

    if p["id"] == "phishing":
        data["email"] = p["email"]

    if p["id"] == "encrypt":
        data["js_code"] = p["js_code"]

    if p["id"] == "logs":
        data["png_b64"] = p["png_b64"]

    return jsonify(data)

# ======================================================
# ANSWER SUBMISSION – checks solution, REVEALS reward flag
# ======================================================

@app.route("/api/submit_answer/<pid>", methods=["POST"])
def api_submit_answer(pid):
    p = PUZZLES.get(pid)
    if not p:
        return jsonify({"error": "unknown puzzle"}), 404

    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip()

    # simple case-insensitive check for textual answers,
    # exact match for FLAG-like ones.
    sol = p["solution"]
    if sol.startswith("FLAG{"):
        correct = (answer == sol)
    else:
        correct = (answer.lower() == sol.lower())

    if correct:
        # return the reward flag but do NOT auto-register it
        return jsonify({"correct": True, "reward_flag": p["flag"]})
    else:
        return jsonify({"correct": False})

# ======================================================
# FLAG SUBMISSION – player enters flags they’ve earned
# ======================================================

@app.route("/api/submit_flag", methods=["POST"])
def api_submit_flag():
    data = request.get_json(silent=True) or {}
    flag = (data.get("flag") or "").strip()

    # Check against known flags
    valid_flags = {p["flag"]: p_id for p_id, p in PUZZLES.items()}
    if flag in valid_flags:
        already = flag in session.get("flags", [])
        give_flag(flag)
        return jsonify({"valid": True, "already": already, "flag": flag})
    else:
        return jsonify({"valid": False})

# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
