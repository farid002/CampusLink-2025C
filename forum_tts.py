# -*- coding: utf-8 -*-
"""
forum_tts.py — Forum TTS modulu (Workshop 2)

Bu modul forum mövzularını və cavabları GPT Chat API ilə qısaldır (xülasə),
sonra OpenAI TTS API ilə səs faylına çevirir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
import os
import datetime
import secrets
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

bp = Blueprint("forum_tts", __name__, url_prefix="/forum")

def get_gpt_api_key():
    """
    Environment variable-dan GPT API açarını alır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key

def summarize_with_gpt(content: str) -> str:
    """
    GPT Chat API istifadə edərək mətni qısaldır (xülasə).
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Prompt hazırla (xülasə üçün)
    3. API çağırışı et (gpt-3.5-turbo model)
    4. Cavabı qaytar
    
    Nümunə prompt:
    "Bu forum mesajını 3-4 cümləyə qısalt. Əsas məzmunu saxla, amma detalları çıxar:\n\n{content}"
    """
    api_key = get_gpt_api_key()
    
    # TODO: Tələbə burada kod yazmalıdır
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key)
    # prompt = f"Bu forum mesajını 3-4 cümləyə qısalt. Əsas məzmunu saxla, amma detalları çıxar.\n\nOrijinal mətn:\n{content}\n\nQısa xülasə:"
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.5,
    #     max_tokens=200
    # )
    # return response.choices[0].message.content.strip()
    
    return "TODO: GPT API çağırışı implement edilməlidir"

def create_tts_audio_with_openai(text: str, voice: str = "alloy") -> str:
    """
    OpenAI TTS API ilə mətni səs faylına çevirir.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. TTS API çağırışı et (tts-1 model)
    3. Audio faylını static/audio/forum/ qovluğuna yaz
    4. Fayl adını qaytar
    
    Voice seçimləri: alloy, echo, fable, onyx, nova, shimmer
    """
    # TODO: Tələbə burada kod yazmalıdır
    return "TODO: OpenAI TTS API çağırışı implement edilməlidir"

@bp.route("/<int:topic_id>/tts", methods=["GET", "POST"])
def tts_topic(topic_id: int):
    """
    Forum mövzusu üçün TTS yaradır.
    
    GET: TTS formu
    POST: GPT ilə mövzunu qısaldır, OpenAI TTS ilə audio yaradır və DB-yə yazır
    """
    db = get_db()
    
    # Mövzunu yoxla
    cursor = db.execute("SELECT * FROM forum_topics WHERE id = ?", (topic_id,))
    topic = cursor.fetchone()
    if not topic:
        return render_template("404.html"), 404
    
    if request.method == "POST":
        try:
            # GPT ilə xülasə
            summarized_content = summarize_with_gpt(topic["content"])
            
            # OpenAI TTS audio yarat
            voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
            audio_filename = create_tts_audio_with_openai(summarized_content, voice)
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO forum_tts_files (topic_id, reply_id, audio_filename, summarized_content, created_at) VALUES (?, ?, ?, ?, ?)",
                (topic_id, None, audio_filename, summarized_content, created_at)
            )
            db.commit()
            
            file_id = cursor.lastrowid
            flash("TTS uğurla yaradıldı!", "success")
            return redirect(url_for("forum_tts.tts_player", topic_id=topic_id, file_id=file_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("forum_tts.tts_topic", topic_id=topic_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("forum_tts.tts_topic", topic_id=topic_id))
    
    return render_template("forum/tts_topic.html", topic=dict(topic))

@bp.route("/<int:topic_id>/reply/<int:reply_id>/tts", methods=["GET", "POST"])
def tts_reply(topic_id: int, reply_id: int):
    """
    Forum cavabı üçün TTS yaradır.
    """
    db = get_db()
    
    # Cavabı yoxla
    cursor = db.execute("SELECT * FROM forum_replies WHERE id = ? AND topic_id = ?", (reply_id, topic_id))
    reply = cursor.fetchone()
    if not reply:
        return render_template("404.html"), 404
    
    if request.method == "POST":
        try:
            # GPT ilə xülasə
            summarized_content = summarize_with_gpt(reply["content"])
            
            # OpenAI TTS audio yarat
            voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
            audio_filename = create_tts_audio_with_openai(summarized_content, voice)
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO forum_tts_files (topic_id, reply_id, audio_filename, summarized_content, created_at) VALUES (?, ?, ?, ?, ?)",
                (topic_id, reply_id, audio_filename, summarized_content, created_at)
            )
            db.commit()
            
            file_id = cursor.lastrowid
            flash("TTS uğurla yaradıldı!", "success")
            return redirect(url_for("forum_tts.tts_player", topic_id=topic_id, file_id=file_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("forum_tts.tts_reply", topic_id=topic_id, reply_id=reply_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("forum_tts.tts_reply", topic_id=topic_id, reply_id=reply_id))
    
    return render_template("forum/tts_topic.html", reply=dict(reply), topic_id=topic_id)

@bp.route("/<int:topic_id>/tts/<int:file_id>")
def tts_player(topic_id: int, file_id: int):
    """
    TTS audio player səhifəsi.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM forum_tts_files WHERE id = ? AND topic_id = ?",
        (file_id, topic_id)
    )
    tts_file = cursor.fetchone()
    if not tts_file:
        return render_template("404.html"), 404
    
    return render_template("forum/tts_player.html", tts_file=dict(tts_file), topic_id=topic_id)
