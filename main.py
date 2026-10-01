from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time
import threading

app = Flask(__name__)

CORS(app)

# ==========================================
# GAME SETTINGS
# ==========================================

PICKING_TIME = 40
CALL_INTERVAL = 3
WINNER_DELAY = 5


# ==========================================
# GAME DATA
# ==========================================

game = {
    "round": 1,
    "status": "picking",
    "round_started_at": time.time(),
    "last_call_at": None,
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

    return jsonify({
        "success": True,
        "message": "Telegram Bingo app connected to Python backend!"
    })


# ==========================================
# GAME STATUS
# ==========================================

@app.route("/api/game-status")
def game_status():

    update_game_state()

    if game["status"] == "picking":

        elapsed = time.time() - game["round_started_at"]

        remaining = max(
            0,
            PICKING_TIME - int(elapsed)
        )

    elif game["status"] == "playing":

        remaining = 0

    elif game["status"] == "winner":

        elapsed = time.time() - game["round_started_at"]

        remaining = max(
            0,
            WINNER_DELAY - int(elapsed)
        )

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

    # Only allow joining during picking

    if game["status"] != "picking":

        return jsonify({

            "success": False,

            "message": "Card picking is closed."

        }), 400


    # Prevent same player joining repeatedly

    for player in game["players"]:

        if player["name"] == player_name:

            return jsonify({

                "success": True,

                "message": "Player already joined.",

                "player": player,

                "round": game["round"]

            })


    # Create player

    player = {

        "id": str(
            random.randint(
                100000,
                999999
            )
        ),

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


    # ======================================
    # PICKING → PLAYING
    # ======================================

    if game["status"] == "picking":

        if elapsed >= PICKING_TIME:

            game["status"] = "playing"

            game["called_numbers"] = []

            game["last_call_at"] = now

            print(
                f"🎮 Round {game['round']} started!"
            )


    # ======================================
    # AUTOMATIC NUMBER CALLING
    # ======================================

    if game["status"] == "playing":

        if game["last_call_at"] is None:

            game["last_call_at"] = now


        time_since_last_call = (
            now - game["last_call_at"]
        )


        if time_since_last_call >= CALL_INTERVAL:

            call_next_number()


# ==========================================
# CALL NEXT NUMBER
# ==========================================

def call_next_number():

    available = [

        number

        for number in range(1, 76)

        if number not in game["called_numbers"]

    ]


    # All 75 numbers have been called

    if not available:

        print(
            "🎱 All 75 numbers have been called!"
        )

        return


    # Pick random number

    number = random.choice(
        available
    )


    # Save number

    game["called_numbers"].append(
        number
    )


    # Update call time

    game["last_call_at"] = time.time()


    # Get Bingo letter

    if number <= 15:

        letter = "B"

    elif number <= 30:

        letter = "I"

    elif number <= 45:

        letter = "N"

    elif number <= 60:

        letter = "G"

    else:

        letter = "O"


    print(
        f"🎱 Called: {letter}-{number}"
    )


# ==========================================
# MANUAL CALL TEST
# ==========================================

@app.route("/api/call-number", methods=["POST"])
def manual_call_number():

    update_game_state()

    if game["status"] != "playing":

        return jsonify({

            "success": False,

            "message":
            "The game is not currently playing."

        }), 400


    call_next_number()


    return jsonify({

        "success": True,

        "called_numbers":
        game["called_numbers"]

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
