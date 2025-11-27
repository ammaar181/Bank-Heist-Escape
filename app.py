from flask import Flask, send_from_directory, jsonify, request
import hashlib

app = Flask(__name__, static_folder="static", static_url_path="/static")

# ---- Puzzle data (simple in-memory store) ----

def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

PUZZLES = {
    "password": {
        "id": "password",
        "title": "Keypad Door Override",
        "type": "password",
        "description": (
            "The outer keypad controls access to the bank lobby.\n"
            "Intel says the guard chose a very lazy 4-digit code.\n"
            "Hint: all four digits are the same."
        ),
        "hash": md5("7777")  # correct code = 7777
    },
    # later we’ll add: phishing / cipher / logs / vault…
}

# ---- Routes to serve pages ----

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/game")
def game():
    # nicer URL instead of /static/game.html
    return send_from_directory("static", "game.html")

# ---- API routes ----

@app.route("/api/puzzles")
def list_puzzles():
    # only send safe metadata (no answers)
    meta = []
    for p in PUZZLES.values():
        meta.append({
            "id": p["id"],
            "title": p["title"],
            "type": p["type"],
        })
    return jsonify(meta)

@app.route("/api/puzzle/<pid>")
def get_puzzle(pid):
    p = PUZZLES.get(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    # don’t leak the hash logic; we only send description + type
    return jsonify({
        "id": p["id"],
        "title": p["title"],
        "type": p["type"],
        "description": p["description"],
    })

@app.route("/api/submit/<pid>", methods=["POST"])
def submit(pid):
    p = PUZZLES.get(pid)
    if not p:
        return jsonify({"error": "unknown puzzle"}), 404

    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip()

    if p["type"] == "password":
        # check md5 of answer against stored hash
        if md5(answer) == p["hash"]:
            return jsonify({
                "correct": True,
                "message": "Door unlocked. You slipped into the lobby."
            })
        else:
            return jsonify({
                "correct": False,
                "message": "Wrong code. The keypad beeps angrily."
            })

    # fallback for future types
    return jsonify({"error": "unhandled puzzle type"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
