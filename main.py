from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import uuid

app = Flask(__name__)
CORS(app)

games = {}


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


# Create a new Bingo room
@app.route("/api/create-room", methods=["POST"])
def create_room():

    room_id = str(uuid.uuid4())[:6].upper()

    games[room_id] = {
        "players": [],
        "called_numbers": [],
        "status": "waiting"
    }

    return jsonify({
        "success": True,
        "room_id": room_id
    })


# Join a Bingo room
@app.route("/api/join-room", methods=["POST"])
def join_room():

    data = request.get_json()

    room_id = data.get("room_id")
    player_name = data.get("player_name", "Player")

    if room_id not in games:
        return jsonify({
            "success": False,
            "message": "Room not found"
        }), 404

    player_id = str(uuid.uuid4())[:8]

    games[room_id]["players"].append({
        "id": player_id,
        "name": player_name
    })

    return jsonify({
        "success": True,
        "player_id": player_id,
        "room_id": room_id,
        "players": games[room_id]["players"]
    })


# Call a Bingo number
@app.route("/api/call-number", methods=["POST"])
def call_number():

    data = request.get_json()

    room_id = data.get("room_id")

    if room_id not in games:
        return jsonify({
            "success": False,
            "message": "Room not found"
        }), 404

    game_data = games[room_id]

    available = [
        n for n in range(1, 76)
        if n not in game_data["called_numbers"]
    ]

    if not available:
        return jsonify({
            "success": False,
            "message": "All numbers have been called"
        })

    number = random.choice(available)

    game_data["called_numbers"].append(number)

    return jsonify({
        "success": True,
        "number": number,
        "called_numbers": game_data["called_numbers"]
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
