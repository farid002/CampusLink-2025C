# -*- coding: utf-8 -*-
"""
forum_tts.py — Forum TTS modulu (Workshop 2)

Summarizes forum topics/replies with OpenAI Chat, converts to MP3 via OpenAI TTS,
caches results, persists metadata in forum_audio table. JSON API for inline UI.
"""

import datetime
import hashlib
import json
import os
import re
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from flask import Blueprint, current_app, jsonify, request
from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from database import get_db
from forum import ensure_forum_schema

load_dotenv()

bp = Blueprint("forum_tts", __name__, url_prefix="/forum")

# Topic-level audio uses reply_id=0 (NOT NULL)
REPLY_ID_TOPIC = 0

# TTS input length limit (OpenAI TTS max ~4096 chars; truncate for quality)
TTS_MAX_CHARS = 1200

# GPT input truncation (approx 3k tokens)
GPT_MAX_CHARS = 12000

# Thread-level AI limits
TOPIC_CONTEXT_CHARS = 1500
REPLY_CONTEXT_CHARS = 600
MAX_REPLIES_FOR_AI = 25

VALID_VOICES = frozenset({"alloy", "echo", "fable", "onyx", "nova", "shimmer"})


def _row_dict(row) -> Optional[dict]:
    """Convert sqlite3.Row to dict."""
    return {k: row[k] for k in row.keys()} if row else None


def get_gpt_api_key() -> str:
    """Load OpenAI API key from .env."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key


def hash_text(text: str) -> str:
    """Deterministic hash for text (sha1, first 16 hex chars)."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def hash_source(content: str) -> str:
    """Hash of original source content for cache key."""
    return hash_text(content)


def _get_audio_folder() -> str:
    """Absolute path to static/audio/forum/."""
    base = current_app.config.get(
        "AUDIO_FOLDER", os.path.join(current_app.root_path, "static", "audio")
    )
    folder = os.path.join(base, "forum")
    os.makedirs(folder, exist_ok=True)
    return folder


def _user_friendly_error(exc: Exception) -> str:
    """Map OpenAI exceptions to user-friendly messages."""
    if isinstance(exc, RateLimitError):
        return "Too many requests. Please try again in a moment."
    if isinstance(exc, APIConnectionError):
        return "Could not reach OpenAI. Check your connection."
    if isinstance(exc, APIError):
        return "API quota exceeded. Please try again later."
    if isinstance(exc, ValueError):
        return str(exc)
    return "An error occurred. Please try again."


def summarize_with_gpt(content: str, lang: str = "az") -> str:
    """
    Summarize content with GPT Chat API. 3-4 sentences, plain text only.
    Enforces language (az = Azerbaijani), no emojis, preserves numbers/names.
    """
    content = (content or "").strip()
    if not content:
        return "Məzmun yoxdur." if lang == "az" else "No content."

    if len(content) > GPT_MAX_CHARS:
        content = content[:GPT_MAX_CHARS] + "..."

    lang_instruction = (
        "Cavabı yalnız Azərbaycan dilində yaz. Emoji istifadə etmə."
        if lang == "az"
        else "Respond in plain text only. No emojis. Preserve numbers, names, and key facts."
    )

    prompt = f"""Bu forum mesajını 3-4 cümləyə qısalt. Əsas məzmunu və nəticəni saxla.
{lang_instruction}
Çıxış: sadə mətn, başlıq və markdown olmasın.

Orijinal mətn:
{content}

Qısa xülasə:"""

    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )
        summary = response.choices[0].message.content.strip()
        return summary or "Xülasə yaradılmadı."
    except (RateLimitError, APIConnectionError, APIError) as e:
        raise ValueError(_user_friendly_error(e))
    except Exception as e:
        raise ValueError(_user_friendly_error(e))


def create_tts_audio_with_openai(text: str, voice: str = "alloy") -> str:
    """
    Convert text to MP3 via OpenAI TTS. Deterministic filename by hash(voice+text).
    If file exists, reuse without API call. Truncates text to TTS_MAX_CHARS.
    Returns relative path: forum/<hash>.mp3
    """
    voice = voice if voice in VALID_VOICES else "alloy"
    text = (text or "").strip()
    if not text:
        text = "Məzmun yoxdur."

    if len(text) > TTS_MAX_CHARS:
        text = text[: TTS_MAX_CHARS - 3].rsplit(" ", 1)[0] + "..."

    name_hash = hash_text(voice + text)
    filename = f"{name_hash}.mp3"
    folder = _get_audio_folder()
    abs_path = os.path.join(folder, filename)

    if os.path.isfile(abs_path):
        return f"forum/{filename}"

    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        response.stream_to_file(abs_path)
        return f"forum/{filename}"
    except (RateLimitError, APIConnectionError, APIError) as e:
        raise ValueError(_user_friendly_error(e))
    except Exception as e:
        raise ValueError(_user_friendly_error(e))


def get_or_create_summary(
    kind: str,
    topic_id: int,
    reply_id: Optional[int],
    content: str,
    lang: str = "az",
) -> str:
    """
    Get or create cached summary. Idempotent: check forum_summaries first.
    Returns summary text.
    """
    ensure_forum_schema()
    db = get_db()
    reply_id_val = int(reply_id) if reply_id is not None else REPLY_ID_TOPIC
    source_hash = hash_source(content or "")

    row = db.execute(
        """
        SELECT summary_text FROM forum_summaries
        WHERE kind = ? AND topic_id = ? AND reply_id = ? AND source_hash = ? AND lang = ?
        """,
        (kind, topic_id, reply_id_val, source_hash, lang),
    ).fetchone()
    if row:
        return row["summary_text"]

    summary = summarize_with_gpt(content, lang)
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute(
        """
        INSERT OR IGNORE INTO forum_summaries
        (kind, topic_id, reply_id, source_hash, lang, summary_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (kind, topic_id, reply_id_val, source_hash, lang, summary, created_at),
    )
    db.commit()
    # Final SELECT (handles race: another request may have inserted)
    row = db.execute(
        """
        SELECT summary_text FROM forum_summaries
        WHERE kind = ? AND topic_id = ? AND reply_id = ? AND source_hash = ? AND lang = ?
        """,
        (kind, topic_id, reply_id_val, source_hash, lang),
    ).fetchone()
    return row["summary_text"] if row else summary


def get_or_create_forum_audio(
    kind: str,
    topic_id: int,
    reply_id: Optional[int],
    content: str,
    voice: str = "alloy",
    lang: str = "az",
) -> dict:
    """
    Idempotent, concurrency-safe: SELECT first, INSERT OR IGNORE, final SELECT.
    Self-healing: if DB record exists but file missing, regenerate and update.
    Prefers cached summary from forum_summaries when generating TTS.
    reply_id=None/0 for topic-level audio.
    """
    ensure_forum_schema()
    db = get_db()

    reply_id_val = int(reply_id) if reply_id is not None else REPLY_ID_TOPIC
    voice = voice if voice in VALID_VOICES else "alloy"
    source_hash = hash_source(content or "")

    # 1. SELECT by unique keys
    row = db.execute(
        """
        SELECT id, file_path, summary_text, summary_hash
        FROM forum_audio
        WHERE kind = ? AND topic_id = ? AND reply_id = ? AND voice = ? AND lang = ? AND source_hash = ?
        """,
        (kind, topic_id, reply_id_val, voice, lang, source_hash),
    ).fetchone()

    if row:
        # 2. Self-healing: verify file exists
        base = current_app.config.get(
            "AUDIO_FOLDER", os.path.join(current_app.root_path, "static", "audio")
        )
        abs_path = os.path.join(base, row["file_path"])
        if os.path.isfile(abs_path):
            return _row_dict(row)
        # File missing: regenerate (prefer cached summary)
        summary = get_or_create_summary(kind, topic_id, reply_id, content, lang)
        summary_hash = hash_text(summary)
        file_path = create_tts_audio_with_openai(summary, voice)
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            """
            UPDATE forum_audio SET file_path = ?, summary_hash = ?, summary_text = ?, created_at = ?
            WHERE id = ?
            """,
            (file_path, summary_hash, summary, created_at, row["id"]),
        )
        db.commit()
        return _row_dict(
            db.execute("SELECT * FROM forum_audio WHERE id = ?", (row["id"],)).fetchone()
        )

    # 3. Generate new (prefer cached summary)
    summary = get_or_create_summary(kind, topic_id, reply_id, content, lang)
    summary_hash = hash_text(summary)
    file_path = create_tts_audio_with_openai(summary, voice)
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # 4. INSERT OR IGNORE (concurrency-safe)
    db.execute(
        """
        INSERT OR IGNORE INTO forum_audio
        (kind, topic_id, reply_id, voice, lang, summary_hash, source_hash, summary_text, file_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (kind, topic_id, reply_id_val, voice, lang, summary_hash, source_hash, summary, file_path, created_at),
    )
    db.commit()

    # 5. Final SELECT (handles race: another request may have inserted)
    row = db.execute(
        """
        SELECT * FROM forum_audio
        WHERE kind = ? AND topic_id = ? AND reply_id = ? AND voice = ? AND lang = ? AND source_hash = ?
        """,
        (kind, topic_id, reply_id_val, voice, lang, source_hash),
    ).fetchone()
    return _row_dict(row)


def _audio_url(file_path: str) -> str:
    """Build static URL for audio file."""
    return f"/static/audio/{file_path}"


# --- JSON API routes ---


@bp.route("/<int:topic_id>/summary", methods=["POST"])
def summary_topic(topic_id: int):
    """Generate/return topic summary. JSON: {ok, summary, summary_id} or {ok: false, error}."""
    ensure_forum_schema()
    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        return jsonify({"ok": False, "error": "Topic not found"}), 404

    lang = (request.json or request.form or {}).get("lang", "az")
    try:
        summary = get_or_create_summary(
            kind="topic",
            topic_id=topic_id,
            reply_id=None,
            content=topic["content"] or "",
            lang=lang,
        )
        row = db.execute(
            """
            SELECT id FROM forum_summaries
            WHERE kind = 'topic' AND topic_id = ? AND reply_id = 0 AND source_hash = ? AND lang = ?
            """,
            (topic_id, hash_source(topic["content"] or ""), lang),
        ).fetchone()
        return jsonify({
            "ok": True,
            "summary": summary,
            "summary_id": row["id"] if row else None,
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _user_friendly_error(e)}), 400


@bp.route("/<int:topic_id>/reply/<int:reply_id>/summary", methods=["POST"])
def summary_reply(topic_id: int, reply_id: int):
    """Generate/return reply summary. JSON: {ok, summary, summary_id} or {ok: false, error}."""
    ensure_forum_schema()
    db = get_db()
    reply = db.execute(
        "SELECT * FROM forum_replies WHERE id = ? AND topic_id = ?",
        (reply_id, topic_id),
    ).fetchone()
    if not reply:
        return jsonify({"ok": False, "error": "Reply not found"}), 404

    lang = (request.json or request.form or {}).get("lang", "az")
    try:
        summary = get_or_create_summary(
            kind="reply",
            topic_id=topic_id,
            reply_id=reply_id,
            content=reply["content"] or "",
            lang=lang,
        )
        row = db.execute(
            """
            SELECT id FROM forum_summaries
            WHERE kind = 'reply' AND topic_id = ? AND reply_id = ? AND source_hash = ? AND lang = ?
            """,
            (topic_id, reply_id, hash_source(reply["content"] or ""), lang),
        ).fetchone()
        return jsonify({
            "ok": True,
            "summary": summary,
            "summary_id": row["id"] if row else None,
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _user_friendly_error(e)}), 400


@bp.route("/<int:topic_id>/tts", methods=["POST"])
def tts_topic(topic_id: int):
    """Generate/return topic audio. JSON: {ok, audio_url, audio_id} or {ok: false, error}."""
    ensure_forum_schema()
    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        return jsonify({"ok": False, "error": "Topic not found"}), 404

    voice = (request.json or request.form or {}).get("voice", "alloy")
    lang = (request.json or request.form or {}).get("lang", "az")
    if voice not in VALID_VOICES:
        voice = "alloy"

    try:
        rec = get_or_create_forum_audio(
            kind="topic",
            topic_id=topic_id,
            reply_id=None,
            content=topic["content"] or "",
            voice=voice,
            lang=lang,
        )
        return jsonify({
            "ok": True,
            "audio_url": _audio_url(rec["file_path"]),
            "audio_id": rec["id"],
            "summary": rec.get("summary_text") or "",
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _user_friendly_error(e)}), 400


@bp.route("/<int:topic_id>/reply/<int:reply_id>/tts", methods=["POST"])
def tts_reply(topic_id: int, reply_id: int):
    """Generate/return reply audio. JSON: {ok, audio_url, audio_id} or {ok: false, error}."""
    ensure_forum_schema()
    db = get_db()
    reply = db.execute(
        "SELECT * FROM forum_replies WHERE id = ? AND topic_id = ?",
        (reply_id, topic_id),
    ).fetchone()
    if not reply:
        return jsonify({"ok": False, "error": "Reply not found"}), 404

    voice = (request.json or request.form or {}).get("voice", "alloy")
    lang = (request.json or request.form or {}).get("lang", "az")
    if voice not in VALID_VOICES:
        voice = "alloy"

    try:
        rec = get_or_create_forum_audio(
            kind="reply",
            topic_id=topic_id,
            reply_id=reply_id,
            content=reply["content"] or "",
            voice=voice,
            lang=lang,
        )
        return jsonify({
            "ok": True,
            "audio_url": _audio_url(rec["file_path"]),
            "audio_id": rec["id"],
            "summary": rec.get("summary_text") or "",
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _user_friendly_error(e)}), 400


@bp.route("/audio/<int:audio_id>", methods=["GET"])
def get_audio(audio_id: int):
    """Return JSON with audio URL and summary."""
    ensure_forum_schema()
    db = get_db()
    row = db.execute("SELECT * FROM forum_audio WHERE id = ?", (audio_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Audio not found"}), 404

    return jsonify({
        "ok": True,
        "audio_url": _audio_url(row["file_path"]),
        "summary": row.get("summary_text") or "",
    })


def _get_thread_context(
    topic_id: int,
    question: Optional[str] = None,
    for_ask: bool = False,
) -> Tuple[dict, List[dict]]:
    """
    Get topic + selected replies for AI. Cost control: max 25 replies, truncate.
    For ask: if >25 replies, select by keyword overlap with question.
    For lazy: if >25 replies, select most recent + longest informative.
    """
    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        raise ValueError("Topic not found")
    topic = dict(topic)
    topic_content = (topic.get("content") or "")[:TOPIC_CONTEXT_CHARS]
    if len(topic.get("content") or "") > TOPIC_CONTEXT_CHARS:
        topic_content += "..."

    replies = db.execute(
        "SELECT id, content, author, created_at FROM forum_replies WHERE topic_id = ? ORDER BY created_at ASC, id ASC",
        (topic_id,),
    ).fetchall()
    replies = [_row_dict(r) for r in replies if r]

    if len(replies) <= MAX_REPLIES_FOR_AI:
        selected = replies
    elif for_ask and question:
        # Keyword overlap: count question words in each reply
        q_words = set(re.findall(r"\w+", (question or "").lower()))
        scored = []
        for r in replies:
            content = (r.get("content") or "").lower()
            overlap = sum(1 for w in q_words if w in content)
            scored.append((overlap, len(content), r))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        selected = [r for _, _, r in scored[:MAX_REPLIES_FOR_AI]]
        selected.sort(key=lambda r: (r["created_at"], r["id"]))
    else:
        # Lazy: most recent + longest
        scored = [(len(r.get("content") or ""), r.get("created_at", ""), r) for r in replies]
        scored.sort(key=lambda x: (-x[0], x[1]))
        selected = [r for _, _, r in scored[:MAX_REPLIES_FOR_AI]]
        selected.sort(key=lambda r: (r["created_at"], r["id"]))

    truncated = []
    for r in selected:
        c = (r.get("content") or "")[:REPLY_CONTEXT_CHARS]
        if len(r.get("content") or "") > REPLY_CONTEXT_CHARS:
            c += "..."
        truncated.append({"id": r["id"], "content": c, "author": r.get("author", "")})
    return {"title": topic.get("title", ""), "content": topic_content}, truncated


def _ask_with_gpt(question: str, topic_title: str, topic_content: str, replies: List[dict], lang: str) -> Tuple[str, List[int]]:
    """Call GPT to answer question about thread. Returns (answer, source_reply_ids)."""
    lang_inst = "Cavabı Azərbaycan dilində yaz." if lang == "az" else "Respond in plain text."
    parts = [f"Başlıq: {topic_title}\n\nMəzmun: {topic_content}\n"]
    for r in replies:
        parts.append(f"Cavab [{r['id']}] ({r.get('author', '')}): {r['content']}\n")
    context = "\n".join(parts)
    prompt = f"""Forum mövzusu və cavabları:
{context}

İstifadəçi sualı: {question}

{lang_inst}
Cavabda yalnız əlaqəli cavablara istinad et. Cavabın sonunda istifadə etdiyin cavab ID-lərini vergüllə yaz: Mənbələr: 1, 3, 5"""

    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        sources = []
        m = re.search(r"(?:Mənbələr|Sources):\s*([\d,\s]+)", text, re.I)
        if m:
            sources = [int(x.strip()) for x in m.group(1).split(",") if x.strip().isdigit()]
            text = re.sub(r"\s*(?:Mənbələr|Sources):[\d,\s]+", "", text, flags=re.I).strip()
        return text, sources
    except (RateLimitError, APIConnectionError, APIError) as e:
        raise ValueError(_user_friendly_error(e))


def _lazy_summary_with_gpt(topic_title: str, topic_content: str, replies: List[dict], lang: str) -> str:
    """Call GPT to generate overall thread summary."""
    lang_inst = "Xülasəni Azərbaycan dilində yaz." if lang == "az" else "Write summary in plain text."
    parts = [f"Başlıq: {topic_title}\n\nMəzmun: {topic_content}\n"]
    for r in replies:
        parts.append(f"Cavab [{r['id']}]: {r['content']}\n")
    context = "\n".join(parts)
    prompt = f"""Forum mövzusu və cavabları:
{context}

{lang_inst}
3-5 cümləlik ümumi xülasə yaz. Əsas məqamları vurğula."""

    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except (RateLimitError, APIConnectionError, APIError) as e:
        raise ValueError(_user_friendly_error(e))


@bp.route("/<int:topic_id>/ask", methods=["POST"])
def ask_topic(topic_id: int):
    """Ask AI about the thread. JSON: {ok, answer, sources} or {ok: false, error}."""
    ensure_forum_schema()
    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        return jsonify({"ok": False, "error": "Topic not found"}), 404

    data = request.json or request.form or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"ok": False, "error": "Question is required"}), 400
    lang = data.get("lang", "az")

    cache_key = hash_text(question + str(topic_id))
    row = db.execute(
        "SELECT result_json FROM forum_ai_cache WHERE topic_id = ? AND cache_type = 'ask' AND cache_key = ?",
        (topic_id, cache_key),
    ).fetchone()
    if row:
        return jsonify(json.loads(row["result_json"]))

    try:
        topic_ctx, replies = _get_thread_context(topic_id, question=question, for_ask=True)
        answer, sources = _ask_with_gpt(
            question, topic_ctx["title"], topic_ctx["content"], replies, lang
        )
        result = {"ok": True, "answer": answer, "sources": sources}
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT OR REPLACE INTO forum_ai_cache (topic_id, cache_type, cache_key, result_json, created_at) VALUES (?, 'ask', ?, ?, ?)",
            (topic_id, cache_key, json.dumps(result), created_at),
        )
        db.commit()
        return jsonify(result)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _user_friendly_error(e)}), 400


@bp.route("/<int:topic_id>/lazy_summary", methods=["POST"])
def lazy_summary_topic(topic_id: int):
    """Lazy summary of thread. JSON: {ok, summary, top_replies} or {ok: false, error}."""
    ensure_forum_schema()
    db = get_db()
    topic = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,)).fetchone()
    if not topic:
        return jsonify({"ok": False, "error": "Topic not found"}), 404

    data = request.json or request.form or {}
    lang = data.get("lang", "az")

    topic_ctx, replies = _get_thread_context(topic_id, for_ask=False)
    cache_key = hash_text(topic_ctx["title"] + topic_ctx["content"] + "|".join(str(r["id"]) for r in replies))
    row = db.execute(
        "SELECT result_json FROM forum_ai_cache WHERE topic_id = ? AND cache_type = 'lazy' AND cache_key = ?",
        (topic_id, cache_key),
    ).fetchone()
    if row:
        return jsonify(json.loads(row["result_json"]))

    try:
        summary = _lazy_summary_with_gpt(
            topic_ctx["title"], topic_ctx["content"], replies, lang
        )
        top_replies = [r["id"] for r in replies]
        result = {"ok": True, "summary": summary, "top_replies": top_replies}
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT OR REPLACE INTO forum_ai_cache (topic_id, cache_type, cache_key, result_json, created_at) VALUES (?, 'lazy', ?, ?, ?)",
            (topic_id, cache_key, json.dumps(result), created_at),
        )
        db.commit()
        return jsonify(result)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": _user_friendly_error(e)}), 400
