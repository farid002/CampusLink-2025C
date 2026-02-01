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
import re

load_dotenv()

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
    Şəkili base64-ə çevirir, GPT Vision API çağırır, üz sayını parse edir.
    """
    if not os.path.isfile(image_path):
        return 0

    with open(image_path, "rb") as f:
        image_data = f.read()
    base64_image = base64.b64encode(image_data).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png" if ext == ".png" else "image/jpeg"
    image_url = f"data:{mime};base64,{base64_image}"

    api_key = get_gpt_api_key()
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Bu şəkildə neçə insan üzü var? Yalnız rəqəm qaytar (0, 1, 2, 3 və s.). Heç bir mətn yazma."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }],
            max_tokens=20
        )
        content = (response.choices[0].message.content or "").strip()
        numbers = re.findall(r"\d+", content)
        return int(numbers[0]) if numbers else 0
    except Exception as e:
        raise ValueError(f"GPT Vision API xətası: {str(e)}")

def generate_description_with_gpt(face_count: int) -> tuple:
    """
    GPT Chat API istifadə edərək şəkil təsviri və teqlər yaradır.
    Üz sayına əsasən prompt hazırlayır, təsvir və teqləri parse edir.
    """
    api_key = get_gpt_api_key()
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    if face_count == 0:
        prompt = "Bu şəkildə üz yoxdur. Şəkil haqqında qısa təsvir və 5 teq yarat. Cavabı mütləq bu formatta ver: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    elif face_count == 1:
        prompt = "Bu şəkildə 1 üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Cavabı mütləq bu formatta ver: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    else:
        prompt = f"Bu şəkildə {face_count} üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Cavabı mütləq bu formatta ver: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        content = (response.choices[0].message.content or "").strip()
        if "|" in content:
            parts = content.split("|", 1)
            description = parts[0].replace("Təsvir:", "").strip()
            tags = parts[1].replace("Teqlər:", "").strip()
        else:
            description = content
            tags = "şəkil, foto"
        return description or "Təsvir yoxdur.", tags or "şəkil"
    except Exception as e:
        raise ValueError(f"GPT Chat API xətası: {str(e)}")

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
