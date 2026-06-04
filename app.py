from flask import Flask, jsonify
from state import get_state

app = Flask(__name__)

@app.route("/api/now-playing/<uid>")
def now_playing(uid):
    return jsonify(get_state(uid))


@app.route("/")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)