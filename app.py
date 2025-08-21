import os
import random
import json
from typing import Dict, Any

from flask import Flask, render_template, request, redirect, url_for, jsonify


APP_TITLE = "Mini RPG"
MAX_PLAYERS = 10
MAP_WIDTH = 900
MAP_HEIGHT = 600
PLAYER_RADIUS = 14

# User data file path
USER_DATA_FILE = "data/users.json"

def load_users():
    """Load users from JSON file"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def save_users(users):
    """Save users to JSON file"""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False


def sanitize_name(raw_name: str) -> str:
    if not raw_name:
        return ""
    cleaned_chars = []
    for ch in raw_name.strip():
        if ch.isalnum() or ch in {" ", "-", "_", "'"}:
            cleaned_chars.append(ch)
    cleaned = "".join(cleaned_chars)
    return cleaned[:20] if cleaned else "Player"


def random_color() -> str:
    palette = [
        "#e6194B", "#3cb44b", "#ffe119", "#0082c8", "#f58231",
        "#911eb4", "#46f0f0", "#f032e6", "#d2f53c", "#fabebe",
        "#008080", "#e6beff", "#aa6e28", "#fffac8", "#800000",
        "#aaffc3", "#808000", "#ffd8b1", "#000080", "#808080",
    ]
    return random.choice(palette)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")


@app.route("/")
def index():
    return render_template("index.html", title=APP_TITLE)


@app.route("/game")
def game():
    name = request.args.get("name", "").strip()
    if not name:
        return redirect(url_for("index"))
    safe_name = sanitize_name(name)
    return render_template(
        "game.html",
        title=APP_TITLE,
        player_name=safe_name,
        map_width=MAP_WIDTH,
        map_height=MAP_HEIGHT,
        player_radius=PLAYER_RADIUS,
        max_players=MAX_PLAYERS,
    )

@app.route("/api/users", methods=["GET"])
def get_users():
    """Get all registered users"""
    users = load_users()
    return jsonify(users)

@app.route("/api/users", methods=["POST"])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        whatsapp = data.get("whatsapp", "").strip()
        
        if not name or not whatsapp:
            return jsonify({"error": "Name and WhatsApp number are required"}), 400
        
        # Load existing users
        users = load_users()
        
        # Check if user already exists
        for user in users:
            if user["name"].lower() == name.lower() or user["whatsapp"] == whatsapp:
                return jsonify({"error": "User with this name or WhatsApp number already exists"}), 400
        
        # Check maximum users limit
        if len(users) >= 10:
            return jsonify({"error": "Maximum 10 users reached"}), 400
        
        # Add new user
        new_user = {
            "id": len(users) + 1,
            "name": name,
            "whatsapp": whatsapp,
            "timestamp": request.headers.get("X-Forwarded-For", request.remote_addr)
        }
        
        users.append(new_user)
        
        # Save to file
        if save_users(users):
            return jsonify({"success": True, "user": new_user, "message": f"Welcome, {name}!"}), 201
        else:
            return jsonify({"error": "Failed to save user data"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    # For local dev. In production behind a reverse proxy, set host/port via env.
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting {APP_TITLE} on http://localhost:{port}")
    # debug=True provides more logs; disable in production
    app.run(host="0.0.0.0", port=port, debug=True)


