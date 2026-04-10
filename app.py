from flask import Flask, render_template, request, jsonify, session
import os, base64, hashlib, time
from urllib.parse import unquote as url_unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "bank-heist-escape", "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)
app.secret_key = "x9#kL2@mNqR7^vWpZ"

LOCKOUT_THRESHOLD = 8  # cosmetic lockout warning after this many total wrong submits


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — Salted SHA-256 password recovery
# Hash formula: SHA-256(salt + password)
# Correct answer: vaultrun#9
# ─────────────────────────────────────────────────────────────────────────────

PHASE1_SALT     = "bhe$2024"
PHASE1_PASSWORD = "vaultrun#9"
PHASE1_HASH     = hashlib.sha256((PHASE1_SALT + PHASE1_PASSWORD).encode()).hexdigest()

# 120-candidate wordlist. Exactly one is correct.
# Structure: common weak passwords, bank-themed guesses, near-misses,
# username-derived guesses, special-char variants around the correct answer.
PHASE1_CANDIDATES = [
    "password", "password1", "Password1", "P@ssw0rd", "letmein",
    "welcome1", "Welcome1", "admin123", "admin@123", "qwerty",
    "bankaccess", "BankAccess", "vault2024", "Vault2024", "vaultkey",
    "bankheist", "BankHeist", "securebank", "bankpass", "vaultpass",
    "winter2024", "Winter2024", "summer2024", "Spring2024", "autumn2024",
    "vaultrunner", "VaultRunner", "vaultrunner9", "VaultRunner9", "Vaultrunner9",
    "vaultrun9", "Vaultrun9", "VAULTRUN9", "vaultrun#", "vaultrun##",
    "vaultrun$9", "vaultrun!9", "vaultrun@9", "vaultrun*9", "vaultrun9#",
    "vaultrun#9",   # ← correct
    "securevault", "SecureVault", "vault#2024", "Vault#2024",
    "heist2024", "heist#2024", "heist#9", "heist9#",
    "runner#9", "Runner#9", "runner9", "Runner9",
    "breakin#9", "access#9", "bypass#9", "crack#9",
    "monkey123", "iloveyou", "sunshine", "master", "dragon",
    "football", "baseball", "shadow", "superman", "batman",
    "hello123", "abc123", "123abc", "pass@123", "Pass@123",
    "test1234", "Test1234", "test@123", "Test@123", "user@123",
    "svc_acc01", "svc_vault", "svc#vault", "svc#vault9", "svc#run9",
    "r00t#pass", "r00t#9", "r00t@vault", "admin#vault", "admin#9",
    "n1ghtgl4ss", "N1ghtGl4ss", "obsidian9", "Obsidian#", "obsidian#9",
    "darkrun#9", "darkrun9", "darkrun", "vaultdark", "vaultnight",
    "bhe2024#9", "bhe#vault9", "bhe#run9", "bhe$run9", "bhe$vault9",
    "mercer2024", "e.mercer#9", "emercer9", "eMercer#9", "mercer#9",
    "emercervault", "mercervault9", "mercerpass", "emercer#vault",
    "vaultrun#0", "vaultrun#1", "vaultrun#8", "vaultrun#10", "vaultrun#99",
    "vaultrun#2024", "vaultrun2024#", "vaultrun-9", "vault-run#9",
    "vault.run#9", "vaultrun_9", "vault_run#9", "vault_run_9",
    "system#9", "system#vault", "system$9", "ops#vault9", "ops#run9",
    "infosec#9", "infosec9", "infosec#vault", "cyber#9", "cyber#vault",
]


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — SIEM log forensics
# Correct answer: 91.108.4.77|c.dreyfus|brute_force
# ─────────────────────────────────────────────────────────────────────────────

PHASE2_LOG_ROWS = [
    # Normal internal traffic
    {"id":  1, "time": "00:12:03", "user": "svc.backup",  "ip": "10.0.4.12",    "event": "LOGIN_SUCCESS", "resource": "/data/backup",       "bytes":  4096, "dept": "Internal"},
    {"id":  2, "time": "00:47:31", "user": "r.turner",    "ip": "10.0.5.33",    "event": "FILE_READ",     "resource": "/reports/q3.xlsx",   "bytes": 18240, "dept": "Internal"},
    {"id":  3, "time": "01:03:19", "user": "svc.payroll", "ip": "10.0.8.44",    "event": "LOGIN_SUCCESS", "resource": "/payroll/run",       "bytes":     0, "dept": "Internal"},
    {"id":  4, "time": "01:22:50", "user": "a.hayes",     "ip": "10.0.5.21",    "event": "FILE_READ",     "resource": "/vault/access.log",  "bytes":  1024, "dept": "Internal"},
    {"id":  5, "time": "01:55:12", "user": "j.finch",     "ip": "172.16.2.44",  "event": "LOGIN_FAILED",  "resource": "/portal/login",      "bytes":     0, "dept": "Internal"},
    {"id":  6, "time": "01:55:44", "user": "j.finch",     "ip": "172.16.2.44",  "event": "LOGIN_SUCCESS", "resource": "/portal/login",      "bytes":     0, "dept": "Internal"},
    # Actor A: j.okafor — travelling employee (pre-authorised, bulletin documented)
    {"id":  7, "time": "02:01:04", "user": "j.okafor",    "ip": "46.55.210.13", "event": "LOGIN_SUCCESS", "resource": "/portal/login",      "bytes":     0, "dept": "External"},
    {"id":  8, "time": "02:01:47", "user": "j.okafor",    "ip": "46.55.210.13", "event": "FILE_READ",     "resource": "/hr/travel_forms",   "bytes":  5120, "dept": "External"},
    {"id":  9, "time": "02:04:11", "user": "j.okafor",    "ip": "46.55.210.13", "event": "FILE_DOWNLOAD", "resource": "/hr/expense_report", "bytes":  9800, "dept": "External"},
    {"id": 10, "time": "02:09:33", "user": "j.okafor",    "ip": "46.55.210.13", "event": "LOGOUT",        "resource": "/portal",            "bytes":     0, "dept": "External"},
    # Normal traffic
    {"id": 11, "time": "02:18:33", "user": "r.turner",    "ip": "10.0.5.33",    "event": "FILE_WRITE",    "resource": "/reports/q3_v2",     "bytes": 19100, "dept": "Internal"},
    {"id": 12, "time": "02:30:00", "user": "svc.monitor", "ip": "10.0.2.5",     "event": "SYS_CHECK",     "resource": "/monitor/health",    "bytes":   512, "dept": "Internal"},
    # Actor B: p.walsh — expired-VPN contractor (NOT in bulletin; rule out by behaviour)
    # Failure spacing: 12s, 18s — human-paced manual attempts
    {"id": 13, "time": "02:35:14", "user": "p.walsh",     "ip": "185.92.73.18", "event": "LOGIN_FAILED",  "resource": "/portal/login",      "bytes":     0, "dept": "External"},
    {"id": 14, "time": "02:35:26", "user": "p.walsh",     "ip": "185.92.73.18", "event": "LOGIN_FAILED",  "resource": "/portal/login",      "bytes":     0, "dept": "External"},
    {"id": 15, "time": "02:35:44", "user": "p.walsh",     "ip": "185.92.73.18", "event": "LOGIN_FAILED",  "resource": "/portal/login",      "bytes":     0, "dept": "External"},
    {"id": 16, "time": "02:36:02", "user": "p.walsh",     "ip": "185.92.73.18", "event": "LOGIN_SUCCESS", "resource": "/portal/login",      "bytes":     0, "dept": "External"},
    {"id": 17, "time": "02:36:20", "user": "p.walsh",     "ip": "185.92.73.18", "event": "FILE_READ",     "resource": "/reports/public",    "bytes":  2300, "dept": "External"},
    {"id": 18, "time": "02:37:05", "user": "p.walsh",     "ip": "185.92.73.18", "event": "FILE_READ",     "resource": "/portal/dashboard",  "bytes":  1100, "dept": "External"},
    {"id": 19, "time": "02:38:44", "user": "p.walsh",     "ip": "185.92.73.18", "event": "LOGOUT",        "resource": "/portal",            "bytes":     0, "dept": "External"},
    # Normal traffic
    {"id": 20, "time": "02:39:01", "user": "m.santos",    "ip": "10.0.7.88",    "event": "LOGIN_SUCCESS", "resource": "/portal/login",      "bytes":     0, "dept": "Internal"},
    # Actor C: c.dreyfus — PRIMARY ATTACKER
    # Failure spacing: 4s, 4s, 4s, 3s, 5s — machine-paced automated tool
    # Target endpoint: /vault/auth (not /portal/login — direct vault subsystem)
    # Post-breach: exfiltrates 133 KB of vault material in 7 seconds
    {"id": 21, "time": "02:41:07", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_FAILED",  "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 22, "time": "02:41:11", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_FAILED",  "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 23, "time": "02:41:15", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_FAILED",  "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 24, "time": "02:41:19", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_FAILED",  "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 25, "time": "02:41:22", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_FAILED",  "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 26, "time": "02:41:27", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_FAILED",  "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 27, "time": "02:41:31", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "LOGIN_SUCCESS", "resource": "/vault/auth",        "bytes":     0, "dept": "External"},
    {"id": 28, "time": "02:41:34", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "FILE_READ",     "resource": "/vault/manifest",    "bytes": 45000, "dept": "External"},
    {"id": 29, "time": "02:41:38", "user": "c.dreyfus",   "ip": "91.108.4.77",  "event": "FILE_DOWNLOAD", "resource": "/vault/keys.enc",    "bytes": 88320, "dept": "External"},
    # Normal traffic resumes
    {"id": 30, "time": "02:44:00", "user": "svc.backup",  "ip": "10.0.4.12",    "event": "FILE_WRITE",    "resource": "/data/backup_2",     "bytes": 40960, "dept": "Internal"},
    {"id": 31, "time": "02:55:01", "user": "m.santos",    "ip": "10.0.7.88",    "event": "FILE_READ",     "resource": "/finance/ledger",    "bytes":  7700, "dept": "Internal"},
    {"id": 32, "time": "03:01:33", "user": "a.hayes",     "ip": "10.0.5.21",    "event": "FILE_WRITE",    "resource": "/vault/access.log",  "bytes":  1034, "dept": "Internal"},
    # CDN health-check burst — fast sequential GETs on public static assets only
    {"id": 33, "time": "03:10:11", "user": "svc.cdn",     "ip": "104.21.14.5",  "event": "HTTP_GET",      "resource": "/static/logo.png",   "bytes":  3200, "dept": "External"},
    {"id": 34, "time": "03:10:12", "user": "svc.cdn",     "ip": "104.21.14.5",  "event": "HTTP_GET",      "resource": "/static/style.css",  "bytes":  9800, "dept": "External"},
    {"id": 35, "time": "03:10:13", "user": "svc.cdn",     "ip": "104.21.14.5",  "event": "HTTP_GET",      "resource": "/static/app.js",     "bytes": 22100, "dept": "External"},
    {"id": 36, "time": "03:22:01", "user": "svc.payroll", "ip": "10.0.8.44",    "event": "FILE_READ",     "resource": "/payroll/run",       "bytes":  6600, "dept": "Internal"},
    {"id": 37, "time": "03:31:55", "user": "r.turner",    "ip": "10.0.5.33",    "event": "LOGOUT",        "resource": "/portal",            "bytes":     0, "dept": "Internal"},
    {"id": 38, "time": "03:44:00", "user": "svc.monitor", "ip": "10.0.2.5",     "event": "SYS_CHECK",     "resource": "/monitor/health",    "bytes":   512, "dept": "Internal"},
    {"id": 39, "time": "04:15:22", "user": "m.santos",    "ip": "10.0.7.88",    "event": "LOGOUT",        "resource": "/portal",            "bytes":     0, "dept": "Internal"},
    {"id": 40, "time": "04:58:01", "user": "svc.monitor", "ip": "10.0.2.5",     "event": "SYS_CHECK",     "resource": "/monitor/health",    "bytes":   512, "dept": "Internal"},
]

PHASE2_CORRECT_ROW_IDS  = list(range(21, 30))   # IDs 21..29: all 6 failures + success + 2 exfil
PHASE2_ATTACKER_IP      = "91.108.4.77"
PHASE2_ATTACKER_USER    = "c.dreyfus"
PHASE2_ATTACK_TYPE      = "brute_force"
PHASE2_ANSWER           = f"{PHASE2_ATTACKER_IP}|{PHASE2_ATTACKER_USER}|{PHASE2_ATTACK_TYPE}"

# IDs that are clearly not part of the breach (used for UI directional feedback)
PHASE2_BENIGN_IDS = {7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 33, 34, 35}


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — Two-layer encoded transmission
# Encoding pipeline (what the attacker did to transmit):
#   plaintext → ROT13 → Base64 → transmitted blob
# Token: OBSIDIAN (submit lowercase: obsidian)
# ─────────────────────────────────────────────────────────────────────────────

PHASE3_PLAINTEXT = (
    "CLASSIFIED RELAY — internal ops channel. "
    "Vault subsystem authentication bypass confirmed. "
    "Proceed with secondary extraction. Codename: OBSIDIAN. "
    "Destroy this transmission upon receipt. EOM."
)

def _rot13(text):
    """Shift A–Z by 13 and a–z by 13. Self-inverse."""
    out = []
    for c in text:
        if 'A' <= c <= 'Z':
            out.append(chr((ord(c) - 65 + 13) % 26 + 65))
        elif 'a' <= c <= 'z':
            out.append(chr((ord(c) - 97 + 13) % 26 + 97))
        else:
            out.append(c)
    return ''.join(out)

# Step 1: ROT13 of plaintext (inner layer)
PHASE3_ROT13_INTERMEDIATE = _rot13(PHASE3_PLAINTEXT)

# Step 2: Base64 of the ROT13 output (outer layer) — this is what students receive
PHASE3_ENCODED = base64.b64encode(PHASE3_ROT13_INTERMEDIATE.encode()).decode()

PHASE3_TOKEN = "obsidian"


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — VLT-7 reflected vault code
#   Fragments in phase order:       "4" + "8" + "6"  → "486"
#   Append Phase 1 password length: len("vaultrun#9") = 10  → "48610"
#   Append unique attacker IP count: 1 (only 91.108.4.77)   → "486101"
#   VLT-7 reflection (reverse):     "486101" → "101684"
#
# Answer: 101684
# ─────────────────────────────────────────────────────────────────────────────

PHASE4_ANSWER   = "101684"
PHASE_FRAGMENTS = {1: "4", 2: "8", 3: "6"}


# ─────────────────────────────────────────────────────────────────────────────
# CHALLENGE METADATA
# ─────────────────────────────────────────────────────────────────────────────

CHALLENGES = {
    1: {
        "title": "Phase 1 — Salted SHA-256 Recovery",
        "description": (
            "A credential dump from a compromised internal workstation has been recovered. "
            "It contains a salted SHA-256 hash for user <strong>e.mercer</strong> and a "
            "partially redacted application config file. The config includes a comment "
            "that reveals the salt format used by this application. "
            "A 120-entry wordlist from the same host is available."
        ),
        "objective": "Recover the plaintext password from the salted SHA-256 hash.",
        "task_brief": (
            "The hash was produced as SHA-256(salt + password). The salt value is shown "
            "in the recovered config comment. You cannot reverse SHA-256 — you must test "
            "each wordlist candidate by computing SHA-256(salt + candidate) and comparing "
            "against the target digest. SHA-256 is case- and symbol-sensitive: two "
            "candidates that differ by one character will produce completely different "
            "64-character hex digests. Work systematically. Once you confirm a match, "
            "submit the exact plaintext password (not the hash, not the salt)."
        ),
        "answer": PHASE1_PASSWORD,
        "answer_label": "Enter the cracked plaintext password (exact characters)",
        "hints": [
            "HINT 1: Prepend the salt to each candidate before hashing — "
            "SHA-256(salt + candidate), not SHA-256(candidate). The config comment "
            "shows the exact salt string to use.",
            "HINT 2: Rainbow tables are useless here. A unique per-application salt means "
            "no pre-computed table contains entries for SHA-256(bhe$2024 + anything).",
            "HINT 3: The correct password contains a special character. Candidates with "
            "only alphanumeric characters will all fail — focus on entries with # $ ! @ etc.",
            "HINT 4: Symbol position matters. 'vaultrun9#' and 'vaultrun#9' share the "
            "same characters but hash to completely different values.",
        ],
        "vault_fragment": PHASE_FRAGMENTS[1],
    },
    2: {
        "title": "Phase 2 — SIEM Log Forensics",
        "description": (
            "A 40-entry SIEM extract from a 5-hour window has been recovered. "
            "An intrusion occurred during this period. The logs contain normal internal "
            "traffic, a pre-authorised external session (documented in the security "
            "bulletin), a second undocumented external session that triggered alerts, "
            "and the actual breach sequence. Events carry no pre-applied classifications."
        ),
        "objective": "Identify the attacker IP, the compromised account, and the attack type.",
        "task_brief": (
            "Two external actors generated suspicious events. Neither is automatically "
            "disqualified — you must distinguish them by examining post-login behaviour. "
            "Consider: which endpoint was targeted? What resources were accessed after "
            "a successful login? How much data was transferred, and how quickly? "
            "Failure interval timing also matters: sub-5-second spacing between attempts "
            "indicates automation; 12–20 second spacing indicates manual entry. "
            "Select the rows forming the complete breach sequence, then submit: "
            "AttackerIP|username|attack_type "
            "where attack_type is one of: brute_force / credential_stuffing / phishing / insider"
        ),
        "answer": PHASE2_ANSWER,
        "answer_label": "Submit: AttackerIP|username|attack_type",
        "hints": [
            "HINT 1: The security bulletin documents one pre-authorised external session. "
            "A second external actor appears in the logs but is NOT in the bulletin. "
            "You cannot use the bulletin to rule them out — you must analyse their behaviour.",
            "HINT 2: Failure timing is a classification signal. Measure the seconds between "
            "consecutive failures for each suspect. Sub-5s intervals are automated tooling. "
            "12–18s intervals are a human at a keyboard.",
            "HINT 3: The targeted endpoint is diagnostic. The portal login endpoint handles "
            "normal user access. A direct vault authentication endpoint is a privileged "
            "subsystem — external access attempts against it are a significant IOC.",
            "HINT 4: Compare post-login byte volumes. One external actor transferred under "
            "3.5 KB of non-sensitive material and then logged out. The other pulled over "
            "130 KB of encrypted vault material within 7 seconds of gaining entry.",
        ],
        "vault_fragment": PHASE_FRAGMENTS[2],
    },
    3: {
        "title": "Phase 3 — Intercepted Encoded Transmission",
        "description": (
            "An encoded relay message was captured in transit from a compromised internal node. "
            "The message was processed through two encoding stages before transmission. "
            "Your toolkit provides five decode methods. Applying them in the wrong order "
            "will produce output that looks structured or partially readable — but is not "
            "the original message. Read each intermediate result carefully before deciding "
            "what to apply next."
        ),
        "objective": "Fully decode the transmission and extract the operational codename.",
        "task_brief": (
            "Two encoding layers were applied in sequence before transmission. "
            "To recover the original message you must remove them in reverse order: "
            "outer layer first, then the inner layer. "
            "After removing the first layer, inspect the output — if it still looks like "
            "English words with every letter consistently displaced, that pattern "
            "identifies the inner layer. "
            "The operational codename is a single word in ALL CAPS embedded in the "
            "recovered plaintext. Submit it in lowercase."
        ),
        "answer": PHASE3_TOKEN,
        "answer_label": "Enter the operational codename (lowercase)",
        "hints": [
            "HINT 1: Examine the transmitted blob's character set and structure. "
            "The presence of +, /, and trailing = characters, combined with the "
            "restricted alphabet, identifies the outer encoding scheme.",
            "HINT 2: After removing the outer layer, the result is still not readable "
            "English — but it uses only printable ASCII characters and the 'words' "
            "have the right length distribution. Every letter has been shifted by the "
            "same fixed amount.",
            "HINT 3: Applying the decode tools in the wrong order produces output that "
            "looks superficially encoded but is not recoverable. If you get non-ASCII "
            "output or a decode error after step 2, your order is wrong — restart.",
            "HINT 4: The inner cipher is its own inverse. Once you know what it is, "
            "apply it once to the step-1 output. The codename will appear in ALL CAPS "
            "after the label 'Codename:'.",
        ],
        "vault_fragment": PHASE_FRAGMENTS[3],
    },
    4: {
        "title": "Phase 4 — VLT-7 Vault Code Assembly",
        "description": (
            "All three security layers are down. Fortis Bank's vault controller requires "
            "a composite access code derived from the intelligence recovered across the "
            "operation. The vault firmware implements protocol VLT-7: a reflected-entry "
            "sequence in which the assembled code is reversed before submission. "
            "This mirrors the CRC bit-reflection convention used in the vault's hardware "
            "checksum verification layer — a deliberate anti-replay measure."
        ),
        "objective": "Assemble and submit the VLT-7 reflected entry code.",
        "task_brief": (
            "VLT-7 assembly steps:\n"
            "1. Concatenate your vault fragments in phase order (Phase 1 → Phase 2 → Phase 3).\n"
            "2. Append the exact character count of the Phase 1 plaintext password.\n"
            "3. Append the count of unique malicious IPs confirmed in Phase 2.\n"
            "4. Apply VLT-7 reflection: reverse the entire assembled digit string.\n"
            "Submit the reversed result. No spaces, no separators."
        ),
        "answer": PHASE4_ANSWER,
        "answer_label": "Enter the VLT-7 reflected code",
        "hints": [
            "HINT 1: Your three vault fragments are shown in the sidebar. They are single "
            "digits awarded at the end of each phase. Concatenate them left-to-right "
            "in the order they were earned.",
            "HINT 2: Count every character in the Phase 1 password you recovered — "
            "including the special character. Do not count the salt prefix.",
            "HINT 3: For the IP count, use only IPs confirmed as malicious. "
            "The pre-authorised employee and the expired-certificate contractor are "
            "not attackers — only one IP was confirmed as the source of the breach.",
            "HINT 4: VLT-7 reflection means reversing the complete digit string you "
            "assembled in steps 1–3. Example: assembled string '48610' → reversed → '01684'. "
            "Submit the reversed version.",
        ],
        "vault_fragment": None,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

def get_initial_state():
    return {
        "progress": 1,
        "vault_fragments": [],
        "phase_answers": {},
        "phase1_tested_candidates": [],
        "phase1_match_found": False,
        "phase1_wrong_submits": 0,
        "phase2_selected_rows": [],
        "phase2_analysis_unlocked": False,
        "phase2_wrong_submits": 0,
        "phase3_decode_attempts": [],
        "phase3_layers_completed": 0,  # 0=none, 1=outer removed, 2=fully decoded
        "phase3_wrong_submits": 0,
        "phase4_wrong_submits": 0,
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


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

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
    state    = get_state()
    progress = state["progress"]
    total    = len(CHALLENGES)

    base = {
        "vault_fragments":     state["vault_fragments"],
        "phase_answers":       state["phase_answers"],
        "total_wrong_submits": state.get("total_wrong_submits", 0),
        "lockout_warned":      state.get("lockout_warned", False),
        "phase1": {
            "username":          "e.mercer",
            "hash_type":         "SHA-256 (salted)",
            "salt_hint":         "// app_salt = bhe$2024",
            "hash":              PHASE1_HASH,
            "candidates":        PHASE1_CANDIDATES,
            "tested_candidates": state["phase1_tested_candidates"],
            "match_found":       state["phase1_match_found"],
            "wrong_submits":     state["phase1_wrong_submits"],
        },
        "phase2": {
            "rows":              PHASE2_LOG_ROWS,
            "selected_rows":     state["phase2_selected_rows"],
            "analysis_unlocked": state["phase2_analysis_unlocked"],
            "wrong_submits":     state["phase2_wrong_submits"],
            "bulletin": (
                "SECURITY BULLETIN 2024-04-08: J. Okafor (j.okafor) is travelling in "
                "Germany for the Berlin conference. External logins from European IP ranges "
                "are pre-authorised for this account until 2024-04-10."
            ),
        },
        "phase3": {
            "encoded":          PHASE3_ENCODED,
            "decode_attempts":  state["phase3_decode_attempts"],
            "layers_completed": state["phase3_layers_completed"],
            "wrong_submits":    state["phase3_wrong_submits"],
        },
        "phase4": {
            "wrong_submits": state["phase4_wrong_submits"],
        },
    }

    if progress > total:
        return jsonify({
            **base,
            "completed": True, "progress": total, "total": total,
            "title": "VAULT BREACHED",
            "description": "The final vault door disengages. The operation is complete.",
            "objective": "Mission Accomplished",
            "task_brief": "All four phases completed successfully.",
            "answer_label": "",
            "hints": [
                "DEBRIEF: Per-application salts defeat rainbow tables — uniqueness is the mechanism.",
                "DEBRIEF: SIEM triage requires behavioural comparison, not only pattern recognition.",
                "DEBRIEF: Encoding layer identification depends on output inspection, not tool-cycling.",
                "DEBRIEF: VLT-7 reflection is grounded in CRC bit-reversal used in real vault hardware.",
            ],
        })

    ch = CHALLENGES[progress]
    return jsonify({
        **base,
        "completed": False, "progress": progress, "total": total,
        "title":        ch["title"],
        "description":  ch["description"],
        "objective":    ch["objective"],
        "task_brief":   ch["task_brief"],
        "answer_label": ch["answer_label"],
        "hints":        ch["hints"],
    })


@app.route("/phase1_test_candidate", methods=["POST"])
def phase1_test_candidate():
    state = get_state()
    if state["progress"] != 1:
        return jsonify({"success": False, "message": "Phase 1 is not active."})

    data      = request.get_json(silent=True) or {}
    candidate = str(data.get("candidate", "")).strip()
    if not candidate:
        return jsonify({"success": False, "message": "No candidate provided."})

    computed = hashlib.sha256((PHASE1_SALT + candidate).encode()).hexdigest()
    is_match = (computed == PHASE1_HASH)

    if candidate not in state["phase1_tested_candidates"]:
        state["phase1_tested_candidates"].append(candidate)
    if is_match:
        state["phase1_match_found"] = True
    save_state(state)

    return jsonify({
        "success":       True,
        "candidate":     candidate,
        "computed_hash": computed,
        "target_hash":   PHASE1_HASH,
        "is_match":      is_match,
        "attempts_used": len(state["phase1_tested_candidates"]),
        "message": ("HASH MATCH — submit the plaintext password."
                    if is_match else "No match."),
    })


@app.route("/phase2_toggle_row", methods=["POST"])
def phase2_toggle_row():
    state = get_state()
    if state["progress"] != 2:
        return jsonify({"success": False, "message": "Phase 2 is not active."})

    data   = request.get_json(silent=True) or {}
    row_id = data.get("row_id")
    if not isinstance(row_id, int):
        return jsonify({"success": False, "message": "Invalid row id."})

    sel = state["phase2_selected_rows"]
    if row_id in sel:
        sel.remove(row_id)
    else:
        sel.append(row_id)
    sel.sort()

    state["phase2_analysis_unlocked"] = (sel == PHASE2_CORRECT_ROW_IDS)
    save_state(state)

    if state["phase2_analysis_unlocked"]:
        msg = "Breach sequence confirmed. Submit attacker details."
    elif sel:
        correct_set = set(PHASE2_CORRECT_ROW_IDS)
        sel_set     = set(sel)
        if sel_set & PHASE2_BENIGN_IDS:
            msg = "Selection includes rows that appear to be authorised or benign activity."
        elif sel_set - correct_set:
            msg = "Selection includes rows outside the breach sequence."
        elif sel_set.issubset(correct_set):
            msg = f"Partial breach sequence — {len(sel)}/{len(PHASE2_CORRECT_ROW_IDS)} rows selected."
        else:
            msg = "Selection updated."
    else:
        msg = "Selection cleared."

    return jsonify({
        "success":           True,
        "selected_rows":     sel,
        "analysis_unlocked": state["phase2_analysis_unlocked"],
        "message":           msg,
    })


@app.route("/phase3_decode", methods=["POST"])
def phase3_decode():
    """
    Decode tool for Phase 3.

    The server returns the raw output and a neutral observation note.
    It does NOT label any attempt as "correct" or "incorrect" in the response —
    the student must read the output and decide what to do next.
    Layer tracking is still maintained server-side to gate the submit route.
    """
    state = get_state()
    if state["progress"] != 3:
        return jsonify({"success": False, "message": "Phase 3 is not active."})

    data       = request.get_json(silent=True) or {}
    method     = str(data.get("method", "")).strip().lower()
    input_text = str(data.get("input_text", "")).strip() or None

    output = ""
    note   = ""

    src = input_text if input_text else PHASE3_ENCODED

    if method == "base64":
        try:
            decoded = base64.b64decode(src.encode()).decode("utf-8")
            output  = decoded
            # Track layer completion silently — no hint in the note
            if decoded == PHASE3_ROT13_INTERMEDIATE and state["phase3_layers_completed"] < 1:
                state["phase3_layers_completed"] = 1
            elif decoded == PHASE3_PLAINTEXT:
                state["phase3_layers_completed"] = 2
            note = "Base64 decode applied."
        except Exception:
            output = "[Base64 decode error: input does not appear to be valid Base64]"
            note   = ""

    elif method == "rot13":
        result = _rot13(src)
        output = result
        if result == PHASE3_PLAINTEXT:
            state["phase3_layers_completed"] = 2
        note = "ROT13 applied."

    elif method == "caesar3":
        out = []
        for c in src:
            if c.isupper():
                out.append(chr((ord(c) - 65 - 3) % 26 + 65))
            elif c.islower():
                out.append(chr((ord(c) - 97 - 3) % 26 + 97))
            else:
                out.append(c)
        output = ''.join(out)
        note   = "Caesar-3 shift applied."

    elif method == "hex":
        try:
            output = bytes.fromhex(src.replace(" ", "")).decode("utf-8", errors="replace")
            note   = "Hex decode applied."
        except Exception:
            output = "[Hex decode error: input does not appear to be valid hexadecimal]"

    elif method == "url":
        output = url_unquote(src)
        note   = "URL decode applied."

    else:
        output = f"[Unknown method '{method}'] — available: base64, rot13, caesar3, hex, url"

    state["phase3_decode_attempts"].append({
        "method":        method,
        "input_preview": (input_text[:50] + "…") if input_text and len(input_text) > 50 else input_text,
        "output":        output,
        "note":          note,
        "timestamp":     time.strftime("%H:%M:%S"),
    })
    save_state(state)

    return jsonify({
        "success":          True,
        "method":           method,
        "output":           output,
        "note":             note,
        "layers_completed": state["phase3_layers_completed"],
    })


@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    state    = get_state()
    progress = state["progress"]
    total    = len(CHALLENGES)

    if progress > total:
        return jsonify({"success": True, "message": "Vault already breached.", "completed": True})

    data    = request.get_json(silent=True) or {}
    answer  = str(data.get("answer", "")).strip().lower()
    ch      = CHALLENGES[progress]
    correct = ch["answer"].strip().lower()

    # Pre-flight gates — student must complete the phase task before submitting
    if progress == 1 and not state["phase1_match_found"]:
        return jsonify({"success": False, "penalty": False, "completed": False,
                        "message": "No hash match recorded. Confirm a candidate match before submitting."})

    if progress == 2 and not state["phase2_analysis_unlocked"]:
        return jsonify({"success": False, "penalty": False, "completed": False,
                        "message": "Breach sequence not confirmed. Identify and select the correct log rows."})

    if progress == 3 and state["phase3_layers_completed"] < 2:
        n = state["phase3_layers_completed"]
        return jsonify({"success": False, "penalty": False, "completed": False,
                        "message": f"Transmission only {n}/2 layers decoded. Continue decoding."})

    if progress == 2 and answer.count("|") != 2:
        return jsonify({"success": False, "penalty": False, "completed": False,
                        "message": "Format: AttackerIP|username|attack_type (two pipe separators required)."})

    if answer != correct:
        pk = f"phase{progress}_wrong_submits"
        state[pk] = state.get(pk, 0) + 1
        state["total_wrong_submits"] = state.get("total_wrong_submits", 0) + 1

        # Partial feedback for Phase 2 only
        partial = ""
        if progress == 2 and answer.count("|") == 2:
            ap, cp = answer.split("|"), correct.split("|")
            if ap[0] == cp[0] and ap[1] != cp[1]:
                partial = " IP confirmed — recheck the username."
            elif ap[1] == cp[1] and ap[0] != cp[0]:
                partial = " Username confirmed — recheck the IP."
            elif ap[0] == cp[0] and ap[1] == cp[1]:
                partial = " IP and username confirmed — reconsider the attack_type."

        if state["total_wrong_submits"] >= LOCKOUT_THRESHOLD and not state.get("lockout_warned"):
            state["lockout_warned"] = True
            save_state(state)
            return jsonify({
                "success": False, "penalty": True, "completed": False,
                "message": (f"SECURITY ALERT: {state['total_wrong_submits']} incorrect submissions. "
                            "A real system would lock this account. Re-examine your analysis." + partial),
                "wrong_count": state["total_wrong_submits"],
            })

        save_state(state)
        n = state.get(pk, 0)
        return jsonify({
            "success": False, "penalty": False, "completed": False,
            "message": (f"Incorrect. ({n} failed attempt{'s' if n != 1 else ''} on this phase.)"
                        + (partial or " Review the task brief.")),
            "wrong_count": n,
        })

    # Correct
    state["phase_answers"][f"phase_{progress}"] = ch["answer"]
    if ch["vault_fragment"]:
        state["vault_fragments"].append(ch["vault_fragment"])
    state["progress"] = progress + 1
    save_state(state)

    if state["progress"] > total:
        return jsonify({"success": True, "completed": True,
                        "message": "ACCESS GRANTED — VAULT OPENED. Operation complete."})

    return jsonify({"success": True, "completed": False,
                    "message": f"Phase {progress} complete. Fragment recovered. Phase {progress + 1} unlocked."})


@app.route("/reset", methods=["POST"])
def reset():
    session["game_state"] = get_initial_state()
    return jsonify({"success": True, "message": "Session reset."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)