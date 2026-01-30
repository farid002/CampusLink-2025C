# -*- coding: utf-8 -*-
"""
blog_tts.py — Blog TTS modulu (Workshop 2)

Bu modul başlıq və açar sözlərdən GPT Chat API ilə blog yazısı yaradır,
sonra OpenAI TTS API ilə səs faylına çevirir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
import os
import datetime
import secrets
from dotenv import load_dotenv

load_dotenv()

bp = Blueprint("blog_tts", __name__, url_prefix="/blog")

def get_gpt_api_key():
    """
    Environment variable-dan GPT API açarını alır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key

def generate_blog_with_gpt(title: str, keywords: str) -> str:
    """
    GPT Chat API istifadə edərək başlıq və açar sözlərdən blog yazısı yaradır.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Prompt hazırla (başlıq + açar sözlər)
    3. API çağırışı et (gpt-3.5-turbo model)
    4. Cavabı qaytar
    
    Nümunə prompt:
    "Bu başlıq və açar sözlərdən 500 sözlük, maraqlı və informativ blog yazısı yaz:\nBaşlıq: {title}\nAçar sözlər: {keywords}"
    """
    api_key = get_gpt_api_key()
    
    # TODO: Tələbə burada kod yazmalıdır
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key)
    # prompt = f"Bu başlıq və açar sözlərdən 500 sözlük, maraqlı və informativ blog yazısı yaz. Yazı strukturlaşdırılmış, oxunaqlı və məzmunlu olsun.\n\nBaşlıq: {title}\nAçar sözlər: {keywords}\n\nBlog yazısını yalnız mətn kimi qaytar, başqa formatlama olmasın."
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.7,
    #     max_tokens=1000
    # )
    # return response.choices[0].message.content.strip()
    
    return "TODO: GPT API çağırışı implement edilməlidir"

def create_tts_audio_with_openai(text: str, voice: str = "alloy") -> str:
    """
    OpenAI TTS API ilə mətni səs faylına çevirir.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. TTS API çağırışı et (tts-1 model)
    3. Audio faylını static/audio/blog/ qovluğuna yaz
    4. Fayl adını qaytar
    
    Voice seçimləri: alloy, echo, fable, onyx, nova, shimmer
    
    Nümunə:
    from openai import OpenAI
    
    client = OpenAI(api_key=get_gpt_api_key())
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    filename = f"{secrets.token_hex(8)}.mp3"
    audio_path = os.path.join(current_app.config["AUDIO_FOLDER"], "blog", filename)
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    response.stream_to_file(audio_path)
    return f"blog/{filename}"
    """
    # TODO: Tələbə burada kod yazmalıdır
    return "TODO: OpenAI TTS API çağırışı implement edilməlidir"

@bp.route("/<int:post_id>/tts/generate", methods=["GET", "POST"])
def tts_generate(post_id: int):
    """
    Blog yazısı üçün TTS yaradır.
    
    GET: Form göstərir (başlıq + açar sözlər)
    POST: GPT ilə blog yazısı yaradır, OpenAI TTS ilə audio yaradır və DB-yə yazır
    """
    db = get_db()
    
    # Blog yazısını yoxla
    cursor = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return render_template("404.html"), 404
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        keywords = request.form.get("keywords", "").strip()
        
        if not title:
            flash("Başlıq boş ola bilməz.", "error")
            return redirect(url_for("blog_tts.tts_generate", post_id=post_id))
        
        try:
            # GPT ilə blog yazısı yarat
            generated_content = generate_blog_with_gpt(title, keywords)
            
            # OpenAI TTS audio yarat
            voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
            audio_filename = create_tts_audio_with_openai(generated_content, voice)
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO blog_tts_files (post_id, audio_filename, generated_content, created_at) VALUES (?, ?, ?, ?)",
                (post_id, audio_filename, generated_content, created_at)
            )
            db.commit()
            
            file_id = cursor.lastrowid
            flash("Blog yazısı və audio uğurla yaradıldı!", "success")
            return redirect(url_for("blog_tts.tts_player", post_id=post_id, file_id=file_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("blog_tts.tts_generate", post_id=post_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("blog_tts.tts_generate", post_id=post_id))
    
    return render_template("blog/tts_generate.html", post=dict(post))

@bp.route("/<int:post_id>/tts/<int:file_id>")
def tts_player(post_id: int, file_id: int):
    """
    TTS audio player səhifəsi.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM blog_tts_files WHERE id = ? AND post_id = ?",
        (file_id, post_id)
    )
    tts_file = cursor.fetchone()
    if not tts_file:
        return render_template("404.html"), 404
    
    return render_template("blog/tts_player.html", tts_file=dict(tts_file), post_id=post_id)
