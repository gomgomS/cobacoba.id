import os
import random
import json
from typing import Dict, Any
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response


APP_TITLE = "Mini RPG"
MAX_PLAYERS = 10
MAP_WIDTH = 900
MAP_HEIGHT = 600
PLAYER_RADIUS = 14

# User data file path
USER_DATA_FILE = "data/users.json"
# Links data file path
LINKS_DATA_FILE = "data/links.json"

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


def load_links():
    """Load links from JSON file"""
    try:
        if os.path.exists(LINKS_DATA_FILE) and os.path.getsize(LINKS_DATA_FILE) > 0:
            with open(LINKS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading links: {e}")
        return []


def save_links(links):
    """Save links to JSON file"""
    try:
        os.makedirs(os.path.dirname(LINKS_DATA_FILE), exist_ok=True)
        with open(LINKS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving links: {e}")
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

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "gomgom")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "gomgom")

def _check_basic_auth(auth) -> bool:
    return bool(auth and auth.username == ADMIN_USERNAME and auth.password == ADMIN_PASSWORD)

def _auth_required() -> Response:
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not _check_basic_auth(auth):
            return _auth_required()
        return f(*args, **kwargs)
    return decorated


def sanitize_id(raw_id: str) -> str:
    """Sanitize an ID for use in URL path (letters, numbers, dash, underscore)."""
    if not raw_id:
        return ""
    cleaned_chars = []
    for ch in raw_id.strip():
        if ch.isalnum() or ch in {"-", "_"}:
            cleaned_chars.append(ch)
    return "".join(cleaned_chars)[:40].lower()


def slugify_name(name: str) -> str:
    """Generate a URL-friendly slug from a name."""
    base = []
    for ch in (name or "").strip().lower():
        if ch.isalnum():
            base.append(ch)
        elif ch in {" ", "-", "_", "."}:
            base.append("-")
        # else drop
    # collapse dashes
    slug = []
    prev_dash = False
    for ch in base:
        if ch == "-":
            if not prev_dash:
                slug.append("-")
            prev_dash = True
        else:
            slug.append(ch)
            prev_dash = False
    slug_str = "".join(slug).strip("-") or "link"
    return slug_str[:40]


RESERVED_IDS = {"admin", "api", "game", "static", ""}


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
        data = request.get_json() or {}
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
        if len(users) >= 20:
            return jsonify({"error": "Maximum 20 users reached"}), 400
        
        # Add new user
        new_user = {
            "id": len(users) + 1,
            "name": name,
            "whatsapp": whatsapp,
            "timestamp": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        # Optional participant fields (from step-2 form)
        optional_fields = [
            "has_laptop",
            "has_data",
            "installed_apps_before",
            "knows_excel_basics",
            "coding_experience",
            "status",
            "reason",
        ]
        for key in optional_fields:
            if key in data:
                new_user[key] = data[key]
        
        users.append(new_user)
        
        # Save to file
        if save_users(users):
            return jsonify({"success": True, "user": new_user, "message": f"Welcome, {name}!"}), 201
        else:
            return jsonify({"error": "Failed to save user data"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/admin/users")
@requires_auth
def admin_users():
    users = load_users()
    return render_template("users.html", title=f"{APP_TITLE} · Users", users=users)


@app.route("/admin/links", methods=["GET"])
@requires_auth
def admin_links():
    links = load_links()
    return render_template("links.html", title=f"{APP_TITLE} · Links", links=links)


@app.route("/admin/links", methods=["POST"])
@requires_auth
def create_link():
    # Accept JSON or form-urlencoded
    data = request.get_json() if request.is_json else request.form.to_dict(flat=True)
    data = data or {}
    name = (data.get("name") or "").strip()
    link = (data.get("link") or "").strip()
    desc = (data.get("desc") or "").strip()
    raw_id = (data.get("id") or "").strip()

    if not name or not link:
        error = "Name and link are required"
        if request.is_json:
            return jsonify({"error": error}), 400
        links = load_links()
        return render_template("links.html", title=f"{APP_TITLE} · Links", links=links, error=error), 400

    links = load_links()
    link_id = sanitize_id(raw_id) or slugify_name(name)

    # Ensure unique ID
    existing_ids = {item.get("id") for item in links}
    base_id = link_id
    suffix = 2
    while link_id in existing_ids or link_id in RESERVED_IDS:
        link_id = f"{base_id}-{suffix}"
        suffix += 1

    new_item = {"id": link_id, "name": name, "link": link, "desc": desc}
    links.append(new_item)

    if save_links(links):
        if request.is_json:
            return jsonify({"success": True, "link": new_item}), 201
        return redirect(url_for("admin_links"))
    else:
        if request.is_json:
            return jsonify({"error": "Failed to save link"}), 500
        links = load_links()
        return render_template("links.html", title=f"{APP_TITLE} · Links", links=links, error="Failed to save link"), 500


@app.route("/<link_id>")
def link_detail(link_id):
    # Avoid catching special prefixes
    if not link_id or link_id in RESERVED_IDS:
        return redirect(url_for("index"))
    items = load_links()
    for item in items:
        if item.get("id") == link_id:
            return render_template("link_detail.html", title=item.get("name") or "Link", item=item)
    return render_template("link_detail.html", title="Not found", item=None), 404


if __name__ == "__main__":
    # For local dev. In production behind a reverse proxy, set host/port via env.
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting {APP_TITLE} on http://localhost:{port}")
    # debug=True provides more logs; disable in production
    app.run(host="0.0.0.0", port=port, debug=True)


