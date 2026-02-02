# -*- coding: utf-8 -*-
"""
gallery_faces.py — Gallery Face Detection modulu (Workshop 2)

Bu modul şəkillərdə üzləri GPT Vision API ilə tapır,
sonra GPT Chat API ilə şəkil təsviri və teqlər yaradır.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
import os
import datetime
import json
import base64
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

bp = Blueprint("gallery_faces", __name__, url_prefix="/gallery")

def get_gpt_api_key():
    """
    Environment variable-dan GPT API açarını alır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key

def detect_faces_with_gpt_vision(image_path: str) -> int:
    """
    GPT Vision API ilə şəkillərdə üzləri tapır.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. Şəkili base64-ə çevir
    2. OpenAI client yarat
    3. GPT Vision API çağırışı et (gpt-4o-mini model)
    4. Üz sayını al
    5. Rəqəmi qaytar
    
    Nümunə prompt:
    "Bu şəkildə neçə üz var? Yalnız rəqəm qaytar (məsələn: 0, 1, 2, 3 və s.)."
    """
    # TODO: Tələbə burada kod yazmalıdır
    return 0

def generate_description_with_gpt(face_count: int) -> tuple:
    """
    GPT Chat API istifadə edərək şəkil təsviri və teqlər yaradır.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Prompt hazırla (üz sayına əsasən təsvir və teqlər)
    3. API çağırışı et (gpt-3.5-turbo model)
    4. Təsvir və teqləri parse et
    5. Tuple kimi qaytar (description, tags)
    
    Nümunə prompt:
    "Bu şəkildə {face_count} üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    """
    api_key = get_gpt_api_key()
    
    # TODO: Tələbə burada kod yazmalıdır
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key)
    # if face_count == 0:
    #     prompt = "Bu şəkildə üz yoxdur. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    # elif face_count == 1:
    #     prompt = "Bu şəkildə 1 üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    # else:
    #     prompt = f"Bu şəkildə {face_count} üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.7,
    #     max_tokens=200
    # )
    # content = response.choices[0].message.content.strip()
    # # Parse description and tags
    # if "|" in content:
    #     parts = content.split("|", 1)
    #     description = parts[0].replace("Təsvir:", "").strip()
    #     tags_part = parts[1].replace("Teqlər:", "").strip()
    #     tags = tags_part
    # else:
    #     description = content
    #     tags = "şəkil, foto"
    # return description, tags
    
    return "TODO: GPT API çağırışı implement edilməlidir", "TODO"

@bp.route("/<int:image_id>/faces", methods=["GET", "POST"])
def faces_detect(image_id: int):
    """
    Şəkil üzərində üz tapma.
    
    GET: Face detection başlatma formu
    POST: GPT Vision ilə üzləri tapır, GPT Chat ilə təsvir yaradır və DB-yə yazır
    """
    db = get_db()
    
    # Şəkili yoxla
    cursor = db.execute("SELECT * FROM gallery_images WHERE id = ?", (image_id,))
    image = cursor.fetchone()
    if not image:
        return render_template("404.html"), 404
    
    if request.method == "POST":
        try:
            # Şəkil yolunu tap
            image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], image["filename"])
            
            # GPT Vision ilə üzləri tap
            face_count = detect_faces_with_gpt_vision(image_path)
            
            # GPT ilə təsvir və teqlər yarat
            gpt_description, gpt_tags = generate_description_with_gpt(face_count)
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO gallery_faces (image_id, face_count, gpt_description, gpt_tags, created_at) VALUES (?, ?, ?, ?, ?)",
                (image_id, face_count, gpt_description, gpt_tags, created_at)
            )
            db.commit()
            
            result_id = cursor.lastrowid
            flash("Face detection uğurla tamamlandı!", "success")
            return redirect(url_for("gallery_faces.faces_result", image_id=image_id, result_id=result_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("gallery_faces.faces_detect", image_id=image_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("gallery_faces.faces_detect", image_id=image_id))
    
    return render_template("gallery/faces_upload.html", image=dict(image))

@bp.route("/<int:image_id>/faces/<int:result_id>")
def faces_result(image_id: int, result_id: int):
    """
    Face detection nəticəsini göstərir.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM gallery_faces WHERE id = ? AND image_id = ?",
        (result_id, image_id)
    )
    result = cursor.fetchone()
    if not result:
        return render_template("404.html"), 404
    
    return render_template("gallery/faces_result.html", result=dict(result), image_id=image_id)
