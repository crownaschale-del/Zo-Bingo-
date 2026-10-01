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
WINNER_DELAY = 5


# ==========================================
# GAME DATA
# ==========================================

game = {
    "round": 1,
    "status": "picking",
    "round_started_at": time.time(),
    "last_call_at": None,
    "winner_time": None,
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
        "message":
            "🎱 Beteseb Bingo Backend is running!",
        "status": "online"
    })


# ==========================================
# API TEST
# ==========================================

@app.route("/api/test")
def api_test():

    return jsonify({
        "success": True,
        "message":
            "Telegram Bingo app connected!"
    })


# ==========================================
# GAME STATUS
# ==========================================

@app.route("/api/game-status")
def game_status():

    update_game_state()

    # ------------------------------
    # PICKING TIMER
    # ------------------------------

    if game["status"] == "picking":

        elapsed = (
            time.time()
            - game["round_started_at"]
        )

        remaining = max(
            0,
            PICKING_TIME - int(elapsed)
        )


    # ------------------------------
    # WINNER TIMER
    # ------------------------------

    elif game["status"] == "winner":

        elapsed = (
            time.time()
            - game["winner_time"]
        )

        remaining = max(
            0,
            WINNER_DELAY - int(elapsed)
        )


    else:

        remaining = 0


    return jsonify({

        "success": True,

        "round":
            game["round"],

        "status":
            game["status"],

        "remaining":
            remaining,

        "players":
            len(game["players"]),

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

    card = data.get("card")


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

    # ======================================
    # PICKING
    # ======================================

    if game["status"] == "picking":

        elapsed = (
            now
            - game["round_started_at"]
        )


        if elapsed >= PICKING_TIME:

            game["status"] = "playing"

            game["called_numbers"] = []

            game["last_call_at"] = now

            print(
                f"🎮 Round "
                f"{game['round']} started!"
            )


    # ======================================
    # PLAYING
    # ======================================

    elif game["status"] == "playing":

        if game["last_call_at"] is None:

            game["last_call_at"] = now


        if (
            now
            - game["last_call_at"]
            >= CALL_INTERVAL
        ):

            call_next_number()


            # Check for Bingo

            check_winner()


    # ======================================
    # WINNER
    # ======================================

    elif game["status"] == "winner":

        elapsed = (
            now
            - game["winner_time"]
        )


        if elapsed >= WINNER_DELAY:

            start_new_round()


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
# CHECK BINGO WINNER
# ==========================================

def check_winner():

    if not game["players"]:

        return


    called = set(
        game["called_numbers"]
    )


    for player in game["players"]:

        card = player["card"]


        # FREE CENTER

        marked = []


        for index, value in enumerate(card):

            if index == 12:

                marked.append(True)

            else:

                try:

                    number = int(value)

                    marked.append(
                        number in called
                    )

                except:

                    marked.append(False)


        # ------------------------------
        # ROWS
        # ------------------------------

        for row in range(5):

            indexes = [

                row * 5,
                row * 5 + 1,
                row * 5 + 2,
                row * 5 + 3,
                row * 5 + 4

            ]


            if all(
                marked[i]
                for i in indexes
            ):

                declare_winner(
                    player
                )

                return


        # ------------------------------
        # COLUMNS
        # ------------------------------

        for col in range(5):

            indexes = [

                col,
                col + 5,
                col + 10,
                col + 15,
                col + 20

            ]


            if all(
                marked[i]
                for i in indexes
            ):

                declare_winner(
                    player
                )

                return


        # ------------------------------
        # DIAGONAL 1
        # ------------------------------

        diagonal_1 = [
            0,
            6,
            12,
            18,
            24
        ]


        if all(
            marked[i]
            for i in diagonal_1
        ):

            declare_winner(
                player
            )

            return


        # ------------------------------
        # DIAGONAL 2
        # ------------------------------

        diagonal_2 = [
            4,
            8,
            12,
            16,
            20
        ]


        if all(
            marked[i]
            for i in diagonal_2
        ):

            declare_winner(
                player
            )

            return


# ==========================================
# DECLARE WINNER
# ==========================================

def declare_winner(player):

    if game["winner"] is not None:

        return


    game["winner"] = {

        "id":
            player["id"],

        "name":
            player["name"]

    }


    game["status"] = "winner"

    game["winner_time"] = time.time()


    print(
        f"🏆 WINNER: "
        f"{player['name']}"
    )


# ==========================================
# START NEW ROUND
# ==========================================

def start_new_round():

    game["round"] += 1

    game["status"] = "picking"

    game["round_started_at"] = time.time()

    game["last_call_at"] = None

    game["winner_time"] = None

    game["players"] = []

    game["called_numbers"] = []

    game["winner"] = None


    print(
        f"🔄 New Round "
        f"{game['round']} started!"
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

    check_winner()


    return jsonify({

        "success": True,

        "called_numbers":
            game["called_numbers"],

        "winner":
            game["winner"]

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
