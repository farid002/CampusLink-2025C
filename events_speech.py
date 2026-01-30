# -*- coding: utf-8 -*-
"""
events_speech.py — Events Speech-to-Text modulu (Workshop 2)

Bu modul audio faylından OpenAI Whisper API ilə mətn çıxarır,
sonra GPT Chat API ilə transkripti strukturlaşdırır (ad, email, mesaj).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
import os
import datetime
import secrets
import json
from dotenv import load_dotenv

load_dotenv()

bp = Blueprint("events_speech", __name__, url_prefix="/events")

def get_gpt_api_key():
    """
    Environment variable-dan GPT API açarını alır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key

def transcribe_audio_with_whisper(audio_path: str) -> str:
    """
    OpenAI Whisper API ilə audio faylından mətn çıxarır.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Audio faylını aç
    3. Whisper API çağırışı et (whisper-1 model)
    4. Transkript mətni qaytar
    
    Nümunə:
    from openai import OpenAI
    
    client = OpenAI(api_key=get_gpt_api_key())
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="az"  # Azərbaycan dili
        )
    return transcript.text
    """
    # TODO: Tələbə burada kod yazmalıdır
    return "TODO: Whisper API çağırışı implement edilməlidir"

def parse_speech_with_gpt(transcribed_text: str) -> dict:
    """
    GPT Chat API istifadə edərək səs transkriptini strukturlaşdırır.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Prompt hazırla (ad, email, mesaj çıxarma üçün)
    3. API çağırışı et (gpt-3.5-turbo model)
    4. JSON formatında cavab al
    5. Dict kimi qaytar
    
    Nümunə prompt:
    "Bu mətndən ad, email və mesajı çıxar. Yalnız JSON formatında qaytar:\n{{\"name\": \"...\", \"email\": \"...\", \"message\": \"...\"}}\n\nMətn: {transcribed_text}"
    """
    api_key = get_gpt_api_key()
    
    # TODO: Tələbə burada kod yazmalıdır
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key)
    # prompt = f"Bu mətndən ad, email və mesajı çıxar. Yalnız JSON formatında qaytar, başqa mətn yazma.\n\nFormat:\n{{\"name\": \"ad\", \"email\": \"email@example.com\", \"message\": \"mesaj mətni\"}}\n\nMətn:\n{transcribed_text}"
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.3,
    #     max_tokens=500
    # )
    # content = response.choices[0].message.content.strip()
    # # JSON-dan dict-ə çevir
    # if "{" in content and "}" in content:
    #     json_start = content.find("{")
    #     json_end = content.rfind("}") + 1
    #     json_str = content[json_start:json_end]
    #     result = json.loads(json_str)
    # else:
    #     result = json.loads(content)
    # return result
    
    return {"name": "TODO", "email": "TODO", "message": "TODO"}

@bp.route("/<int:event_id>/speech-register", methods=["GET", "POST"])
def speech_register(event_id: int):
    """
    Səs ilə tədbirə qeydiyyat.
    
    GET: Audio yükləmə formu göstərir
    POST: Audio yükləyir, Whisper ilə transkript edir, GPT ilə formatlaşdırır və DB-yə yazır
    """
    db = get_db()
    
    # Event-i yoxla
    cursor = db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    if not event:
        return render_template("404.html"), 404
    
    if request.method == "POST":
        if 'audio' not in request.files:
            flash("Audio faylı seçilməyib.", "error")
            return redirect(url_for("events_speech.speech_register", event_id=event_id))
        
        file = request.files['audio']
        if file.filename == '':
            flash("Audio faylı seçilməyib.", "error")
            return redirect(url_for("events_speech.speech_register", event_id=event_id))
        
        # Audio faylını yüklə
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'mp3'
        filename = f"{secrets.token_hex(8)}.{ext}"
        audio_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        try:
            file.save(audio_path)
            
            # Whisper ilə transkript et
            transcribed_text = transcribe_audio_with_whisper(audio_path)
            
            # GPT ilə formatlaşdır
            parsed_data = parse_speech_with_gpt(transcribed_text)
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO event_speech_registrations (event_id, audio_filename, transcribed_text, parsed_data_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (event_id, filename, transcribed_text, json.dumps(parsed_data), created_at)
            )
            db.commit()
            
            reg_id = cursor.lastrowid
            flash("Qeydiyyat uğurla tamamlandı!", "success")
            return redirect(url_for("events_speech.speech_result", event_id=event_id, reg_id=reg_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("events_speech.speech_register", event_id=event_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("events_speech.speech_register", event_id=event_id))
    
    return render_template("events/speech_register.html", event=dict(event))

@bp.route("/<int:event_id>/speech/<int:reg_id>")
def speech_result(event_id: int, reg_id: int):
    """
    Speech qeydiyyat nəticəsini göstərir.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM event_speech_registrations WHERE id = ? AND event_id = ?",
        (reg_id, event_id)
    )
    registration = cursor.fetchone()
    if not registration:
        return render_template("404.html"), 404
    
    reg_dict = dict(registration)
    if reg_dict.get("parsed_data_json"):
        reg_dict["parsed_data"] = json.loads(reg_dict["parsed_data_json"])
    else:
        reg_dict["parsed_data"] = {}
    
    return render_template("events/speech_result.html", registration=reg_dict, event_id=event_id)
