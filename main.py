from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time

app = Flask(__name__)

CORS(app)

# ==========================================
# AUTOMATIC BINGO GAME
# ==========================================

PICKING_TIME = 40
WINNER_DELAY = 5

game = {
    "round": 1,
    "status": "picking",
    "round_started_at": time.time(),
    "players": [],
    "called_numbers": [],
    "winner": None
}


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return jsonify({
        "message": "🎱 Beteseb Bingo Backend is running!",
        "status": "online"
    })


# ==========================================
# API TEST
# ==========================================

@app.route("/api/test")
def api_test():

    response = jsonify({
        "success": True,
        "message": "Telegram Bingo app connected to Python backend!"
    })

    response.headers["Access-Control-Allow-Origin"] = "*"

    return response


# ==========================================
# GAME STATUS
# ==========================================

@app.route("/api/game-status")
def game_status():

    update_game_state()

    elapsed = time.time() - game["round_started_at"]

    if game["status"] == "picking":
        remaining = max(0, PICKING_TIME - int(elapsed))

    elif game["status"] == "winner":
        remaining = max(0, WINNER_DELAY - int(elapsed))

    else:
        remaining = 0

    return jsonify({
        "success": True,
        "round": game["round"],
        "status": game["status"],
        "remaining": remaining,
        "players": len(game["players"]),
        "called_numbers": game["called_numbers"],
        "winner": game["winner"]
    })


# ==========================================
# JOIN CURRENT ROUND
# ==========================================

@app.route("/api/join", methods=["POST"])
def join():

    update_game_state()

    data = request.get_json() or {}

    player_name = data.get(
        "player_name",
        "Player"
    )

    # Players can only join during card picking
    if game["status"] != "picking":

        return jsonify({
            "success": False,
            "message": "Card picking is closed."
        }), 400

    # Create player
    player = {
        "id": str(random.randint(100000, 999999)),
        "name": player_name
    }

    game["players"].append(player)

    return jsonify({
        "success": True,
        "message": f"Player {player_name} joined!",
        "player": player,
        "round": game["round"]
    })


# ==========================================
# UPDATE GAME STATE
# ==========================================

def update_game_state():

    now = time.time()

    elapsed = now - game["round_started_at"]

    # --------------------------------------
    # PICKING → GAME
    # --------------------------------------

    if game["status"] == "picking":

        if elapsed >= PICKING_TIME:

            game["status"] = "playing"

            game["called_numbers"] = []

            print(
                f"🎮 Round {game['round']} started!"
            )


    # --------------------------------------
    # WINNER → NEW ROUND
    # --------------------------------------

    elif game["status"] == "winner":

        if elapsed >= WINNER_DELAY:

            game["round"] += 1

            game["status"] = "picking"

            game["round_started_at"] = now

            game["players"] = []

            game["called_numbers"] = []

            game["winner"] = None

            print(
                f"🔄 Round {game['round']} started!"
            )


# ==========================================
# CALL NUMBER
# ==========================================

@app.route("/api/call-number", methods=["POST"])
def call_number():

    update_game_state()

    if game["status"] != "playing":

        return jsonify({
            "success": False,
            "message": "The game is not currently playing."
        }), 400

    available = [
        number
        for number in range(1, 76)
        if number not in game["called_numbers"]
    ]

    if not available:

        return jsonify({
            "success": False,
            "message": "All numbers have been called."
        })

    number = random.choice(available)

    game["called_numbers"].append(number)

    return jsonify({
        "success": True,
        "number": number,
        "called_numbers": game["called_numbers"]
    })


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
