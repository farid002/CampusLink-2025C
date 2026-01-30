# -*- coding: utf-8 -*-
"""
polls_speech.py — Polls Speech-to-Text modulu (Workshop 2)

Bu modul audio faylından OpenAI Whisper API ilə mətn çıxarır,
sonra GPT Chat API ilə transkripti sorğu seçimlərinə uyğunlaşdırır.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from database import get_db
import os
import datetime
import secrets
import json
from dotenv import load_dotenv

load_dotenv()

bp = Blueprint("polls_speech", __name__, url_prefix="/polls")

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

def match_speech_to_poll_option(transcribed_text: str, options: list) -> int:
    """
    GPT Chat API istifadə edərək səs transkriptini sorğu seçimlərinə uyğunlaşdırır.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Prompt hazırla (seçimlərə uyğunlaşdırma üçün)
    3. API çağırışı et (gpt-3.5-turbo model)
    4. Seçim indeksini qaytar (0, 1, 2, ...)
    
    Nümunə prompt:
    "Bu mətn hansı seçimə uyğundur? Yalnız rəqəm qaytar (0, 1, 2, və s.).\n\nSeçimlər:\n{options}\n\nMətn: {transcribed_text}"
    """
    api_key = get_gpt_api_key()
    
    # TODO: Tələbə burada kod yazmalıdır
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key)
    # options_str = "\n".join([f"{i}. {opt}" for i, opt in enumerate(options)])
    # prompt = f"Bu mətn hansı seçimə uyğundur? Yalnız rəqəm qaytar (0, 1, 2, və s.).\n\nSeçimlər:\n{options_str}\n\nMətn: {transcribed_text}\n\nCavab: Yalnız indeks rəqəmi (0, 1, 2, ...)"
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.1,
    #     max_tokens=10
    # )
    # content = response.choices[0].message.content.strip()
    # # Rəqəmi çıxar
    # import re
    # numbers = re.findall(r'\d+', content)
    # if numbers:
    #     index = int(numbers[0])
    #     if 0 <= index < len(options):
    #         return index
    # # Fallback: mətn uyğunluğuna görə tap
    # transcribed_lower = transcribed_text.lower()
    # for i, opt in enumerate(options):
    #     if opt.lower() in transcribed_lower or transcribed_lower in opt.lower():
    #         return i
    # raise ValueError("Seçim tapılmadı")
    
    return -1

@bp.route("/<int:poll_id>/speech-vote", methods=["GET", "POST"])
def speech_vote(poll_id: int):
    """
    Səs ilə sorğuya səs vermə.
    
    GET: Audio yükləmə formu
    POST: Audio yükləyir, Whisper ilə transkript edir, GPT ilə uyğunlaşdırır və DB-yə yazır
    """
    db = get_db()
    
    # Sorğunu yoxla
    cursor = db.execute("SELECT * FROM polls WHERE id = ?", (poll_id,))
    poll = cursor.fetchone()
    if not poll:
        return render_template("404.html"), 404
    
    poll_dict = dict(poll)
    options = json.loads(poll_dict["options_json"])
    
    # Sorğu bağlıdırsa
    if poll_dict["is_closed"]:
        flash("Sorğu bağlıdır, səs vermək mümkün deyil.", "error")
        return redirect(url_for("polls.detail", poll_id=poll_id))
    
    # Artıq səs veribsə
    if session.get(f"voted_{poll_id}"):
        flash("Siz artıq bu sorğuya səs vermisiniz.", "error")
        return redirect(url_for("polls.detail", poll_id=poll_id))
    
    if request.method == "POST":
        if 'audio' not in request.files:
            flash("Audio faylı seçilməyib.", "error")
            return redirect(url_for("polls_speech.speech_vote", poll_id=poll_id))
        
        file = request.files['audio']
        if file.filename == '':
            flash("Audio faylı seçilməyib.", "error")
            return redirect(url_for("polls_speech.speech_vote", poll_id=poll_id))
        
        # Audio faylını yüklə
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'mp3'
        filename = f"{secrets.token_hex(8)}.{ext}"
        audio_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        try:
            file.save(audio_path)
            
            # Whisper ilə transkript et
            transcribed_text = transcribe_audio_with_whisper(audio_path)
            
            # GPT ilə seçimə uyğunlaşdır
            matched_option_index = match_speech_to_poll_option(transcribed_text, options)
            
            if matched_option_index < 0 or matched_option_index >= len(options):
                flash("Seçim tapılmadı. Zəhmət olmasa yenidən cəhd edin.", "error")
                return redirect(url_for("polls_speech.speech_vote", poll_id=poll_id))
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO poll_speech_votes (poll_id, audio_filename, transcribed_text, matched_option_index, created_at) VALUES (?, ?, ?, ?, ?)",
                (poll_id, filename, transcribed_text, matched_option_index, created_at)
            )
            db.commit()
            
            # Səs vermə qeydini sessiyaya yaz
            session[f"voted_{poll_id}"] = True
            
            vote_id = cursor.lastrowid
            flash("Səsiniz qeydə alındı!", "success")
            return redirect(url_for("polls_speech.speech_result", poll_id=poll_id, vote_id=vote_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("polls_speech.speech_vote", poll_id=poll_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("polls_speech.speech_vote", poll_id=poll_id))
    
    return render_template("polls/speech_vote.html", poll=poll_dict, options=options)

@bp.route("/<int:poll_id>/speech/<int:vote_id>")
def speech_result(poll_id: int, vote_id: int):
    """
    Speech vote nəticəsini göstərir.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM poll_speech_votes WHERE id = ? AND poll_id = ?",
        (vote_id, poll_id)
    )
    vote = cursor.fetchone()
    if not vote:
        return render_template("404.html"), 404
    
    # Sorğu seçimlərini al
    cursor = db.execute("SELECT options_json FROM polls WHERE id = ?", (poll_id,))
    poll = cursor.fetchone()
    options = json.loads(poll["options_json"]) if poll else []
    
    vote_dict = dict(vote)
    if vote_dict.get("matched_option_index") is not None:
        vote_dict["matched_option"] = options[vote_dict["matched_option_index"]] if vote_dict["matched_option_index"] < len(options) else "Naməlum"
    else:
        vote_dict["matched_option"] = "Naməlum"
    
    return render_template("polls/speech_result.html", vote=vote_dict, poll_id=poll_id)
