# -*- coding: utf-8 -*-


from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from database import get_db, dict_from_row
import datetime, csv, io, sqlite3

bp = Blueprint("events", __name__, url_prefix="/events")
ADMIN_PASS = "admin123"

@bp.route("/")
def list_events():
    db = get_db()
    cur = db.execute("SELECT * FROM events ORDER BY date ASC")
    rows = cur.fetchall()
    events = []
    for row in rows:
        e = dict_from_row(row)
        cur2 = db.execute("SELECT COUNT(*) AS c FROM event_registrations WHERE event_id = ?", (e["id"],))
        reg_count = cur2.fetchone()[0]
        e["remaining"] = max(0, e["capacity"] - reg_count)
        events.append(e)
    return render_template("events/list.html", events=events)

@bp.route("/create", methods=["GET","POST"])
def create_event():
    if request.method == "GET":
        return render_template("events/create.html", error=None)
    title = (request.form.get("title") or "").strip()
    date = (request.form.get("date") or "").strip()
    location = (request.form.get("location") or "").strip()
    description = (request.form.get("description") or "").strip()
    capacity_raw = request.form.get("capacity") or "100"
    password = (request.form.get("password") or "").strip()
    if password != ADMIN_PASS:
        return render_template("events/create.html", error="Admin parolu səhvdir.")
    if not title or not date or not location or not description:
        return render_template("events/create.html", error="Bütün sahələr doldurulmalıdır.")
    try:
        capacity = int(capacity_raw)
    except (ValueError, TypeError):
        capacity = 100
    db = get_db()
    db.execute(
        "INSERT INTO events (title, date, location, description, capacity) VALUES (?, ?, ?, ?, ?)",
        (title, date, location, description, capacity),
    )
    db.commit()
    return redirect(url_for("events.list_events"))

@bp.route("/<int:event_id>", methods=["GET", "POST"])
def detail(event_id: int):
    db = get_db()
    cur = db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    if not row:
        return render_template("404.html"), 404
    event = dict_from_row(row)
    cur = db.execute("SELECT COUNT(*) FROM event_registrations WHERE event_id = ?", (event_id,))
    reg_count = cur.fetchone()[0]
    remaining = max(0, event["capacity"] - reg_count)
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        if not name or not email:
            flash("Ad və e-poçt mütləqdir.")
            return redirect(url_for("events.detail", event_id=event_id))
        if remaining <= 0:
            flash("Kapasite dolub.")
            return redirect(url_for("events.detail", event_id=event_id))
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            db.execute(
                "INSERT INTO event_registrations (event_id, name, email, created_at) VALUES (?, ?, ?, ?)",
                (event_id, name, email, created_at),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Bu e-poçt ilə artıq qeydiyyatdan keçmisiniz.")
            return redirect(url_for("events.detail", event_id=event_id))
        flash("Qeydiyyat uğurla tamamlandı.")
        return redirect(url_for("events.detail", event_id=event_id))
    cur = db.execute(
        "SELECT * FROM event_registrations WHERE event_id = ? ORDER BY id DESC",
        (event_id,),
    )
    regs = [dict_from_row(r) for r in cur.fetchall()]
    return render_template("events/detail.html", event=event, regs=regs, remaining=remaining)

@bp.route("/<int:event_id>/export.csv")
def export_csv(event_id: int):
    if request.args.get("password") != ADMIN_PASS:
        return "İcazə yoxdur.", 403
    db = get_db()
    cur = db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    if not cur.fetchone():
        return render_template("404.html"), 404
    cur = db.execute(
        "SELECT name, email, created_at FROM event_registrations WHERE event_id = ? ORDER BY id ASC",
        (event_id,),
    )
    rows = cur.fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["name", "email", "created_at"])
    for r in rows:
        w.writerow([r["name"], r["email"], r["created_at"]])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_regs.csv"},
    )

@bp.route("/my-registrations")
def my_regs():
    email = (request.args.get("email") or "").strip()
    if not email:
        return render_template("events/my_registrations.html", email="", items=[])
    db = get_db()
    cur = db.execute(
        "SELECT e.title, e.date, e.location, r.created_at "
        "FROM event_registrations r JOIN events e ON e.id = r.event_id "
        "WHERE r.email = ? ORDER BY r.created_at DESC",
        (email,),
    )
    items = [dict_from_row(r) for r in cur.fetchall()]
    return render_template("events/my_registrations.html", email=email, items=items)