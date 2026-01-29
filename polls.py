# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import json, datetime, secrets

bp = Blueprint("polls", __name__, url_prefix="/polls")
ADMIN_PASS = "admin123"  # demo parol (yalnız dərs məqsədi üçün)


@bp.before_app_request
def ensure_session():
    if "voter_id" not in session:
        session["voter_id"] = secrets.token_hex(8)
    return None


@bp.route("/")
def list_polls():
    db = get_db()
    cursor = db.execute("SELECT * FROM polls ORDER BY id DESC")
    polls = [dict(row) for row in cursor.fetchall()]
    return render_template("polls/list.html", polls=polls)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "GET":
        return render_template("polls/new.html", error=None)

    # POST request
    password = request.form.get("password", "").strip()
    question = request.form.get("question", "").strip()
    options_raw = request.form.get("options", "").strip()

    # Admin password check
    if password != ADMIN_PASS:
        return render_template("polls/new.html", error="Admin parolu səhvdir.")

    # Question validation
    if not question:
        return render_template("polls/new.html", error="Sual boş ola bilməz.")

    # Options validation
    opts = [o.strip() for o in options_raw.splitlines() if o.strip()]
    if len(opts) < 2:
        return render_template("polls/new.html", error="Ən az 2 seçim tələb olunur.")

    # DB INSERT
    db = get_db()
    options_json = json.dumps(opts)
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute(
        "INSERT INTO polls (question, options_json, is_closed, created_at) VALUES (?, ?, 0, ?)",
        (question, options_json, created_at)
    )
    db.commit()

    flash("Sorğu uğurla yaradıldı!", "success")
    return redirect(url_for("polls.list_polls"))


@bp.route("/<int:poll_id>/toggle", methods=["GET", "POST"])
def toggle(poll_id: int):
    # Get password from form (POST) or query parameter (GET)
    password = request.form.get("password") or request.args.get("password", "").strip()

    # Admin password check
    if password != ADMIN_PASS:
        flash("Admin parolu səhvdir.", "error")
        return redirect(url_for("polls.detail", poll_id=poll_id))

    # DB UPDATE
    db = get_db()
    db.execute("UPDATE polls SET is_closed = 1 - is_closed WHERE id=?", (poll_id,))
    db.commit()

    return redirect(url_for("polls.detail", poll_id=poll_id))


@bp.route("/<int:poll_id>", methods=["GET", "POST"])
def detail(poll_id: int):
    db = get_db()

    # Get poll from DB
    cursor = db.execute("SELECT * FROM polls WHERE id=?", (poll_id,))
    poll_row = cursor.fetchone()

    if not poll_row:
        return render_template("404.html"), 404

    poll = dict(poll_row)
    options = json.loads(poll["options_json"])

    # Handle POST (voting)
    if request.method == "POST":
        # Check if poll is closed
        if poll["is_closed"]:
            flash("Sorğu bağlıdır, səs vermək mümkün deyil.", "error")
            return redirect(url_for("polls.detail", poll_id=poll_id))

        # Check if user already voted
        if session.get(f"voted_{poll_id}"):
            flash("Siz artıq bu sorğuya səs vermisiniz.", "error")
            return redirect(url_for("polls.detail", poll_id=poll_id))

        # Get option_index
        try:
            idx = int(request.form.get("option_index", "-1"))
        except ValueError:
            idx = -1

        # Validate option_index
        if 0 <= idx < len(options):
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db.execute(
                "INSERT INTO poll_votes (poll_id, option_index, created_at) VALUES (?, ?, ?)",
                (poll_id, idx, created_at)
            )
            db.commit()
            session[f"voted_{poll_id}"] = True
            flash("Səsiniz qeydə alındı!", "success")
            return redirect(url_for("polls.detail", poll_id=poll_id))
        else:
            flash("Yanlış seçim.", "error")
            return redirect(url_for("polls.detail", poll_id=poll_id))

    # GET: Calculate results
    cursor = db.execute(
        "SELECT option_index, COUNT(*) AS cnt FROM poll_votes WHERE poll_id=? GROUP BY option_index",
        (poll_id,)
    )
    votes = cursor.fetchall()
    counts = {row["option_index"]: row["cnt"] for row in votes}
    total = sum(counts.values()) if counts else 0

    # Build percentages list: (option_name, (count, percentage))
    percentages = []
    for i, opt in enumerate(options):
        count = counts.get(i, 0)
        pct = (count / total * 100) if total > 0 else 0.0
        percentages.append((opt, (count, pct)))

    return render_template("polls/detail.html", poll=poll, options=options, percentages=percentages, total=total)