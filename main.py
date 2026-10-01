from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time

app = Flask(__name__)

CORS(app)

# ==========================================
# GAME SETTINGS
# ==========================================

PICKING_TIME = 40
CALL_INTERVAL = 3


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
        "message": "Telegram Bingo app connected!"
    })


# ==========================================
# GAME STATUS
# ==========================================

@app.route("/api/game-status")
def game_status():

    update_game_state()

    if game["status"] == "picking":

        elapsed = (
            time.time()
            - game["round_started_at"]
        )

        remaining = max(
            0,
            PICKING_TIME - int(elapsed)
        )

    else:

        remaining = 0


    return jsonify({

        "success": True,

        "round": game["round"],

        "status": game["status"],

        "remaining": remaining,

        "players": len(game["players"]),

        "called_numbers":
            game["called_numbers"],

        "winner":
            game["winner"]

    })


# ==========================================
# JOIN ROUND
# ==========================================

@app.route("/api/join", methods=["POST"])
def join():

    update_game_state()

    data = request.get_json() or {}

    player_name = data.get(
        "player_name",
        "Player"
    )

    card = data.get(
        "card"
    )


    # --------------------------------------
    # CHECK GAME STATUS
    # --------------------------------------

    if game["status"] != "picking":

        return jsonify({

            "success": False,

            "message":
                "Card picking is closed."

        }), 400


    # --------------------------------------
    # CHECK CARD
    # --------------------------------------

    if not card or len(card) != 25:

        return jsonify({

            "success": False,

            "message":
                "Invalid Bingo card."

        }), 400


    # --------------------------------------
    # CHECK DUPLICATE PLAYER
    # --------------------------------------

    for player in game["players"]:

        if player["name"] == player_name:

            return jsonify({

                "success": True,

                "message":
                    "Player already joined.",

                "player":
                    player,

                "round":
                    game["round"]

            })


    # --------------------------------------
    # CREATE PLAYER
    # --------------------------------------

    player = {

        "id":
            str(
                random.randint(
                    100000,
                    999999
                )
            ),

        "name":
            player_name,

        "card":
            card

    }


    game["players"].append(
        player
    )


    print(
        f"👤 {player_name} joined "
        f"Round {game['round']}"
    )


    return jsonify({

        "success": True,

        "message":
            f"Player {player_name} joined!",

        "player":
            player,

        "round":
            game["round"]

    })


# ==========================================
# UPDATE GAME STATE
# ==========================================

def update_game_state():

    now = time.time()

    elapsed = (
        now
        - game["round_started_at"]
    )


    # ======================================
    # PICKING → PLAYING
    # ======================================

    if game["status"] == "picking":

        if elapsed >= PICKING_TIME:

            game["status"] = "playing"

            game["called_numbers"] = []

            game["last_call_at"] = now

            print(
                f"🎮 Round "
                f"{game['round']} started!"
            )


    # ======================================
    # AUTOMATIC NUMBER CALLING
    # ======================================

    if game["status"] == "playing":

        if game["last_call_at"] is None:

            game["last_call_at"] = now


        if (
            now
            - game["last_call_at"]
            >= CALL_INTERVAL
        ):

            call_next_number()


# ==========================================
# CALL NEXT NUMBER
# ==========================================

def call_next_number():

    available = [

        number

        for number in range(1, 76)

        if number
        not in game["called_numbers"]

    ]


    if not available:

        return


    number = random.choice(
        available
    )


    game["called_numbers"].append(
        number
    )


    game["last_call_at"] = time.time()


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
        f"🎱 Called: "
        f"{letter}-{number}"
    )


# ==========================================
# MANUAL CALL TEST
# ==========================================

@app.route(
    "/api/call-number",
    methods=["POST"]
)
def manual_call_number():

    update_game_state()

    if game["status"] != "playing":

        return jsonify({

            "success": False,

            "message":
                "Game is not playing."

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
