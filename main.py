from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    },
    methods=[
        "GET",
        "POST",
        "OPTIONS"
    ],
    allow_headers=[
        "Content-Type"
    ]
)

# =========================================================
# POSTGRESQL DATABASE
# =========================================================

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is missing."
        )

    conn = psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )

    return conn


def init_database():

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL DEFAULT 'Player',
            balance DOUBLE PRECISION NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            transaction_id TEXT UNIQUE NOT NULL,
            telegram_id TEXT NOT NULL,
            type TEXT NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP
        )
    """)

    conn.commit()

    cur.close()
    conn.close()

# Initialize PostgreSQL database
init_database()

# =========================================================
# GAME SETTINGS
# =========================================================
PICKING_TIME = 40
CALL_INTERVAL = 3
WINNER_DELAY = 5
TOTAL_CARDS = 100

# =========================================================
# GAME DATA
# =========================================================
game = {
    "round": 1,
    "status": "picking",
    "round_started_at": None,
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
    rng = random.Random(card_number)

    b_numbers = list(range(1, 16))
    i_numbers = list(range(16, 31))
    n_numbers = list(range(31, 46))
    g_numbers = list(range(46, 61))
    o_numbers = list(range(61, 76))

    rng.shuffle(b_numbers)
    rng.shuffle(i_numbers)
    rng.shuffle(n_numbers)
    rng.shuffle(g_numbers)
    rng.shuffle(o_numbers)

    b_numbers = b_numbers[:5]
    i_numbers = i_numbers[:5]
    n_numbers = n_numbers[:5]
    g_numbers = g_numbers[:5]
    o_numbers = o_numbers[:5]

    card = []

    for row in range(5):
        card.append([
            b_numbers[row],
            i_numbers[row],
            n_numbers[row],
            g_numbers[row],
            o_numbers[row]
        ])

    card[2][2] = "FREE"

    flat_card = []

    for row in card:
        flat_card.extend(row)

    return flat_card


CARDS = {
    card_number: generate_card(card_number)
    for card_number in range(1, TOTAL_CARDS + 1)
}

# =========================================================
# HELPERS
# =========================================================
def get_remaining_time():

    if game["status"] == "picking":

        if game["round_started_at"] is None:
            return PICKING_TIME

        elapsed = time.time() - game["round_started_at"]

        return max(
            0,
            PICKING_TIME - int(elapsed)
        )

    if game["status"] == "winner":

        if game["winner_time"] is None:
            return WINNER_DELAY

        elapsed = time.time() - game["winner_time"]

        return max(
            0,
            WINNER_DELAY - int(elapsed)
        )

    return 0


def get_player(player_id):

    for player in game["players"]:

        if player["id"] == player_id:
            return player

    return None


def get_reserved_cards():

    reserved_cards = {}

    for player in game["players"]:

        for card_number in player.get(
            "card_numbers",
            []
        ):

            reserved_cards[
                str(card_number)
            ] = {
                "player": player["name"],
                "player_id": player["id"]
            }

    return reserved_cards


def card_has_bingo(
    card,
    called_numbers
):

    called = set(called_numbers)

    marked = []

    for index, value in enumerate(card):

        if (
            index == 12
            or value == "FREE"
        ):

            marked.append(True)

        else:

            try:

                marked.append(
                    int(value)
                    in called
                )

            except (
                TypeError,
                ValueError
            ):

                marked.append(False)

    # ROWS
    for row in range(5):

        indexes = range(
            row * 5,
            row * 5 + 5
        )

        if all(
            marked[i]
            for i in indexes
        ):

            return True

    # COLUMNS
    for col in range(5):

        indexes = [
            col + 5 * row
            for row in range(5)
        ]

        if all(
            marked[i]
            for i in indexes
        ):

            return True

    # DIAGONAL 1
    if all(
        marked[i]
        for i in [
            0,
            6,
            12,
            18,
            24
        ]
    ):

        return True

    # DIAGONAL 2
    if all(
        marked[i]
        for i in [
            4,
            8,
            12,
            16,
            20
        ]
    ):

        return True

    return False


# =========================================================
# HOME
# =========================================================
@app.route("/")
def home():

    return jsonify({
        "message":
            "🎱 ZO BINGO Backend is running!",
        "status":
            "online",
        "round":
            game["round"],
        "cards":
            TOTAL_CARDS
    })


# =========================================================
# API TEST
# =========================================================
@app.route("/api/database-test")
def database_test():

    conn = None
    cur = None

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) AS count FROM users"
        )

        users = cur.fetchone()["count"]

        cur.execute(
            "SELECT COUNT(*) AS count FROM transactions"
        )

        transactions = cur.fetchone()["count"]

        return jsonify({
            "success": True,
            "database": "connected",
            "users": users,
            "transactions": transactions
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "database": "error",
            "message": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# =========================================================
# WALLET
# =========================================================
@app.route("/api/wallet")
def get_wallet():

    telegram_id = str(
        request.args.get(
            "telegram_id",
            ""
        )
    ).strip()

    if not telegram_id:

        return jsonify({
            "success": False,
            "message": "Telegram ID is required."
        }), 400

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = %s
            """,
            (telegram_id,)
        ).fetchone()

        if user is None:

            return jsonify({
                "success": False,
                "message": "Wallet not found."
            }), 404

        return jsonify({
            "success": True,
            "user": dict(user)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        conn.close()
# =========================================================
# GET ALL CARTELAS
# =========================================================
@app.route("/api/cards")
def get_cards():

    update_game_state()

    return jsonify({

        "success":
            True,

        "round":
            game["round"],

        "status":
            game["status"],

        "remaining":
            get_remaining_time(),

        "cards":
            CARDS,

        "reserved_cards":
            get_reserved_cards()

    })


# =========================================================
# GET ONE CARTELA
# =========================================================
@app.route(
    "/api/cards/<int:card_number>"
)
def get_card(card_number):

    if (
        card_number < 1
        or card_number > TOTAL_CARDS
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Invalid Cartela number."

        }), 400

    return jsonify({

        "success":
            True,

        "card_number":
            card_number,

        "card":
            CARDS[card_number]

    })


# =========================================================
# GAME STATUS
# =========================================================
@app.route("/api/game-status")
def game_status():

    update_game_state()

    player_id = str(
        request.args.get(
            "player_id",
            ""
        )
    ).strip()

    my_player = (
        get_player(player_id)
        if player_id
        else None
    )

    return jsonify({

        "success":
            True,

        "round":
            game["round"],

        "status":
            game["status"],

        "remaining":
            get_remaining_time(),

        "players":
            len(game["players"]),

        "called_numbers":
            game["called_numbers"],

        "winner":
            game["winner"],

        "my_card_numbers":
            my_player.get(
                "card_numbers",
                []
            )
            if my_player
            else [],

        "my_cards":
            my_player.get(
                "cards",
                []
            )
            if my_player
            else [],

        "my_mode":
            my_player.get(
                "mode",
                "automatic"
            )
            if my_player
            else None

    })


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

    if not player_id:

        return jsonify({

            "success":
                False,

            "message":
                "Player ID is required."

        }), 400

    try:

        card_number = int(
            card_number
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Invalid Cartela number."

        }), 400

    if (
        card_number < 1
        or card_number > TOTAL_CARDS
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Cartela must be between 1 and 100."

        }), 400

    if game["status"] != "picking":

        return jsonify({

            "success":
                False,

            "message":
                "Cartela selection is closed."

        }), 400

    existing_player = get_player(
        player_id
    )

    # =====================================================
    # CHECK WHETHER ANOTHER PLAYER OWNS THIS CARTELA
    # =====================================================
    for player in game["players"]:

        if player["id"] == player_id:
            continue

        if card_number in player.get(
            "card_numbers",
            []
        ):

            return jsonify({

                "success":
                    False,

                "message":
                    "This Cartela is already selected by another player."

            }), 409

    # =====================================================
    # EXISTING PLAYER
    # =====================================================
    if existing_player:

        selected_cards = \
            existing_player.setdefault(
                "card_numbers",
                []
            )

        if card_number in selected_cards:

            return jsonify({

                "success":
                    False,

                "message":
                    "You already selected this Cartela."

            }), 409

        if len(selected_cards) >= 3:

            return jsonify({

                "success":
                    False,

                "message":
                    "You can select a maximum of 3 Cartelas."

            }), 400

        selected_cards.append(
            card_number
        )

        existing_player["cards"] = [
            CARDS[number]
            for number in selected_cards
        ]

        existing_player["name"] = \
            player_name

        existing_player["stake"] = \
            stake

        return jsonify({

            "success":
                True,

            "message":
                "Cartela added successfully.",

            "round":
                game["round"],

            "player":
                existing_player

        })

    # =====================================================
    # NEW PLAYER
    # =====================================================

    # FIRST CARTELA STARTS THE 40 SECOND TIMER
    if (
        not game["players"]
        and game["round_started_at"] is None
    ):

        game["round_started_at"] = \
            time.time()

        print(
            f"Cartela selection started "
            f"for Round {game['round']}"
        )

    player = {

        "id":
            player_id,

        "name":
            player_name,

        "card_numbers":
            [card_number],

        "cards":
            [CARDS[card_number]],

        "stake":
            stake,

        "mode":
            "automatic"

    }

    game["players"].append(
        player
    )

    print(
        f"👤 {player_name} "
        f"joined with Cartela "
        f"{card_number}"
    )

    return jsonify({

        "success":
            True,

        "message":
            "Cartela selected successfully.",

        "round":
            game["round"],

        "player":
            player

    })


# =========================================================
# DESELECT CARTELA
# =========================================================
@app.route(
    "/api/deselect-card",
    methods=["POST"]
)
def deselect_card():

    update_game_state()

    data = request.get_json() or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    card_number = data.get(
        "card_number"
    )

    if not player_id:

        return jsonify({

            "success":
                False,

            "message":
                "Player ID is required."

        }), 400

    try:

        card_number = int(
            card_number
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Invalid Cartela number."

        }), 400

    if game["status"] != "picking":

        return jsonify({

            "success":
                False,

            "message":
                "Cartela selection is closed."

        }), 400

    player = get_player(
        player_id
    )

    if player is None:

        return jsonify({

            "success":
                False,

            "message":
                "Player was not found."

        }), 404

    if card_number not in player.get(
        "card_numbers",
        []
    ):

        return jsonify({

            "success":
                False,

            "message":
                "This Cartela is not selected by you."

        }), 404

    player["card_numbers"].remove(
        card_number
    )

    player["cards"] = [

        CARDS[number]

        for number in
        player["card_numbers"]

    ]

    # REMOVE PLAYER IF NO CARTELAS REMAIN
    if not player["card_numbers"]:

        game["players"] = [

            p

            for p in game["players"]

            if p["id"] != player_id

        ]

    # IF EVERYONE DESELECTS,
    # RESET THE TIMER
    if (
        not game["players"]
        and game["status"] == "picking"
    ):

        game["round_started_at"] = None

    return jsonify({

        "success":
            True,

        "message":
            "Cartela deselected.",

        "player":
            player
            if player["card_numbers"]
            else None,

        "players":
            game["players"]

    })


# =========================================================
# LEAVE ROUND
# =========================================================
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

            "success":
                False,

            "message":
                "Player ID is required."

        }), 400

    original_count = \
        len(game["players"])

    game["players"] = [

        player

        for player in game["players"]

        if player["id"] != player_id

    ]

    if (
        len(game["players"])
        == original_count
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Player was not found."

        }), 404

    # IF EVERYONE LEAVES DURING PICKING,
    # STOP THE TIMER
    if (
        not game["players"]
        and game["status"] == "picking"
    ):

        game["round_started_at"] = None

    return jsonify({

        "success":
            True,

        "message":
            "Player left the round."

    })


# =========================================================
# SET PLAYER MODE
# =========================================================
@app.route(
    "/api/set-mode",
    methods=["POST"]
)
def set_mode():

    data = request.get_json() or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    mode = str(
        data.get(
            "mode",
            "automatic"
        )
    ).strip().lower()

    if mode not in (
        "automatic",
        "manual",
        "watch"
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Mode must be automatic, manual, or watch."

        }), 400

    player = get_player(
        player_id
    )

    if player is None:

        return jsonify({

            "success":
                False,

            "message":
                "Player was not found."

        }), 404

    player["mode"] = mode

    return jsonify({

        "success":
            True,

        "message":
            "Mode updated.",

        "player":
            player

    })


# =========================================================
# MANUAL BINGO CLAIM
# =========================================================
@app.route(
    "/api/bingo",
    methods=["POST"]
)
def bingo_claim():

    update_game_state()

    data = request.get_json() or {}

    player_id = str(
        data.get(
            "player_id",
            ""
        )
    ).strip()

    card_number = data.get(
        "card_number"
    )

    if not player_id:

        return jsonify({

            "success":
                False,

            "message":
                "Player ID is required."

        }), 400

    player = get_player(
        player_id
    )

    if player is None:

        return jsonify({

            "success":
                False,

            "message":
                "Player was not found."

        }), 404

    if game["status"] != "playing":

        return jsonify({

            "success":
                False,

            "message":
                "The game is not currently playing."

        }), 400

    try:

        card_number = int(
            card_number
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Invalid Cartela number."

        }), 400

    if card_number not in player.get(
        "card_numbers",
        []
    ):

        return jsonify({

            "success":
                False,

            "message":
                "This Cartela does not belong to you."

        }), 403

    card = CARDS[
        card_number
    ]

    if card_has_bingo(
        card,
        game["called_numbers"]
    ):

        declare_winner(
            player,
            card_number
        )

        return jsonify({

            "success":
                True,

            "message":
                "BINGO! Valid claim.",

            "winner":
                game["winner"]

        })

    return jsonify({

        "success":
            False,

        "message":
            "BINGO is not valid yet."

    }), 400


# =========================================================
# UPDATE GAME STATE
# =========================================================
def update_game_state():

    now = time.time()

    # =====================================================
    # PICKING
    # =====================================================
    if game["status"] == "picking":

        # NO PLAYERS:
        # WAIT FOREVER
        if (
            not game["players"]
            or game["round_started_at"] is None
        ):

            return

        elapsed = \
            now - game["round_started_at"]

        # 40 SECONDS FINISHED
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

        # SAFETY:
        # NEVER PLAY WITHOUT PLAYERS
        if not game["players"]:

            game["status"] = "picking"

            game["round_started_at"] = None

            game["last_call_at"] = None

            game["winner_time"] = None

            game["called_numbers"] = []

            game["winner"] = None

            return

        if game["last_call_at"] is None:

            game["last_call_at"] = now

        if (
            now - game["last_call_at"]
            >= CALL_INTERVAL
        ):

            call_next_number()

            check_winner()

    # =====================================================
    # WINNER
    # =====================================================
    elif game["status"] == "winner":

        if game["winner_time"] is None:

            return

        elapsed = \
            now - game["winner_time"]

        if elapsed >= WINNER_DELAY:

            start_new_round()


# =========================================================
# CALL NEXT NUMBER
# =========================================================
def call_next_number():

    available = [

        number

        for number in range(
            1,
            76
        )

        if number not in
        game["called_numbers"]

    ]

    if not available:

        return

    number = random.choice(
        available
    )

    game["called_numbers"].append(
        number
    )

    game["last_call_at"] = \
        time.time()

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

    if (
        not game["players"]
        or game["winner"] is not None
    ):

        return

    for player in game["players"]:

        for card_number in player.get(
            "card_numbers",
            []
        ):

            card = CARDS[
                card_number
            ]

            if card_has_bingo(
                card,
                game["called_numbers"]
            ):

                declare_winner(
                    player,
                    card_number
                )

                return


# =========================================================
# DECLARE WINNER
# =========================================================
def declare_winner(
    player,
    card_number
):

    if game["winner"] is not None:

        return

    game["winner"] = {

        "id":
            player["id"],

        "name":
            player["name"],

        "card_number":
            card_number

    }

    game["status"] = "winner"

    game["winner_time"] = \
        time.time()

    print(
        f"🏆 WINNER: "
        f"{player['name']} "
        f"(Cartela "
        f"{card_number})"
    )


# =========================================================
# START COMPLETELY FRESH NEW ROUND
# =========================================================
def start_new_round():

    game["round"] += 1

    game["status"] = "picking"

    # IMPORTANT:
    # NO TIMER UNTIL FIRST CARTELA
    game["round_started_at"] = None

    game["last_call_at"] = None

    game["winner_time"] = None

    # IMPORTANT:
    # COMPLETELY REMOVE ALL OLD PLAYERS
    game["players"] = []

    # IMPORTANT:
    # REMOVE ALL OLD CALLED NUMBERS
    game["called_numbers"] = []

    # IMPORTANT:
    # REMOVE OLD WINNER
    game["winner"] = None

    print(
        f"🔄 NEW ROUND "
        f"{game['round']} "
        f"WAITING FOR FIRST CARTELA"
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

            "success":
                False,

            "message":
                "Game is not playing."

        }), 400

    call_next_number()

    check_winner()

    return jsonify({

        "success":
            True,

        "called_numbers":
            game["called_numbers"],

        "winner":
            game["winner"]

    })


# =========================================================
# RESET TEST ROUND
# =========================================================
@app.route(
    "/api/reset-test",
    methods=["POST"]
)
def reset_test():

    game["round"] += 1

    game["status"] = "picking"

    # IMPORTANT:
    # RESET EVERYTHING
    game["round_started_at"] = None

    game["last_call_at"] = None

    game["winner_time"] = None

    game["players"] = []

    game["called_numbers"] = []

    game["winner"] = None

    return jsonify({

        "success":
            True,

        "message":
            "Test round reset successfully.",

        "round":
            game["round"],

        "status":
            game["status"],

        "remaining":
            PICKING_TIME

    })


# =========================================================
# RUN SERVER
# =========================================================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
