import os
import random
import json
import time
from typing import Dict, Any
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response


APP_TITLE = "gomgom.id"
MAX_PLAYERS = 10
MAP_WIDTH = 900
MAP_HEIGHT = 600
PLAYER_RADIUS = 14

# User data file path
USER_DATA_FILE = "data/users.json"
# Links data file path
LINKS_DATA_FILE = "data/links.json"
# Schedules data file path
SCHEDULES_DATA_FILE = "data/schedules.json"
# Articles data file path
ARTICLES_DATA_FILE = "data/articles.json"
CV_FILE = "mycv"

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


def load_schedules():
    """Load schedules from JSON file"""
    try:
        if os.path.exists(SCHEDULES_DATA_FILE) and os.path.getsize(SCHEDULES_DATA_FILE) > 0:
            with open(SCHEDULES_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading schedules: {e}")
        return []


def save_schedules(items):
    """Save schedules to JSON file"""
    try:
        os.makedirs(os.path.dirname(SCHEDULES_DATA_FILE), exist_ok=True)
        with open(SCHEDULES_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving schedules: {e}")
        return False


def load_articles():
    """Load articles from JSON file"""
    try:
        if os.path.exists(ARTICLES_DATA_FILE) and os.path.getsize(ARTICLES_DATA_FILE) > 0:
            with open(ARTICLES_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading articles: {e}")
        return []


def save_articles(items):
    """Save articles to JSON file"""
    try:
        os.makedirs(os.path.dirname(ARTICLES_DATA_FILE), exist_ok=True)
        with open(ARTICLES_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving articles: {e}")
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


RESERVED_IDS = {"admin", "api", "game", "static", "schedule", ""}


@app.route("/")
def index():
    # Render CV from text file
    try:
        with open(CV_FILE, 'r', encoding='utf-8') as f:
            cv_text = f.read()
    except Exception:
        cv_text = ""
    meta = parse_cv_meta(cv_text)
    return render_template(
        "cv.html",
        title=f"{APP_TITLE} · CV",
        cv_text=cv_text,
        cv_meta=meta,
    )


@app.route("/apply-class")
def apply_class():
    return render_template("index.html", title=f"{APP_TITLE} · Apply Class")



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
    archives = []
    try:
        for fname in sorted(os.listdir("data")):
            if fname.startswith("users_") and fname.endswith(".json") and fname != os.path.basename(USER_DATA_FILE):
                archives.append(fname[:-5])  # drop .json
    except FileNotFoundError:
        pass
    return render_template("users.html", title=f"{APP_TITLE} · Users", users=users, archives=archives)


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
    while link_id in existing_ids or link_id in RESERVED_IDS or link_id.startswith("users_"):
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


@app.route("/admin/schedules", methods=["GET"])
@requires_auth
def admin_schedules():
    items = load_schedules()
    # sort by date then type
    items = sorted(items, key=lambda x: (x.get("date") or "", x.get("type") or "", x.get("id") or ""))
    return render_template("schedules.html", title=f"{APP_TITLE} · Schedules", items=items)


@app.route("/admin/schedules", methods=["POST"])
@requires_auth
def create_schedule():
    data = request.form.to_dict(flat=True)
    date = (data.get("date") or "").strip()
    desc = (data.get("desc") or "").strip()
    type_ = (data.get("type") or "").strip() or "activity"
    if not date or not desc:
        items = load_schedules()
        return render_template("schedules.html", title=f"{APP_TITLE} · Schedules", items=items, error="Date and description are required"), 400
    items = load_schedules()
    new_id = f"sch-{int(time.time()*1000)}"
    items.append({"id": new_id, "date": date, "desc": desc, "type": type_})
    if save_schedules(items):
        return redirect(url_for("admin_schedules"))
    items = load_schedules()
    return render_template("schedules.html", title=f"{APP_TITLE} · Schedules", items=items, error="Failed to save"), 500


@app.route("/admin/schedules/delete", methods=["POST"])
@requires_auth
def delete_schedule():
    sched_id = (request.form.get("id") or "").strip()
    if not sched_id:
        return redirect(url_for("admin_schedules"))
    items = load_schedules()
    items = [it for it in items if it.get("id") != sched_id]
    save_schedules(items)
    return redirect(url_for("admin_schedules"))


@app.route("/admin/schedules/<sched_id>", methods=["GET", "POST"])
@requires_auth
def edit_schedule(sched_id):
    items = load_schedules()
    idx = next((i for i, it in enumerate(items) if it.get("id") == sched_id), None)
    if idx is None:
        return redirect(url_for("admin_schedules"))
    if request.method == "POST":
        data = request.form.to_dict(flat=True)
        date = (data.get("date") or "").strip()
        desc = (data.get("desc") or "").strip()
        type_ = (data.get("type") or "").strip() or "activity"
        if not date or not desc:
            return render_template("schedules_edit.html", title=f"{APP_TITLE} · Edit Schedule", item=items[idx], error="Date and description are required")
        items[idx]["date"] = date
        items[idx]["desc"] = desc
        items[idx]["type"] = type_
        if save_schedules(items):
            return redirect(url_for("admin_schedules"))
        return render_template("schedules_edit.html", title=f"{APP_TITLE} · Edit Schedule", item=items[idx], error="Failed to save")
    return render_template("schedules_edit.html", title=f"{APP_TITLE} · Edit Schedule", item=items[idx])


@app.route("/api/schedules", methods=["GET"])
def api_schedules():
    items = load_schedules()
    items = sorted(items, key=lambda x: (x.get("date") or "", x.get("type") or "", x.get("id") or ""))
    return jsonify(items)


@app.route("/schedule")
def schedule_page():
    return render_template("schedule.html", title=f"{APP_TITLE} · Schedule")


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


# --- Users batch archive ---
def sanitize_batch_name(raw: str) -> str:
    if not raw:
        return ""
    cleaned_chars = []
    for ch in raw.strip():
        if ch.isalnum() or ch in {"_", "-"}:
            cleaned_chars.append(ch)
    return "".join(cleaned_chars)[:64]


@app.route("/admin/users/archive", methods=["POST"])
@requires_auth
def archive_users():
    batch = (request.form.get("batch_name") or "").strip()
    batch = sanitize_batch_name(batch)
    if not batch:
        users = load_users()
        archives = []
        try:
            for fname in sorted(os.listdir("data")):
                if fname.startswith("users_") and fname.endswith(".json") and fname != os.path.basename(USER_DATA_FILE):
                    archives.append(fname[:-5])
        except FileNotFoundError:
            pass
        return render_template("users.html", title=f"{APP_TITLE} · Users", users=users, archives=archives, error="Batch name required"), 400

    # Ensure filename ends with .json and is in data directory
    archive_file = f"{batch}.json" if batch.startswith("users_") else f"users_{batch}.json"
    archive_path = os.path.join("data", archive_file)
    if os.path.exists(archive_path):
        users = load_users()
        archives = []
        try:
            for fname in sorted(os.listdir("data")):
                if fname.startswith("users_") and fname.endswith(".json") and fname != os.path.basename(USER_DATA_FILE):
                    archives.append(fname[:-5])
        except FileNotFoundError:
            pass
        return render_template("users.html", title=f"{APP_TITLE} · Users", users=users, archives=archives, error="Archive already exists"), 400

    current_users = load_users()
    # Save current users into archive
    try:
        os.makedirs("data", exist_ok=True)
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(current_users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        users = load_users()
        return render_template("users.html", title=f"{APP_TITLE} · Users", users=users, error=f"Failed to write archive: {e}"), 500

    # Clear users.json
    save_users([])
    return redirect(url_for("admin_users"))


@app.route("/users_<batch>")
def view_users_batch(batch):
    batch = sanitize_batch_name(batch)
    if not batch:
        return redirect(url_for("index"))
    archive_path = os.path.join("data", f"users_{batch}.json") if not batch.startswith("users_") else os.path.join("data", f"{batch}.json")
    if not os.path.exists(archive_path):
        return Response("Not Found", 404)
    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []
    return render_template("users.html", title=f"{APP_TITLE} · {batch}", users=data)


def parse_cv_meta(cv_text: str) -> Dict[str, Any]:
    """Lightweight parsing of plain-text CV into basic meta fields for UI."""
    lines = [ln.strip() for ln in (cv_text or "").splitlines()]
    lines = [ln for ln in lines if ln]
    data: Dict[str, Any] = {
        "name": "",
        "title": "",
        "location": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "skills": [],
        "certifications": [],
        "experiences": [],
    }

    # Contact block
    try:
        cidx = next(i for i, ln in enumerate(lines) if ln.lower() == "contact")
        if cidx is not None:
            # location is first non-empty after contact
            for j in range(cidx + 1, min(cidx + 6, len(lines))):
                if not data["location"] and lines[j] and "@" not in lines[j] and "linkedin.com" not in lines[j].lower():
                    data["location"] = lines[j]
                    break
    except StopIteration:
        pass

    # Simple detectors
    for ln in lines:
        low = ln.lower()
        if ("@" in ln) and not data["email"]:
            data["email"] = ln
        if ("linkedin.com" in low) and not data["linkedin"]:
            data["linkedin"] = ln if ln.startswith("http") else f"https://{ln}" if not ln.startswith("www.") else f"https://{ln}"
        if any(ch.isdigit() for ch in ln) and ("mobile" in low or ln.replace(" ", "").replace("+", "").replace("-", "").isdigit()) and not data["phone"]:
            data["phone"] = ln

    # Name and title heuristics
    dev_idx = next((i for i, ln in enumerate(lines) if any(w in ln.lower() for w in ["developer", "engineer", "programmer"])) , None)
    if dev_idx is not None and dev_idx > 0:
        data["title"] = lines[dev_idx]
        data["name"] = lines[dev_idx - 1]
    else:
        # fallback: first non Contact/section line with spaces
        data["name"] = next((ln for ln in lines if " " in ln and ln.lower() not in {"contact", "top skills", "certifications", "experience", "education"}), "")

    # Skills
    try:
        sidx = next(i for i, ln in enumerate(lines) if ln.lower() == "top skills")
        eidx = next((i for i, ln in enumerate(lines[sidx+1:], start=sidx+1) if ln.lower() in {"certifications", "experience", "education"}), len(lines))
        data["skills"] = [ln for ln in lines[sidx+1:eidx] if ln]
    except StopIteration:
        pass

    # Certifications
    try:
        cidx = next(i for i, ln in enumerate(lines) if ln.lower() == "certifications")
        eidx = next((i for i, ln in enumerate(lines[cidx+1:], start=cidx+1) if ln.lower() in {"experience", "education"} or ln == data["name"]), len(lines))
        data["certifications"] = [ln for ln in lines[cidx+1:eidx] if ln]
    except StopIteration:
        pass

    # Experiences (greedy, simple heuristic)
    try:
        ex_start = next(i for i, ln in enumerate(lines) if ln.lower() == "experience") + 1
        ex_end = next((i for i, ln in enumerate(lines[ex_start:], start=ex_start) if ln.lower() in {"education", "skills", "top skills", "certifications"}), len(lines))
        i = ex_start
        while i < ex_end:
            company = lines[i] if i < ex_end else ""
            role = lines[i+1] if i+1 < ex_end else ""
            dates_line = lines[i+2] if i+2 < ex_end else ""
            loc_line = lines[i+3] if i+3 < ex_end else ""

            # Validate minimal structure
            if not company or ":" in company.lower():
                i += 1
                continue
            # Ensure dates look like a range
            if "-" not in dates_line and "Present" not in dates_line:
                # shift if needed
                i += 1
                continue

            bullets = []
            j = i + 4
            while j < ex_end:
                ln = lines[j]
                if ln.lower() in {"project key roles", "technologies"}:
                    j += 1
                    continue
                # bullet lines
                if ln.startswith("-"):
                    bullets.append(ln.lstrip("- "))
                    j += 1
                    continue
                # next entry boundary heuristic: short title-case line without colon and not starting with '-'
                if (len(ln) < 60 and ":" not in ln and not ln.startswith("-") and not any(k in ln.lower() for k in ["month", "year", "present", "area"])):
                    break
                # otherwise skip lines within description
                j += 1

            data["experiences"].append({
                "company": company,
                "role": role,
                "dates": dates_line,
                "location": loc_line if ("area" in loc_line.lower() or "indonesia" in loc_line.lower()) else "",
                "bullets": bullets,
            })

            i = j
    except StopIteration:
        pass

    return data


# --- Articles CMS ---

def _find_article_index_by_id(items: list, article_id: str):
    return next((i for i, it in enumerate(items) if (it.get("id") or "") == article_id), None)


@app.route("/admin/articles", methods=["GET"])
@requires_auth
def admin_articles():
    items = load_articles()
    # sort by created desc if available
    try:
        items = sorted(items, key=lambda x: x.get("created_ts", 0), reverse=True)
    except Exception:
        pass
    return render_template("articles.html", title=f"{APP_TITLE} · Articles", items=items)


@app.route("/admin/articles", methods=["POST"])
@requires_auth
def create_article():
    # Accept JSON or form-urlencoded
    data = request.get_json() if request.is_json else request.form.to_dict(flat=True)
    data = data or {}
    title = (data.get("title") or "").strip()
    raw_id = (data.get("id") or "").strip()
    external_link = (data.get("external_link") or "").strip()
    blocks_json = data.get("blocks_json")
    if request.is_json:
        blocks = data.get("blocks") or []
    else:
        try:
            blocks = json.loads(blocks_json) if blocks_json else []
        except Exception:
            blocks = []

    if not title:
        items = load_articles()
        return render_template("articles.html", title=f"{APP_TITLE} · Articles", items=items, error="Title is required"), 400

    items = load_articles()
    art_id = sanitize_id(raw_id) or slugify_name(title)

    # Ensure unique ID
    existing_ids = {item.get("id") for item in items}
    base_id = art_id
    suffix = 2
    while art_id in existing_ids or art_id in RESERVED_IDS or art_id.startswith("users_"):
        art_id = f"{base_id}-{suffix}"
        suffix += 1

    new_item = {
        "id": art_id,
        "title": title,
        "external_link": external_link,
        "blocks": blocks,
        "created_ts": int(time.time() * 1000),
        "updated_ts": int(time.time() * 1000),
    }
    items.append(new_item)
    if save_articles(items):
        if request.is_json:
            return jsonify({"success": True, "article": new_item}), 201
        return redirect(url_for("admin_articles"))
    else:
        if request.is_json:
            return jsonify({"error": "Failed to save article"}), 500
        items = load_articles()
        return render_template("articles.html", title=f"{APP_TITLE} · Articles", items=items, error="Failed to save article"), 500


@app.route("/admin/articles/<article_id>", methods=["GET", "POST"])
@requires_auth
def edit_article(article_id):
    items = load_articles()
    idx = _find_article_index_by_id(items, article_id)
    if idx is None:
        return redirect(url_for("admin_articles"))

    if request.method == "POST":
        data = request.form.to_dict(flat=True)
        title = (data.get("title") or "").strip()
        external_link = (data.get("external_link") or "").strip()
        blocks_json = data.get("blocks_json")
        try:
            blocks = json.loads(blocks_json) if blocks_json else []
        except Exception:
            blocks = []
        if not title:
            return render_template("articles_edit.html", title=f"{APP_TITLE} · Edit Article", item=items[idx], error="Title is required")
        items[idx]["title"] = title
        items[idx]["external_link"] = external_link
        items[idx]["blocks"] = blocks
        items[idx]["updated_ts"] = int(time.time() * 1000)
        if save_articles(items):
            return redirect(url_for("admin_articles"))
        return render_template("articles_edit.html", title=f"{APP_TITLE} · Edit Article", item=items[idx], error="Failed to save")
    return render_template("articles_edit.html", title=f"{APP_TITLE} · Edit Article", item=items[idx])


@app.route("/admin/articles/delete", methods=["POST"])
@requires_auth
def delete_article():
    art_id = (request.form.get("id") or "").strip()
    if not art_id:
        return redirect(url_for("admin_articles"))
    items = load_articles()
    items = [it for it in items if (it.get("id") or "") != art_id]
    save_articles(items)
    return redirect(url_for("admin_articles"))


@app.route("/a/<article_id>")
def article_detail(article_id):
    items = load_articles()
    for item in items:
        if (item.get("id") or "") == article_id:
            return render_template("article_detail.html", title=item.get("title") or "Article", item=item)
    return render_template("article_detail.html", title="Not found", item=None), 404


if __name__ == "__main__":
    # For local dev. In production behind a reverse proxy, set host/port via env.
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting {APP_TITLE} on http://localhost:{port}")
    # debug=True provides more logs; disable in production
    app.run(host="0.0.0.0", port=port, debug=True)


