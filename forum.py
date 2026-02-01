# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime
import json
import os
import time
from typing import Optional

from flask import Blueprint, abort, flash, render_template, request, redirect, session, url_for

from database import get_db

bp = Blueprint("forum", __name__, url_prefix="/forum")

ADMIN_CODE = os.getenv("ADMIN_CODE", "1234")  # override via env
ALLOWED_EMOJIS = ["🔥", "✅", "⚠️", "📌", "💡", "🚀", "❗"]
DEBUG_LOG_PATH = "/Users/ilkinmammadov/PycharmProjects/PythonProject/CampusLink-2025C/.cursor/debug.log"
_schema_ready: bool = False


def _now_str() -> str:
    # Keep format consistent with the rest of the project (lexicographically sortable).
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _current_author() -> str:
    # Spec: author from current user else "Anonymous"
    role = session.get("role") or "guest"
    if role == "admin":
        return (session.get("admin_name") or session.get("user_name") or "Anonymous").strip() or "Anonymous"
    return (session.get("user_name") or "Anonymous").strip() or "Anonymous"

def _current_user_display() -> str:
    role = session.get("role") or "guest"
    if role == "admin":
        return (session.get("admin_name") or session.get("user_name") or "Admin").strip() or "Admin"
    if role == "user":
        return (session.get("user_name") or "User").strip() or "User"
    return "Guest"


def _is_admin() -> bool:
    return (session.get("role") or "guest") == "admin"


def _is_logged_in() -> bool:
    return (session.get("role") or "guest") in ("user", "admin")


def _safe_next(next_url: Optional[str]) -> Optional[str]:
    # Only allow local redirects.
    if not next_url:
        return None
    if next_url.startswith("/"):
        return next_url
    return None


def _dlog(hypothesisId: str, location: str, message: str, data: dict, runId: str = "pre") -> None:
    payload = {
        "sessionId": "debug-session",
        "runId": runId,
        "hypothesisId": hypothesisId,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _redirect_login(message: str, next_url: Optional[str]):
    flash(message)
    nxt = _safe_next(next_url) or url_for("forum.list_topics")
    # region agent log
    _dlog("B", "forum.py:_redirect_login", "redirect_to_login", {"role": session.get("role") or "guest", "next": nxt})
    # endregion
    return redirect(url_for("forum.login", next=nxt))


@bp.app_context_processor
def _inject_forum_auth():
    return {"forum_role": session.get("role") or "guest", "forum_name": _current_user_display()}


def ensure_forum_schema() -> None:
    """
    Ensure the forum schema meets the assignment requirements without touching other files.

    The repo already creates `forum_topics` with `is_pinned`; the assignment expects `pinned`.
    We add `pinned` if missing, backfill it from `is_pinned`, and create required indexes.
    """
    global _schema_ready
    if _schema_ready:
        return

    db = get_db()
    db.execute("PRAGMA foreign_keys = ON;")

    # Ensure tables exist in case DB was created elsewhere.
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS forum_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            likes INTEGER NOT NULL DEFAULT 0,
            pinned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS forum_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS forum_topic_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            emoji TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE
        );
        """
    )

    # Add `pinned` column if missing (existing DB uses `is_pinned`).
    cols = [r["name"] for r in db.execute("PRAGMA table_info(forum_topics)").fetchall()]
    if "pinned" not in cols:
        db.execute("ALTER TABLE forum_topics ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0;")
        cols.append("pinned")

    # Keep legacy column too (some code/DBs rely on it).
    if "is_pinned" not in cols:
        db.execute("ALTER TABLE forum_topics ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0;")
        cols.append("is_pinned")

    if "is_pinned" in cols:
        # Backfill pinned from is_pinned (one-way safe backfill).
        db.execute("UPDATE forum_topics SET pinned = COALESCE(pinned, is_pinned) WHERE pinned IS NULL OR pinned = 0;")

    # Add views column if missing.
    if "views" not in cols:
        db.execute("ALTER TABLE forum_topics ADD COLUMN views INTEGER NOT NULL DEFAULT 0;")
        cols.append("views")

    # Indexes (recommended/required by assignment).
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_forum_topics_pinned_created_at ON forum_topics(pinned, created_at);"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_forum_replies_topic_created_at ON forum_replies(topic_id, created_at);"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_forum_reactions_topic_id ON forum_topic_reactions(topic_id, id);"
    )

    # Workshop 2 - Forum TTS: forum_summaries (cache summaries by source_hash+lang)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS forum_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            reply_id INTEGER NOT NULL DEFAULT 0,
            source_hash TEXT NOT NULL,
            lang TEXT NOT NULL DEFAULT 'az',
            summary_text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(kind, topic_id, reply_id, source_hash, lang)
        );
        CREATE INDEX IF NOT EXISTS idx_forum_summaries_source ON forum_summaries(source_hash, lang);
        """
    )

    # Workshop 2 - Forum TTS: ForumAudio table (reply_id=0 for topic-level audio)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS forum_audio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            reply_id INTEGER NOT NULL DEFAULT 0,
            voice TEXT NOT NULL DEFAULT 'alloy',
            lang TEXT NOT NULL DEFAULT 'az',
            summary_hash TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            summary_text TEXT,
            file_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(kind, topic_id, reply_id, voice, lang, source_hash)
        );
        CREATE INDEX IF NOT EXISTS idx_forum_audio_topic ON forum_audio(topic_id);
        CREATE INDEX IF NOT EXISTS idx_forum_audio_source ON forum_audio(source_hash);
        """
    )

    # Forum AI: cache for ask/lazy_summary
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS forum_ai_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            cache_type TEXT NOT NULL,
            cache_key TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(topic_id, cache_type, cache_key)
        );
        CREATE INDEX IF NOT EXISTS idx_forum_ai_cache_topic ON forum_ai_cache(topic_id);
        """
    )

    db.commit()
    _schema_ready = True
    # region agent log
    _dlog(
        "D",
        "forum.py:ensure_forum_schema",
        "schema_ready",
        {"has_pinned": "pinned" in cols, "has_is_pinned": "is_pinned" in cols},
    )
    # endregion


@bp.before_app_request
def _forum_schema_bootstrap():
    # Ensure FK enforcement per request/connection, then ensure schema once per process.
    db = get_db()
    db.execute("PRAGMA foreign_keys = ON;")
    ensure_forum_schema()


@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = _safe_next(request.args.get("next") or request.form.get("next")) or url_for("forum.list_topics")

    if request.method == "GET":
        return render_template("forum/login.html", error=None, next_url=next_url, admin_code_hint=bool(ADMIN_CODE))

    login_type = (request.form.get("login_type") or "user").strip()
    # region agent log
    _dlog(
        "A",
        "forum.py:login",
        "login_post_received",
        {"login_type": login_type, "role_before": session.get("role") or "guest", "has_next": bool(next_url)},
    )
    # endregion

    if login_type == "admin":
        admin_code = (request.form.get("admin_code") or "").strip()
        admin_name = (request.form.get("admin_name") or "").strip()
        if admin_code != ADMIN_CODE:
            return render_template("forum/login.html", error="Wrong admin code.", next_url=next_url, admin_code_hint=bool(ADMIN_CODE))

        session["role"] = "admin"
        if admin_name:
            session["admin_name"] = admin_name[:30]
            session["user_name"] = admin_name[:30]
        else:
            session["admin_name"] = session.get("admin_name") or session.get("user_name") or "Admin"

        # region agent log
        _dlog("A", "forum.py:login", "admin_login_success", {"role_after": session.get("role"), "name_len": len(session.get("admin_name") or "")})
        # endregion
        flash("Logged in as admin.")
        return redirect(next_url)

    user_name = (request.form.get("user_name") or "").strip()
    if not user_name or not (2 <= len(user_name) <= 30):
        return render_template("forum/login.html", error="Username is required (2–30 chars).", next_url=next_url, admin_code_hint=bool(ADMIN_CODE))

    session["user_name"] = user_name
    session["role"] = "user"
    session.pop("admin_name", None)
    # region agent log
    _dlog("A", "forum.py:login", "user_login_success", {"role_after": session.get("role"), "name_len": len(user_name)})
    # endregion
    flash("Logged in.")
    return redirect(next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    next_url = _safe_next(request.form.get("next") or request.args.get("next")) or url_for("forum.list_topics")
    session.pop("role", None)
    session.pop("user_name", None)
    session.pop("admin_name", None)
    flash("Logged out.")
    return redirect(next_url)


@bp.route("/")
def list_topics():
    q = (request.args.get("q") or "").strip()

    where = []
    params = []
    if q:
        where.append("(title LIKE ? COLLATE NOCASE OR content LIKE ? COLLATE NOCASE)")
        like = f"%{q}%"
        params.extend([like, like])

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    sql = f"""
        SELECT *
        FROM forum_topics
        {where_sql}
        ORDER BY pinned DESC, created_at DESC
    """

    db = get_db()
    topics = db.execute(sql, params).fetchall()
    topics = [dict(t) for t in topics]

    topic_ids = [t["id"] for t in topics]
    # Aggregated metadata: replies count, last activity (date + author)
    meta_by_topic = {}
    if topic_ids:
        placeholders = ",".join(["?"] * len(topic_ids))
        meta_rows = db.execute(
            f"""
            SELECT r.topic_id, COUNT(*) AS reply_count, MAX(r.created_at) AS last_activity_at
            FROM forum_replies r
            WHERE r.topic_id IN ({placeholders})
            GROUP BY r.topic_id
            """,
            topic_ids,
        ).fetchall()
        for m in meta_rows:
            m = dict(m)
            aid = db.execute(
                "SELECT author FROM forum_replies WHERE topic_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (m["topic_id"],),
            ).fetchone()
            m["last_activity_author"] = aid["author"] if aid else ""
            meta_by_topic[m["topic_id"]] = m
    # Topics with no replies: use topic created_at and author
    for t in topics:
        tid = t["id"]
        if tid not in meta_by_topic:
            meta_by_topic[tid] = {
                "reply_count": 0,
                "last_activity_at": t["created_at"],
                "last_activity_author": t["author"],
            }

    reactions_by_topic = {}
    if topic_ids:
        placeholders = ",".join(["?"] * len(topic_ids))
        rx_rows = db.execute(
            f"SELECT id, topic_id, emoji FROM forum_topic_reactions WHERE topic_id IN ({placeholders}) ORDER BY id ASC",
            topic_ids,
        ).fetchall()
        for r in rx_rows:
            reactions_by_topic.setdefault(r["topic_id"], []).append(r)

    return render_template(
        "forum/forum_list.html",
        topics=topics,
        meta_by_topic=meta_by_topic,
        q=q,
        is_admin=_is_admin(),
        is_logged_in=_is_logged_in(),
        reactions_by_topic=reactions_by_topic,
        allowed_emojis=ALLOWED_EMOJIS,
        next_url=request.full_path if request.query_string else request.path,
    )


@bp.route("/new", methods=["GET", "POST"])
def new_topic():
    if not _is_logged_in():
        return _redirect_login("Please log in to create a topic.", request.full_path if request.query_string else request.path)

    if request.method == "GET":
        return render_template(
            "forum/new.html",
            error=None,
            title="",
            content="",
            is_admin=_is_admin(),
            is_logged_in=True,
        )

    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()

    if len(title) < 3:
        return render_template(
            "forum/new.html",
            error="Title must be at least 3 characters.",
            title=title,
            content=content,
            is_admin=_is_admin(),
            is_logged_in=True,
        )
    if len(content) < 10:
        return render_template(
            "forum/new.html",
            error="Content must be at least 10 characters.",
            title=title,
            content=content,
            is_admin=_is_admin(),
            is_logged_in=True,
        )

    author = _current_author()
    created_at = _now_str()

    db = get_db()
    cur = db.execute(
        """
        INSERT INTO forum_topics (title, content, author, likes, pinned, created_at, is_pinned)
        VALUES (?, ?, ?, 0, 0, ?, 0)
        """,
        (title, content, author, created_at),
    )
    db.commit()
    topic_id = cur.lastrowid
    return redirect(url_for("forum.detail", topic_id=topic_id))


@bp.route("/<int:topic_id>", methods=["GET", "POST"])
def detail(topic_id: int):
    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        return render_template("404.html"), 404

    # Increment views on GET (topic detail view)
    if request.method == "GET":
        cols = [r["name"] for r in db.execute("PRAGMA table_info(forum_topics)").fetchall()]
        if "views" in cols:
            db.execute("UPDATE forum_topics SET views = COALESCE(views, 0) + 1 WHERE id = ?", (topic_id,))
            db.commit()

    if request.method == "POST":
        if not _is_logged_in():
            return _redirect_login("Please log in to like or reply.", url_for("forum.detail", topic_id=topic_id))
        content = (request.form.get("content") or "").strip()
        if len(content) < 3:
            flash("Reply must be at least 3 characters.")
            return redirect(url_for("forum.detail", topic_id=topic_id))

        author = _current_author()
        created_at = _now_str()
        db.execute(
            """
            INSERT INTO forum_replies (topic_id, content, author, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (topic_id, content, author, created_at),
        )
        db.commit()
        return redirect(url_for("forum.detail", topic_id=topic_id))

    replies = db.execute(
        """
        SELECT *
        FROM forum_replies
        WHERE topic_id = ?
        ORDER BY created_at ASC, id ASC
        """,
        (topic_id,),
    ).fetchall()

    reactions = db.execute(
        "SELECT id, topic_id, emoji FROM forum_topic_reactions WHERE topic_id = ? ORDER BY id ASC",
        (topic_id,),
    ).fetchall()

    return render_template(
        "forum/forum_detail.html",
        topic=topic,
        replies=replies,
        reactions=reactions,
        is_admin=_is_admin(),
        is_logged_in=_is_logged_in(),
        allowed_emojis=ALLOWED_EMOJIS,
        next_url=request.path,
    )


@bp.route("/like/<int:topic_id>", methods=["POST"])
def like(topic_id: int):
    """
    Mövzunu “bəyənmək” (likes sayını 1 artırmaq).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) HTTP method:
         - Təhlükəsizlik baxımından **POST** istifadə edin (GET deyil).
         - `form` və ya `fetch`/AJAX ilə çağırıla bilər.

      2) DB UPDATE:
         - `UPDATE forum_topics SET likes = likes + 1 WHERE id = ?`.
         - `commit()`.

      3) Nəticə:
         - `redirect(url_for("forum.detail", topic_id=topic_id))`
           və ya JSON cavab (əgər AJAX).

      4) Anti-abuse (opsional):
         - Sessiya və ya IP ilə eyni istifadəçinin tez-tez bəyənməsinin qarşısını alın.

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    if not _is_logged_in():
        # region agent log
        _dlog("B", "forum.py:like", "like_denied_guest", {"topic_id": topic_id, "role": session.get("role") or "guest"})
        # endregion
        return _redirect_login("Please log in to like or reply.", url_for("forum.detail", topic_id=topic_id))

    db = get_db()
    cur = db.execute(
        "UPDATE forum_topics SET likes = likes + 1 WHERE id = ?",
        (topic_id,),
    )
    db.commit()
    if cur.rowcount == 0:
        return render_template("404.html"), 404

    nxt = _safe_next(request.args.get("next") or request.form.get("next"))
    return redirect(nxt or url_for("forum.detail", topic_id=topic_id))


@bp.route("/pin/<int:topic_id>", methods=["POST"])
def pin(topic_id: int):
    if not _is_admin():
        if not _is_logged_in():
            return _redirect_login("Please log in as admin to use admin actions.", url_for("forum.detail", topic_id=topic_id))
        flash("Not authorized (admin only).")
        nxt = _safe_next(request.args.get("next") or request.form.get("next"))
        return redirect(nxt or url_for("forum.detail", topic_id=topic_id))

    db = get_db()
    row = db.execute(
        "SELECT COALESCE(pinned, 0) AS pinned FROM forum_topics WHERE id = ?",
        (topic_id,),
    ).fetchone()
    if not row:
        return render_template("404.html"), 404

    new_val = 0 if int(row["pinned"] or 0) == 1 else 1
    # Keep both columns in sync for existing DBs.
    db.execute(
        "UPDATE forum_topics SET pinned = ?, is_pinned = ? WHERE id = ?",
        (new_val, new_val, topic_id),
    )
    db.commit()

    nxt = _safe_next(request.args.get("next") or request.form.get("next"))
    return redirect(nxt or url_for("forum.list_topics"))


@bp.route("/admin")
def admin_view():
    # Backwards-compatible alias: admin login is now inside /forum/login.
    return redirect(url_for("forum.login", next=url_for("forum.list_topics")))


@bp.route("/user")
def user_view():
    # Backwards-compatible alias: user login is now /forum/login.
    return redirect(url_for("forum.login", next=url_for("forum.list_topics")))


@bp.route("/delete/<int:topic_id>", methods=["POST"])
def delete_topic(topic_id: int):
    if not _is_admin():
        if not _is_logged_in():
            return _redirect_login("Please log in as admin to use admin actions.", url_for("forum.detail", topic_id=topic_id))
        flash("Not authorized (admin only).")
        return redirect(url_for("forum.detail", topic_id=topic_id))

    db = get_db()
    db.execute("DELETE FROM forum_topics WHERE id = ?", (topic_id,))
    db.commit()
    flash("Topic deleted.")
    return redirect(url_for("forum.list_topics"))


@bp.route("/edit/<int:topic_id>", methods=["GET", "POST"])
def edit_topic(topic_id: int):
    if not _is_admin():
        if not _is_logged_in():
            return _redirect_login("Please log in as admin to use admin actions.", url_for("forum.detail", topic_id=topic_id))
        flash("Not authorized (admin only).")
        return redirect(url_for("forum.detail", topic_id=topic_id))

    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        return render_template("404.html"), 404

    if request.method == "GET":
        return render_template("forum/edit.html", error=None, topic=topic)

    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    if len(title) < 3:
        return render_template("forum/edit.html", error="Title must be at least 3 characters.", topic={**dict(topic), "title": title, "content": content})
    if len(content) < 10:
        return render_template("forum/edit.html", error="Content must be at least 10 characters.", topic={**dict(topic), "title": title, "content": content})

    db.execute("UPDATE forum_topics SET title = ?, content = ? WHERE id = ?", (title, content, topic_id))
    db.commit()
    flash("Topic updated.")
    return redirect(url_for("forum.detail", topic_id=topic_id))


@bp.route("/react/<int:topic_id>", methods=["POST"])
def react(topic_id: int):
    if not _is_admin():
        if not _is_logged_in():
            return _redirect_login("Please log in as admin to use admin actions.", url_for("forum.detail", topic_id=topic_id))
        flash("Not authorized (admin only).")
        return redirect(url_for("forum.detail", topic_id=topic_id))

    emoji = (request.form.get("emoji") or "").strip()
    if emoji not in ALLOWED_EMOJIS:
        flash("Invalid emoji.")
        return redirect(url_for("forum.detail", topic_id=topic_id))

    db = get_db()
    db.execute(
        "INSERT INTO forum_topic_reactions (topic_id, emoji, created_at) VALUES (?, ?, ?)",
        (topic_id, emoji, _now_str()),
    )
    db.commit()
    nxt = _safe_next(request.form.get("next") or request.args.get("next"))
    return redirect(nxt or url_for("forum.detail", topic_id=topic_id))


@bp.route("/unreact/<int:reaction_id>", methods=["POST"])
def unreact(reaction_id: int):
    if not _is_admin():
        if not _is_logged_in():
            return _redirect_login("Please log in as admin to use admin actions.", url_for("forum.list_topics"))
        flash("Not authorized (admin only).")
        return redirect(url_for("forum.list_topics"))

    db = get_db()
    row = db.execute("SELECT topic_id FROM forum_topic_reactions WHERE id = ?", (reaction_id,)).fetchone()
    if not row:
        return render_template("404.html"), 404
    topic_id = row["topic_id"]
    db.execute("DELETE FROM forum_topic_reactions WHERE id = ?", (reaction_id,))
    db.commit()
    nxt = _safe_next(request.form.get("next") or request.args.get("next"))
    return redirect(nxt or url_for("forum.detail", topic_id=topic_id))