from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "message": "🎱 Beteseb Bingo Backend is running!",
        "status": "online"
    })


@app.route("/game")
def game():
    return jsonify({
        "game": "Beteseb Bingo",
        "status": "ready"
    })


@app.route("/api/test")
def api_test():
    return jsonify({
        "success": True,
        "message": "Telegram Bingo app connected to Python backend!"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
