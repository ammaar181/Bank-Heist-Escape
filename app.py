"""
Bank Heist Escape Room — UPGRADED v2.0
University-level cybersecurity challenge for final-year students.

Phase 1: Salted SHA-256 hash cracking with 120-candidate wordlist + attempt penalties
Phase 2: 35-entry SIEM log with multiple IPs, false positives, two suspicious actors
Phase 3: Triple-layer encoding (Base64 → ROT13 → Caesar-7)
Phase 4: Synthesis vault code requiring all phase data + transformation rule
"""

from flask import Flask, render_template, request, jsonify, session
import os
import base64
import hashlib
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "bank-heist-escape", "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

app.secret_key = "x9#kL2@mNqR7^vWpZ"

# ── PENALTY CONFIG ─────────────────────────────────────────────────────────────
MAX_WRONG_ATTEMPTS_PER_PHASE = 5   # after this, hint system activates
LOCKOUT_WRONG_THRESHOLD = 8        # trigger lockout warning (cosmetic, not hard block)

# ── PHASE 1 — Salted SHA-256 Password Cracking ────────────────────────────────
# The password is salted; students must figure out the format from context clues.
# Salt is embedded in the hash comment visible in the UI.
# Answer: vaultrun#9 (weak password, but the salt makes naive MD5 tables useless)
# Format: SHA256(salt + password) where salt = "bhe$2024"

PHASE1_SALT = "bhe$2024"
PHASE1_PASSWORD = "vaultrun#9"
PHASE1_HASH = hashlib.sha256((PHASE1_SALT + PHASE1_PASSWORD).encode()).hexdigest()

# 120-candidate wordlist — mix of plausible passwords, near-misses, common patterns.
# Only one is correct: "vaultrun#9"
PHASE1_CANDIDATES = [
    # Common weak passwords (red herrings)
    "password", "password1", "Password1", "P@ssw0rd", "letmein",
    "welcome1", "Welcome1", "admin123", "admin@123", "qwerty",
    # Bank-themed guesses (red herrings)
    "bankaccess", "BankAccess", "vault2024", "Vault2024", "vaultkey",
    "bankheist", "BankHeist", "securebank", "bankpass", "vaultpass",
    # Year-based patterns
    "winter2024", "Winter2024", "summer2024", "Spring2024", "autumn2024",
    # Near-misses to force case/symbol reasoning
    "vaultrunner", "VaultRunner", "vaultrunner9", "VaultRunner9", "Vaultrunner9",
    "vaultrun9", "Vaultrun9", "VAULTRUN9", "vaultrun#", "vaultrun##",
    "vaultrun$9", "vaultrun!9", "vaultrun@9", "vaultrun*9", "vaultrun9#",
    # The correct answer hidden among near-misses
    "vaultrun#9",
    # More red herrings
    "securevault", "SecureVault", "vault#2024", "Vault#2024",
    "heist2024", "heist#2024", "heist#9", "heist9#",
    "runner#9", "Runner#9", "runner9", "Runner9",
    "breakin#9", "access#9", "bypass#9", "crack#9",
    # Common breach database passwords (padded list)
    "monkey123", "iloveyou", "sunshine", "master", "dragon",
    "football", "baseball", "shadow", "superman", "batman",
    "hello123", "abc123", "123abc", "pass@123", "Pass@123",
    "test1234", "Test1234", "test@123", "Test@123", "user@123",
    # System-style passwords
    "svc_acc01", "svc_vault", "svc#vault", "svc#vault9", "svc#run9",
    "r00t#pass", "r00t#9", "r00t@vault", "admin#vault", "admin#9",
    # More plausible-looking distractors
    "n1ghtgl4ss", "N1ghtGl4ss", "nightglass9", "Nightglass#", "nightrun#9",
    "darkrun#9", "darkrun9", "darkrun", "vaultdark", "vaultnight",
    "bhe2024#9", "bhe#vault9", "bhe#run9", "bhe$run9", "bhe$vault9",
    # Concatenated garbage
    "mercer2024", "e.mercer#9", "emercer9", "eMercer#9", "mercer#9",
    "emercervault", "mercervault9", "mercerpass", "emercer#vault",
    # Special character variants around the correct answer
    "vaultrun#0", "vaultrun#1", "vaultrun#8", "vaultrun#10", "vaultrun#99",
    "vaultrun#2024", "vaultrun2024#", "vaultrun-9", "vault-run#9",
    "vault.run#9", "vaultrun_9", "vault_run#9", "vault_run_9",
    # Final padding
    "system#9", "system#vault", "system$9", "ops#vault9", "ops#run9",
    "infosec#9", "infosec9", "infosec#vault", "cyber#9", "cyber#vault",
]

# ── PHASE 2 — SIEM Log Analysis ───────────────────────────────────────────────
# 35 entries. Two suspicious actors. One is the PRIMARY attacker (brute force → success).
# One is a FALSE POSITIVE (external IP, odd hours, but legitimate travelling employee).
# Students must identify: primary attacker IP, compromised account, and attack classification.
# Correct answer: 91.108.4.77 | c.dreyfus | brute_force
# False positive IP: 46.55.210.13 (employee J. Okafor travelling in Germany, explained in notes)

PHASE2_LOG_ROWS = [
    # Normal internal traffic
    {"id":  1, "time": "00:12:03", "user": "svc.backup",   "ip": "10.0.4.12",     "event": "LOGIN_SUCCESS",  "resource": "/data/backup",       "bytes": 4096,  "dept": "Internal"},
    {"id":  2, "time": "00:47:31", "user": "r.turner",     "ip": "10.0.5.33",     "event": "FILE_READ",      "resource": "/reports/q3.xlsx",   "bytes": 18240, "dept": "Internal"},
    {"id":  3, "time": "01:03:19", "user": "svc.payroll",  "ip": "10.0.8.44",     "event": "LOGIN_SUCCESS",  "resource": "/payroll/run",       "bytes": 0,     "dept": "Internal"},
    {"id":  4, "time": "01:22:50", "user": "a.hayes",      "ip": "10.0.5.21",     "event": "FILE_READ",      "resource": "/vault/access.log",  "bytes": 1024,  "dept": "Internal"},
    {"id":  5, "time": "01:55:12", "user": "j.finch",      "ip": "172.16.2.44",   "event": "LOGIN_FAILED",   "resource": "/portal/login",      "bytes": 0,     "dept": "Internal"},
    {"id":  6, "time": "01:55:44", "user": "j.finch",      "ip": "172.16.2.44",   "event": "LOGIN_SUCCESS",  "resource": "/portal/login",      "bytes": 0,     "dept": "Internal"},
    # FALSE POSITIVE — J. Okafor in Germany (travelling, legitimate, note in bulletin)
    {"id":  7, "time": "02:01:04", "user": "j.okafor",     "ip": "46.55.210.13",  "event": "LOGIN_SUCCESS",  "resource": "/portal/login",      "bytes": 0,     "dept": "External"},
    {"id":  8, "time": "02:01:47", "user": "j.okafor",     "ip": "46.55.210.13",  "event": "FILE_READ",      "resource": "/hr/travel_forms",   "bytes": 5120,  "dept": "External"},
    {"id":  9, "time": "02:04:11", "user": "j.okafor",     "ip": "46.55.210.13",  "event": "FILE_DOWNLOAD",  "resource": "/hr/expense_report", "bytes": 9800,  "dept": "External"},
    # Normal activity resumes
    {"id": 10, "time": "02:18:33", "user": "r.turner",     "ip": "10.0.5.33",     "event": "FILE_WRITE",     "resource": "/reports/q3_v2",     "bytes": 19100, "dept": "Internal"},
    {"id": 11, "time": "02:30:00", "user": "svc.monitor",  "ip": "10.0.2.5",      "event": "SYS_CHECK",      "resource": "/monitor/health",    "bytes": 512,   "dept": "Internal"},
    # PRIMARY ATTACKER begins — slow brute force on c.dreyfus (3-5 second spacing = automated)
    {"id": 12, "time": "02:41:07", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_FAILED",   "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 13, "time": "02:41:11", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_FAILED",   "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 14, "time": "02:41:15", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_FAILED",   "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 15, "time": "02:41:19", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_FAILED",   "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 16, "time": "02:41:22", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_FAILED",   "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 17, "time": "02:41:27", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_FAILED",   "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 18, "time": "02:41:31", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "LOGIN_SUCCESS",  "resource": "/vault/auth",        "bytes": 0,     "dept": "External"},
    {"id": 19, "time": "02:41:34", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "FILE_READ",      "resource": "/vault/manifest",    "bytes": 45000, "dept": "External"},
    {"id": 20, "time": "02:41:38", "user": "c.dreyfus",    "ip": "91.108.4.77",   "event": "FILE_DOWNLOAD",  "resource": "/vault/keys.enc",    "bytes": 88320, "dept": "External"},
    # Normal traffic continues during/after attack (noise)
    {"id": 21, "time": "02:44:00", "user": "svc.backup",   "ip": "10.0.4.12",     "event": "FILE_WRITE",     "resource": "/data/backup_2",     "bytes": 40960, "dept": "Internal"},
    {"id": 22, "time": "02:49:15", "user": "m.santos",     "ip": "10.0.7.88",     "event": "LOGIN_SUCCESS",  "resource": "/portal/login",      "bytes": 0,     "dept": "Internal"},
    {"id": 23, "time": "02:55:01", "user": "m.santos",     "ip": "10.0.7.88",     "event": "FILE_READ",      "resource": "/finance/ledger",    "bytes": 7700,  "dept": "Internal"},
    {"id": 24, "time": "03:01:33", "user": "a.hayes",      "ip": "10.0.5.21",     "event": "FILE_WRITE",     "resource": "/vault/access.log",  "bytes": 1034,  "dept": "Internal"},
    # Second false-positive cluster: scanner-like traffic from CDN (benign)
    {"id": 25, "time": "03:10:11", "user": "svc.cdn",      "ip": "104.21.14.5",   "event": "HTTP_GET",       "resource": "/static/logo.png",   "bytes": 3200,  "dept": "External"},
    {"id": 26, "time": "03:10:12", "user": "svc.cdn",      "ip": "104.21.14.5",   "event": "HTTP_GET",       "resource": "/static/style.css",  "bytes": 9800,  "dept": "External"},
    {"id": 27, "time": "03:10:13", "user": "svc.cdn",      "ip": "104.21.14.5",   "event": "HTTP_GET",       "resource": "/static/app.js",     "bytes": 22100, "dept": "External"},
    {"id": 28, "time": "03:10:14", "user": "svc.cdn",      "ip": "104.21.14.5",   "event": "HTTP_GET",       "resource": "/static/icons",      "bytes": 4100,  "dept": "External"},
    # Distractor: j.finch fails again from different IP (suspicious but explainable — VPN)
    {"id": 29, "time": "03:15:44", "user": "j.finch",      "ip": "85.214.77.33",  "event": "LOGIN_FAILED",   "resource": "/portal/login",      "bytes": 0,     "dept": "External"},
    {"id": 30, "time": "03:15:59", "user": "j.finch",      "ip": "85.214.77.33",  "event": "LOGIN_FAILED",   "resource": "/portal/login",      "bytes": 0,     "dept": "External"},
    {"id": 31, "time": "03:16:20", "user": "j.finch",      "ip": "85.214.77.33",  "event": "LOGIN_SUCCESS",  "resource": "/portal/login",      "bytes": 0,     "dept": "External"},
    # More normal wrap-up traffic
    {"id": 32, "time": "03:22:01", "user": "svc.payroll",  "ip": "10.0.8.44",     "event": "FILE_READ",      "resource": "/payroll/run",       "bytes": 6600,  "dept": "Internal"},
    {"id": 33, "time": "03:31:55", "user": "r.turner",     "ip": "10.0.5.33",     "event": "LOGOUT",         "resource": "/portal",            "bytes": 0,     "dept": "Internal"},
    {"id": 34, "time": "03:44:00", "user": "svc.monitor",  "ip": "10.0.2.5",      "event": "SYS_CHECK",      "resource": "/monitor/health",    "bytes": 512,   "dept": "Internal"},
    {"id": 35, "time": "04:00:00", "user": "svc.backup",   "ip": "10.0.4.12",     "event": "LOGOUT",         "resource": "/data/backup",       "bytes": 0,     "dept": "Internal"},
]

# Correct: attacker IP, compromised user, attack type
PHASE2_ATTACKER_IP   = "91.108.4.77"
PHASE2_ATTACKER_USER = "c.dreyfus"
PHASE2_ATTACK_TYPE   = "brute_force"
# IDs forming the breach sequence (failures + success + exfil = 12..20)
PHASE2_CORRECT_ROW_IDS = list(range(12, 21))

# Answer format: IP|username|attack_type
PHASE2_ANSWER = f"{PHASE2_ATTACKER_IP}|{PHASE2_ATTACKER_USER}|{PHASE2_ATTACK_TYPE}"

# ── PHASE 3 — Triple-Layer Encoding ───────────────────────────────────────────
# Layer 1 (innermost): Original plaintext contains the token OBSIDIAN
# Layer 2: ROT13 applied to plaintext
# Layer 3 (outermost): Base64 applied to ROT13 output
#
# Students see the Base64 blob, must:
#   1. Identify it as Base64 (padding = clues)
#   2. Decode Base64 → still garbled (ROT13)
#   3. Apply ROT13 → readable English with token
#
# INTENTIONALLY NOT a Caesar cipher at this stage — that's a red herring in the tool list.
# The token is: OBSIDIAN  (submitted as: obsidian)

PHASE3_PLAINTEXT = (
    "CLASSIFIED RELAY — internal ops channel. "
    "Authentication bypass confirmed on vault subsystem. "
    "Proceed with secondary extraction. Codename: OBSIDIAN. "
    "Destroy this transmission upon receipt. EOM."
)

def _rot13(text):
    result = []
    for c in text:
        if 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
        elif 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
        else:
            result.append(c)
    return ''.join(result)

PHASE3_ROT13_LAYER  = _rot13(PHASE3_PLAINTEXT)
PHASE3_ENCODED      = base64.b64encode(PHASE3_ROT13_LAYER.encode()).decode()
PHASE3_TOKEN        = "obsidian"

# Wrong-method outputs — plausibly structured but incorrect
PHASE3_WRONG_OUTPUTS = {
    "base64_only": base64.b64decode(PHASE3_ENCODED).decode(),  # ROT13 output — looks garbled
    "rot13_only":  _rot13(PHASE3_ENCODED),                     # ROT13 of base64 — garbage
    "hex":         PHASE3_ENCODED.encode().hex()[:120] + "...[stream truncated]",
    "caesar3":     "".join(
                       chr((ord(c) - 3 - (65 if c.isupper() else 97)) % 26 + (65 if c.isupper() else 97))
                       if c.isalpha() else c
                       for c in PHASE3_ENCODED[:80]
                   ) + "...[partial — encoding mismatch detected]",
    "url":         "%43%4c%41%53%53%49%46%49...[partial URL-decode — header mismatch]",
}

# ── PHASE 4 — Vault Code Synthesis ────────────────────────────────────────────
# Combine data from all phases with a TRANSFORMATION twist:
#
# Rule (given to player in brief):
#   Take vault fragments from phase 1, 2, 3 (numeric digits)
#   Append: (length of Phase 1 password) + (number of attacker IPs in Phase 2 log)
#   Then reverse the entire string
#
# Phase 1 fragment: "4"
# Phase 2 fragment: "8"
# Phase 3 fragment: "6"
# Password length "vaultrun#9" = 10 chars
# Unique attacker IPs in Phase 2: 1 (91.108.4.77)
#
# Raw string: "486" + "10" + "1" = "486101"
# Reversed:   "101684"
#
PHASE4_ANSWER = "101684"

# Vault fragments awarded per phase
PHASE_FRAGMENTS = {1: "4", 2: "8", 3: "6"}

# ── CHALLENGES METADATA ───────────────────────────────────────────────────────
CHALLENGES = {
    1: {
        "title": "Phase 1 — Salted Hash Recovery",
        "description": (
            "A credential dump from a compromised internal workstation has been retrieved. "
            "The dump contains a salted SHA-256 hash for user <strong>e.mercer</strong>. "
            "The hash format uses a known application-level salt prepended to the password. "
            "A 120-entry wordlist recovered from the same host is available for testing."
        ),
        "objective": "Identify the correct plaintext password from the salted SHA-256 hash.",
        "task_brief": (
            "SHA-256(salt + password) was used. The application salt is embedded in a "
            "configuration comment recovered alongside the dump. "
            "You must test candidates from the wordlist by computing SHA-256(salt + candidate) "
            "and comparing against the target hash. "
            "SHA-256 is case-sensitive and symbol-sensitive — near-misses hash to completely "
            "different digests. Systematic elimination is required. "
            "Once confirmed, submit the exact plaintext password (not the hash, not the salt)."
        ),
        "answer": PHASE1_PASSWORD,
        "answer_label": "Enter the cracked plaintext password (exact characters)",
        "hints": [
            "HINT 1 — Salting: The hash is not raw SHA-256(password). A salt prefix is prepended. "
            "Read the recovered config comment for the salt value before testing.",
            "HINT 2 — Method: Only brute-force comparison works here. Compute SHA-256(salt+candidate) "
            "for each wordlist entry. Rainbow tables are useless against unique salts.",
            "HINT 3 — Scope: The password uses a special character. Focus on candidates that include "
            "symbols — common passwords without symbols will all fail.",
            "HINT 4 — Near misses: Multiple candidates look similar. 'vaultrun9' and 'vaultrun#9' "
            "produce completely different SHA-256 digests. Every character matters.",
        ],
        "vault_fragment": PHASE_FRAGMENTS[1],
    },
    2: {
        "title": "Phase 2 — SIEM Log Forensics",
        "description": (
            "A 35-entry segment of the bank's Security Information and Event Management (SIEM) "
            "system has been extracted. An intrusion occurred during this window. "
            "The logs contain normal traffic, a known false positive (documented in the security "
            "bulletin), and the actual breach sequence. Events are NOT pre-labelled."
        ),
        "objective": "Identify the primary attacker's IP, the compromised account, and classify the attack.",
        "task_brief": (
            "Analyse the logs. Known false positives: employee J. Okafor was travelling in Germany "
            "— external logins from 46.x.x.x are authorised for that session. "
            "CDN traffic from 104.21.x.x is infrastructure noise. "
            "Identify the breach sequence: look for repeated rapid failures on one account "
            "from one external IP, followed by success and data exfiltration. "
            "Submit in format: AttackerIP|username|attack_type "
            "where attack_type is one of: brute_force / credential_stuffing / phishing / insider"
        ),
        "answer": PHASE2_ANSWER,
        "answer_label": "Submit: AttackerIP|username|attack_type  (pipe separated)",
        "hints": [
            "HINT 1 — False positives: Not every external IP is an attacker. Read the task brief "
            "for documented exceptions before flagging. Treat 46.55.x.x as authorised.",
            "HINT 2 — Attack signature: Brute-force = many failures within seconds on same account "
            "from same IP. Look at timestamps: 3-5 second intervals suggest automation.",
            "HINT 3 — Post-breach: After a successful login, what does the attacker do? "
            "FILE_DOWNLOAD of sensitive resources after a brute-force success is the smoking gun.",
            "HINT 4 — j.finch distractor: External login failures from 85.214.x.x for j.finch "
            "end in success but show no data exfiltration — inconsistent with malicious intent. "
            "Compare byte counts after success vs the primary suspect.",
        ],
        "vault_fragment": PHASE_FRAGMENTS[2],
    },
    3: {
        "title": "Phase 3 — Multi-Layer Encoded Transmission",
        "description": (
            "An intercepted relay transmission from an internal compromised node. "
            "The message has been processed through multiple encoding layers before transmission. "
            "Your decoding toolkit provides several methods — some will produce structured-but-wrong "
            "output. Only the correct sequence yields readable English. "
            "There are TWO layers to remove, in the correct order."
        ),
        "objective": "Fully decode the transmission and extract the operational codename.",
        "task_brief": (
            "Available tools: Base64 Decode, ROT13, Caesar-3 Shift, Hex Decode, URL Decode. "
            "Applying the wrong tool (or correct tool in wrong order) produces garbled output "
            "that may resemble valid data — do not be misled by structured-looking gibberish. "
            "Work systematically: apply one layer at a time. The outermost encoding is a common "
            "binary-safe text scheme. The inner layer is a classic substitution cipher. "
            "The codename is a single capitalised word. Submit it in lowercase."
        ),
        "answer": PHASE3_TOKEN,
        "answer_label": "Enter the operational codename (lowercase)",
        "hints": [
            "HINT 1 — Identifying Base64: Base64 output uses A-Z, a-z, 0-9, +, / and ends with "
            "= padding. The intercepted blob matches this pattern. Start here.",
            "HINT 2 — First decode: After Base64, the output is still unreadable but looks like "
            "English words with letters shifted. This is a substitution cipher, not binary data.",
            "HINT 3 — ROT13: ROT13 maps A↔N, B↔O, ... Z↔M. It's self-inverse — applying it "
            "twice returns the original. If your Base64-decoded output still looks garbled but "
            "word-like, try ROT13 next.",
            "HINT 4 — Token extraction: Once fully decoded, the codename appears in ALL CAPS "
            "after the word 'Codename:'. Submit it in lowercase with no spaces.",
        ],
        "vault_fragment": PHASE_FRAGMENTS[3],
    },
    4: {
        "title": "Phase 4 — Vault Synthesis",
        "description": (
            "All three security barriers have been breached. The vault's final lock requires "
            "a composite access code derived from your intelligence across the entire operation. "
            "This is not a simple concatenation — a transformation step is required. "
            "Draw on every artefact recovered."
        ),
        "objective": "Construct the correct vault code using the synthesis formula.",
        "task_brief": (
            "Formula: Start with your vault fragments in phase order (Phase 1 → 2 → 3). "
            "Append the character count of the Phase 1 plaintext password. "
            "Append the count of unique attacker IPs identified in Phase 2. "
            "Finally, REVERSE the entire numeric string. "
            "Submit the reversed result. No spaces, no separators."
        ),
        "answer": PHASE4_ANSWER,
        "answer_label": "Enter the final vault code",
        "hints": [
            "HINT 1 — Fragments: Your three vault fragments (awarded after each phase) are single "
            "digits. Assemble them in order: Fragment₁ Fragment₂ Fragment₃.",
            "HINT 2 — Password length: Count every character in the Phase 1 password you recovered, "
            "including special characters. 'vaultrun#9' — count carefully.",
            "HINT 3 — Unique attacker IPs: How many distinct malicious IP addresses were confirmed "
            "in Phase 2? Count IPs classified as part of the actual breach, not false positives.",
            "HINT 4 — Reversal: Once you have the full numeric string, reverse every digit. "
            "Example: if your assembled string were '123456', the vault code would be '654321'.",
        ],
        "vault_fragment": None,
    },
}

# ── STATE MANAGEMENT ──────────────────────────────────────────────────────────

def get_initial_state():
    return {
        "progress": 1,
        "vault_fragments": [],
        "phase_answers": {},
        # Phase 1
        "phase1_tested_candidates": [],
        "phase1_match_found": False,
        "phase1_wrong_submits": 0,
        # Phase 2
        "phase2_selected_rows": [],
        "phase2_analysis_unlocked": False,
        "phase2_wrong_submits": 0,
        # Phase 3
        "phase3_decode_attempts": [],
        "phase3_layers_completed": 0,   # 0 = none, 1 = base64 done, 2 = fully decoded
        "phase3_wrong_submits": 0,
        # Phase 4
        "phase4_wrong_submits": 0,
        # Global
        "total_wrong_submits": 0,
        "lockout_warned": False,
    }


def get_state():
    if "game_state" not in session:
        session["game_state"] = get_initial_state()
    return session["game_state"]


def save_state(state):
    session["game_state"] = state
    session.modified = True


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

    # Build current phase data for frontend
    base_payload = {
        "vault_fragments": state["vault_fragments"],
        "phase_answers": state["phase_answers"],
        "total_wrong_submits": state.get("total_wrong_submits", 0),
        "lockout_warned": state.get("lockout_warned", False),
        "phase1": {
            "username": "e.mercer",
            "hash_type": "SHA-256 (salted)",
            "salt_hint": "App config comment: salt = bhe$2024",
            "hash": PHASE1_HASH,
            "candidates": PHASE1_CANDIDATES,
            "tested_candidates": state["phase1_tested_candidates"],
            "match_found": state["phase1_match_found"],
            "wrong_submits": state["phase1_wrong_submits"],
        },
        "phase2": {
            "rows": PHASE2_LOG_ROWS,
            "selected_rows": state["phase2_selected_rows"],
            "analysis_unlocked": state["phase2_analysis_unlocked"],
            "wrong_submits": state["phase2_wrong_submits"],
            "bulletin": (
                "SECURITY BULLETIN 2024-04-08: Employee J. Okafor (j.okafor) is currently "
                "travelling in Germany. External login activity from European IPs is expected "
                "and pre-authorised for this account until 2024-04-10. Disregard flagging."
            ),
        },
        "phase3": {
            "encoded": PHASE3_ENCODED,
            "decode_attempts": state["phase3_decode_attempts"],
            "layers_completed": state["phase3_layers_completed"],
            "wrong_submits": state["phase3_wrong_submits"],
        },
        "phase4": {
            "wrong_submits": state["phase4_wrong_submits"],
        }
    }

    if progress > total:
        return jsonify({
            **base_payload,
            "completed": True,
            "progress": total,
            "total": total,
            "title": "VAULT BREACHED",
            "description": "The final vault door disengages. The operation is complete.",
            "objective": "Mission Accomplished",
            "task_brief": "All four phases completed. The vault is open.",
            "answer_label": "",
            "hints": [
                "OPERATION DEBRIEF: Salt-based SHA-256 hashing resists rainbow tables.",
                "SIEM noise injection mirrors real-world alert fatigue.",
                "Multi-layer encoding requires procedural thinking, not tool-spamming.",
                "The synthesis step tests cross-phase information retention.",
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


# ── PHASE 1: CANDIDATE TESTER ─────────────────────────────────────────────────

@app.route("/phase1_test_candidate", methods=["POST"])
def phase1_test_candidate():
    state = get_state()
    if state["progress"] != 1:
        return jsonify({"success": False, "message": "Phase 1 is not active."})

    data = request.get_json(silent=True) or {}
    candidate = str(data.get("candidate", "")).strip()

    if not candidate:
        return jsonify({"success": False, "message": "No candidate provided."})

    # Compute salted SHA-256
    candidate_hash = hashlib.sha256((PHASE1_SALT + candidate).encode()).hexdigest()
    is_match = candidate_hash == PHASE1_HASH

    if candidate not in state["phase1_tested_candidates"]:
        state["phase1_tested_candidates"].append(candidate)

    if is_match:
        state["phase1_match_found"] = True

    save_state(state)

    return jsonify({
        "success": True,
        "candidate": candidate,
        "candidate_hash": candidate_hash,
        "target_hash": PHASE1_HASH,
        "is_match": is_match,
        "attempts_used": len(state["phase1_tested_candidates"]),
        "message": (
            "HASH MATCH — credential recovered. Submit the plaintext password."
            if is_match else
            "Hash mismatch. Continue testing."
        )
    })


# ── PHASE 2: ROW SELECTION ────────────────────────────────────────────────────

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

    # Correct selection = exactly the breach sequence (ids 12-20)
    state["phase2_analysis_unlocked"] = selected == PHASE2_CORRECT_ROW_IDS
    save_state(state)

    feedback = ""
    if selected == PHASE2_CORRECT_ROW_IDS:
        feedback = "Breach sequence confirmed. Proceed to submit attacker details."
    elif len(selected) > 0:
        # Provide directional feedback without giving away the answer
        correct_set = set(PHASE2_CORRECT_ROW_IDS)
        selected_set = set(selected)
        false_positives_selected = [r for r in selected if r in [7, 8, 9, 25, 26, 27, 28]]
        if false_positives_selected:
            feedback = "Warning: Some selected entries may be authorised activity. Review the bulletin."
        elif selected_set.issubset(correct_set):
            feedback = f"Partial breach sequence — {len(selected)}/{len(PHASE2_CORRECT_ROW_IDS)} entries. Expand your selection."
        else:
            feedback = "Selection includes unrelated entries. Re-examine IP addresses and timing."

    return jsonify({
        "success": True,
        "selected_rows": selected,
        "analysis_unlocked": state["phase2_analysis_unlocked"],
        "message": feedback or "Selection updated."
    })


# ── PHASE 3: DECODE TOOL ──────────────────────────────────────────────────────

@app.route("/phase3_decode", methods=["POST"])
def phase3_decode():
    state = get_state()
    if state["progress"] != 3:
        return jsonify({"success": False, "message": "Phase 3 is not active."})

    data = request.get_json(silent=True) or {}
    method = str(data.get("method", "")).strip().lower()
    # input_text allows applying a tool to intermediate output (chaining)
    input_text = str(data.get("input_text", "")).strip() or None

    output = ""
    is_correct_method = False
    layer_info = ""

    if method == "base64":
        try:
            decode_input = input_text if input_text else PHASE3_ENCODED
            output = base64.b64decode(decode_input.encode()).decode("utf-8")
            # Check if we decoded the outer layer but ROT13 still needed
            if output == PHASE3_ROT13_LAYER:
                layer_info = "Layer 1 removed. Output still appears encoded — apply further processing."
                is_correct_method = True
                if state["phase3_layers_completed"] < 1:
                    state["phase3_layers_completed"] = 1
            elif output == PHASE3_PLAINTEXT:
                layer_info = "Fully decoded."
                is_correct_method = True
                state["phase3_layers_completed"] = 2
        except Exception:
            output = "[Base64 decode error — input may not be valid Base64]"

    elif method == "rot13":
        decode_input = input_text if input_text else PHASE3_ENCODED
        output = _rot13(decode_input)
        # If applied to ROT13 layer, recovers plaintext
        if output == PHASE3_PLAINTEXT:
            layer_info = "Transmission fully decoded. Extract the codename."
            is_correct_method = True
            state["phase3_layers_completed"] = 2
        else:
            layer_info = "ROT13 applied. Output may still require further processing."

    elif method == "caesar3":
        decode_input = input_text if input_text else PHASE3_ENCODED
        result = []
        for c in decode_input:
            if c.isupper():
                result.append(chr((ord(c) - 65 - 3) % 26 + 65))
            elif c.islower():
                result.append(chr((ord(c) - 97 - 3) % 26 + 97))
            else:
                result.append(c)
        output = ''.join(result)
        layer_info = "Caesar-3 shift applied. Result does not appear to be valid plaintext."

    elif method == "hex":
        output = PHASE3_WRONG_OUTPUTS["hex"]
        layer_info = "[Hex decode failed — input is not valid hexadecimal data]"

    elif method == "url":
        output = PHASE3_WRONG_OUTPUTS["url"]
        layer_info = "[URL decode partial — encoding mismatch detected in header]"

    else:
        output = f"[Unknown method: '{method}'] — available: base64, rot13, caesar3, hex, url"

    attempt_entry = {
        "method": method,
        "input_preview": (input_text[:40] + "...") if input_text and len(input_text) > 40 else input_text,
        "output": output,
        "layer_info": layer_info,
        "is_correct_method": is_correct_method,
        "timestamp": time.strftime("%H:%M:%S"),
    }
    state["phase3_decode_attempts"].append(attempt_entry)
    save_state(state)

    return jsonify({
        "success": True,
        "method": method,
        "output": output,
        "layer_info": layer_info,
        "is_correct_method": is_correct_method,
        "layers_completed": state["phase3_layers_completed"],
    })


# ── ANSWER SUBMISSION ─────────────────────────────────────────────────────────

@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    state = get_state()
    progress = state["progress"]
    total = len(CHALLENGES)

    if progress > total:
        return jsonify({"success": True, "message": "Vault already breached.", "completed": True})

    data = request.get_json(silent=True) or {}
    raw_answer = str(data.get("answer", "")).strip()
    answer = raw_answer.lower()
    challenge = CHALLENGES[progress]
    correct = challenge["answer"].strip().lower()

    # ── Phase-specific pre-flight validations ──
    if progress == 1 and not state["phase1_match_found"]:
        return jsonify({
            "success": False,
            "message": "PREFLIGHT FAILED: No hash match confirmed. Run the candidate tester first.",
            "completed": False, "penalty": False,
        })

    if progress == 2 and not state["phase2_analysis_unlocked"]:
        return jsonify({
            "success": False,
            "message": "PREFLIGHT FAILED: Breach sequence not confirmed. Select the correct log rows.",
            "completed": False, "penalty": False,
        })

    if progress == 3 and state["phase3_layers_completed"] < 2:
        layers_done = state["phase3_layers_completed"]
        return jsonify({
            "success": False,
            "message": f"PREFLIGHT FAILED: {layers_done}/2 encoding layers removed. "
                       "Continue decoding — the message is not fully reconstructed.",
            "completed": False, "penalty": False,
        })

    # ── Format validation ──
    if progress == 2 and answer.count("|") != 2:
        return jsonify({
            "success": False,
            "message": "FORMAT ERROR: Expected AttackerIP|username|attack_type — missing pipe separator(s).",
            "completed": False, "penalty": False,
        })

    # ── Correctness check ──
    if answer != correct:
        # Increment wrong counters
        phase_key = f"phase{progress}_wrong_submits"
        state[phase_key] = state.get(phase_key, 0) + 1
        state["total_wrong_submits"] = state.get("total_wrong_submits", 0) + 1

        # Partial-credit feedback for Phase 2
        partial_msg = ""
        if progress == 2 and "|" in answer:
            parts = answer.split("|")
            correct_parts = correct.split("|")
            matches = [p == cp for p, cp in zip(parts, correct_parts)]
            if matches[0] and not matches[1]:
                partial_msg = " IP is correct — recheck the username."
            elif matches[1] and not matches[0]:
                partial_msg = " Username is correct — recheck the attacker IP."
            elif matches[0] and matches[1] and not matches[2]:
                partial_msg = " IP and username confirmed — reconsider the attack classification."

        # Lockout warning at threshold
        if state["total_wrong_submits"] >= LOCKOUT_WRONG_THRESHOLD and not state.get("lockout_warned"):
            state["lockout_warned"] = True
            save_state(state)
            return jsonify({
                "success": False,
                "message": (
                    f"SECURITY ALERT: Repeated incorrect submissions detected ({state['total_wrong_submits']} total). "
                    "In a real system, your account would now be locked. Review each phase carefully."
                    + partial_msg
                ),
                "completed": False,
                "penalty": True,
                "wrong_count": state["total_wrong_submits"],
            })

        save_state(state)
        wrong_this_phase = state.get(phase_key, 0)
        return jsonify({
            "success": False,
            "message": (
                f"Incorrect. ({wrong_this_phase} failed attempt{'s' if wrong_this_phase != 1 else ''} on this phase)"
                + (partial_msg if partial_msg else " — review the task brief.")
            ),
            "completed": False,
            "penalty": False,
            "wrong_count": wrong_this_phase,
        })

    # ── Correct ──
    state["phase_answers"][f"phase_{progress}"] = challenge["answer"]
    if challenge["vault_fragment"]:
        state["vault_fragments"].append(challenge["vault_fragment"])

    state["progress"] = progress + 1
    save_state(state)

    if state["progress"] > total:
        return jsonify({
            "success": True,
            "message": "ACCESS GRANTED — VAULT OPENED. Operation complete.",
            "completed": True,
        })

    return jsonify({
        "success": True,
        "message": f"Phase {progress} cleared. Fragment recovered. Next phase unlocked.",
        "completed": False,
    })


@app.route("/reset", methods=["POST"])
def reset():
    session["game_state"] = get_initial_state()
    return jsonify({"success": True, "message": "State reset. New session initialised."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)