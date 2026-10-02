from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time

app = Flask(__name__)
CORS(app)

# =========================================================
# GAME SETTINGS
# =========================================================

PICKING_TIME = 40
CALL_INTERVAL = 3
WINNER_DELAY = 5

TOTAL_CARDS = 96


# =========================================================
# GAME DATA
# =========================================================

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


# =========================================================
# CREATE FIXED BINGO CARDS
# =========================================================

def generate_card(card_number):

    # Use the card number as the random seed.
    # This makes the same Cartela always produce
    # the same Bingo numbers.

    rng = random.Random(card_number)

    # B column: 1 - 15
    b_numbers = list(range(1, 16))
    rng.shuffle(b_numbers)
    b_numbers = b_numbers[:5]

    # I column: 16 - 30
    i_numbers = list(range(16, 31))
    rng.shuffle(i_numbers)
    i_numbers = i_numbers[:5]

    # N column: 31 - 45
    n_numbers = list(range(31, 46))
    rng.shuffle(n_numbers)
    n_numbers = n_numbers[:5]

    # G column: 46 - 60
    g_numbers = list(range(46, 61))
    rng.shuffle(g_numbers)
    g_numbers = g_numbers[:5]

    # O column: 61 - 75
    o_numbers = list(range(61, 76))
    rng.shuffle(o_numbers)
    o_numbers = o_numbers[:5]

    # Create 5 rows
    card = []

    for row in range(5):

        card.append([
            b_numbers[row],
            i_numbers[row],
            n_numbers[row],
            g_numbers[row],
            o_numbers[row]
        ])

    # FREE CENTER
    card[2][2] = "FREE"

    # Convert 5x5 card to one list
    flat_card = []

    for row in card:
        for value in row:
            flat_card.append(value)

    return flat_card


# =========================================================
# CREATE ALL 96 CARTELAS
# =========================================================

CARDS = {}

for card_number in range(1, TOTAL_CARDS + 1):

    CARDS[card_number] = generate_card(card_number)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message": "🎱 Beteseb Bingo Backend is running!",
        "status": "online",
        "round": game["round"],
        "cards": TOTAL_CARDS
    })


# =========================================================
# API TEST
# =========================================================

@app.route("/api/test")
def api_test():

    return jsonify({
        "success": True,
        "message": "Telegram Bingo app connected!"
    })


# =========================================================
# GET ALL CARTELAS
# =========================================================

@app.route("/api/cards")
def get_cards():

    update_game_state()

    reserved_cards = {}

    for player in game["players"]:

        card_number = player.get("card_number")

        if card_number:

            reserved_cards[str(card_number)] = {
                "player": player["name"]
            }

    return jsonify({

        "success": True,

        "round": game["round"],

        "status": game["status"],

        "remaining": get_remaining_time(),

        "cards": CARDS,

        "reserved_cards": reserved_cards

    })


# =========================================================
# GET ONE CARTELA
# =========================================================

@app.route("/api/cards/<int:card_number>")
def get_card(card_number):

    if card_number < 1 or card_number > TOTAL_CARDS:

        return jsonify({
            "success": False,
            "message": "Invalid Cartela number."
        }), 400

    return jsonify({

        "success": True,

        "card_number": card_number,

        "card": CARDS[card_number]

    })


# =========================================================
# GAME STATUS
# =========================================================

@app.route("/api/game-status")
def game_status():

    update_game_state()

    return jsonify({

        "success": True,

        "round": game["round"],

        "status": game["status"],

        "remaining": get_remaining_time(),

        "players": len(game["players"]),

        "called_numbers":
            game["called_numbers"],

        "winner":
            game["winner"]

    })


# =========================================================
# GET REMAINING TIME
# =========================================================

def get_remaining_time():

    if game["status"] == "picking":

        elapsed = (
            time.time()
            - game["round_started_at"]
        )

        return max(
            0,
            PICKING_TIME - int(elapsed)
        )

    if game["status"] == "winner":

        if game["winner_time"] is None:

            return WINNER_DELAY

        elapsed = (
            time.time()
            - game["winner_time"]
        )

        return max(
            0,
            WINNER_DELAY - int(elapsed)
        )

    return 0


# =========================================================
# SELECT CARTELA
# =========================================================

@app.route(
    "/api/select-card",
    methods=["POST"]
)
def select_card():

    update_game_state()

    data = request.get_json() or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    player_name = str(
        data.get(
            "player_name",
            "Player"
        )
    ).strip()

    card_number = data.get(
        "card_number"
    )

    stake = data.get(
        "stake",
        10
    )


    # -----------------------------------------------------
    # VALIDATE PLAYER
    # -----------------------------------------------------

    if not player_id:

        return jsonify({

            "success": False,

            "message":
                "Player ID is required."

        }), 400


    # -----------------------------------------------------
    # VALIDATE CARD NUMBER
    # -----------------------------------------------------

    try:

        card_number = int(
            card_number
        )

    except:

        return jsonify({

            "success": False,

            "message":
                "Invalid Cartela number."

        }), 400


    if (
        card_number < 1
        or
        card_number > TOTAL_CARDS
    ):

        return jsonify({

            "success": False,

            "message":
                "Cartela must be between 1 and 96."

        }), 400


    # -----------------------------------------------------
    # ONLY PICKING PHASE
    # -----------------------------------------------------

    if game["status"] != "picking":

        return jsonify({

            "success": False,

            "message":
                "Cartela selection is closed."

        }), 400


    # -----------------------------------------------------
    # CHECK WHETHER PLAYER ALREADY HAS A CARD
    # -----------------------------------------------------

    existing_player = None

    for player in game["players"]:

        if player["id"] == player_id:

            existing_player = player

            break


    # -----------------------------------------------------
    # CHECK WHETHER CARD BELONGS TO SOMEONE ELSE
    # -----------------------------------------------------

    for player in game["players"]:

        if (
            player.get("card_number")
            == card_number
            and
            player["id"] != player_id
        ):

            return jsonify({

                "success": False,

                "message":
                    "This Cartela is already selected by another player."

            }), 409


    # -----------------------------------------------------
    # UPDATE EXISTING PLAYER
    # -----------------------------------------------------

    if existing_player:

        existing_player["name"] = player_name

        existing_player["card_number"] = card_number

        existing_player["card"] = CARDS[
            card_number
        ]

        existing_player["stake"] = stake


        print(
            f"🎫 {player_name} selected "
            f"Cartela {card_number}"
        )


        return jsonify({

            "success": True,

            "message":
                "Cartela selected successfully.",

            "player":
                existing_player

        })


    # -----------------------------------------------------
    # CREATE NEW PLAYER
    # -----------------------------------------------------

    player = {

        "id":
            player_id,

        "name":
            player_name,

        "card_number":
            card_number,

        "card":
            CARDS[card_number],

        "stake":
            stake,

        "mode":
            "automatic"

    }


    game["players"].append(
        player
    )
    
    update_game_state()

    data = request.get_json() or {}

    player_id = str(data.get("player_id", "")).strip()
    player_name = str(
        data.get("player_name", "Player")
    ).strip()

    card_number = data.get("card_number")
    stake = data.get("stake", 10)

    if not player_id:
        return jsonify({
            "success": False,
            "message": "Player ID is required."
        }), 400

    try:
        card_number = int(card_number)
    except:
        return jsonify({
            "success": False,
            "message": "Invalid Cartela number."
        }), 400

    if card_number < 1 or card_number > TOTAL_CARDS:
        return jsonify({
            "success": False,
            "message": "Cartela must be between 1 and 96."
        }), 400

    if game["status"] != "picking":
        return jsonify({
            "success": False,
            "message": "Cartela selection is closed."
        }), 400

    # Find this player
    existing_player = None

    for player in game["players"]:
        if player["id"] == player_id:
            existing_player = player
            break

    # Check if another player already owns this Cartela
    for player in game["players"]:

        if player["id"] == player_id:
            continue

        if card_number in player.get("card_numbers", []):

            return jsonify({
                "success": False,
                "message":
                    "This Cartela is already selected by another player."
            }), 409

    # Existing player
    if existing_player:

        selected_cards = existing_player.get(
            "card_numbers", []
        )

        # Already selected
        if card_number in selected_cards:

            return jsonify({
                "success": False,
                "message":
                    "You already selected this Cartela."
            }), 409

        # Maximum 3 Cartelas
        if len(selected_cards) >= 3:

            return jsonify({
                "success": False,
                "message":
                    "You can select a maximum of 3 Cartelas."
            }), 400

        selected_cards.append(card_number)

        existing_player["card_numbers"] = selected_cards

        existing_player["cards"] = [
            CARDS[number]
            for number in selected_cards
        ]

        existing_player["name"] = player_name
        existing_player["stake"] = stake

        print(
            f"🎫 {player_name} added Cartela {card_number}"
        )

        return jsonify({
            "success": True,
            "message":
                "Cartela added successfully.",
            "player":
                existing_player
        })

    # New player
    player = {

        "id": player_id,

        "name": player_name,

        "card_numbers": [
            card_number
        ],

        "cards": [
            CARDS[card_number]
        ],

        "stake": stake,

        "mode": "automatic"
    }

    game["players"].append(player)

    print(
        f"👤 {player_name} joined with Cartela {card_number}"
    )

    return jsonify({
        "success": True,
        "message":
            "Cartela selected successfully.",

        "round":
            game["round"],

        "player":
            player
    })

@app.route(
    "/api/leave",
    methods=["POST"]
)
def leave():

    data = request.get_json() or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()


    if not player_id:

        return jsonify({

            "success": False,

            "message":
                "Player ID is required."

        }), 400


    original_count = len(
        game["players"]
    )


    game["players"] = [

        player

        for player in game["players"]

        if player["id"] != player_id

    ]


    if len(game["players"]) == original_count:

        return jsonify({

            "success": False,

            "message":
                "Player was not found."

        })


    return jsonify({

        "success": True,

        "message":
            "Player left the round."

    })


# =========================================================
# UPDATE GAME STATE
# =========================================================

def update_game_state():

    now = time.time()


    # =====================================================
    # PICKING → PLAYING
    # =====================================================

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


    # =====================================================
    # PLAYING
    # =====================================================

    elif game["status"] == "playing":

        if game["last_call_at"] is None:

            game["last_call_at"] = now


        if (
            now
            - game["last_call_at"]
            >= CALL_INTERVAL
        ):

            call_next_number()

            check_winner()


    # =====================================================
    # WINNER → NEW ROUND
    # =====================================================

    elif game["status"] == "winner":

        if game["winner_time"] is None:

            return


        elapsed = (
            now
            - game["winner_time"]
        )


        if elapsed >= WINNER_DELAY:

            start_new_round()


# =========================================================
# CALL NEXT NUMBER
# =========================================================

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


# =========================================================
# CHECK WINNER
# =========================================================

def check_winner():

    if not game["players"]:

        return


    called = set(
        game["called_numbers"]
    )


    for player in game["players"]:

        card = player["card"]


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


        # -----------------------------------------------
        # ROWS
        # -----------------------------------------------

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


        # -----------------------------------------------
        # COLUMNS
        # -----------------------------------------------

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


        # -----------------------------------------------
        # DIAGONAL 1
        # -----------------------------------------------

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


        # -----------------------------------------------
        # DIAGONAL 2
        # -----------------------------------------------

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


# =========================================================
# DECLARE WINNER
# =========================================================

def declare_winner(player):

    if game["winner"] is not None:

        return


    game["winner"] = {

        "id":
            player["id"],

        "name":
            player["name"],

        "card_number":
            player["card_number"]

    }


    game["status"] = "winner"

    game["winner_time"] = time.time()


    print(
        f"🏆 WINNER: "
        f"{player['name']} "
        f"(Cartela {player['card_number']})"
    )


# =========================================================
# START NEW ROUND
# =========================================================

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


# =========================================================
# MANUAL CALL TEST
# =========================================================

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


# =========================================================
# RUN SERVER
# =========================================================
@app.route("/api/reset-test", methods=["POST"])
def reset_test():
    game["round"] += 1
    game["status"] = "picking"
    game["round_started_at"] = time.time()
    game["last_call_at"] = None
    game["winner_time"] = None
    game["players"] = []
    game["called_numbers"] = []
    game["winner"] = None

    return jsonify({
        "success": True,
        "message": "Test round reset successfully.",
        "round": game["round"],
        "status": game["status"],
        "remaining": PICKING_TIME
    })
    
if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=8000,

        debug=False

    )
