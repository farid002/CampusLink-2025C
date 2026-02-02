# -*- coding: utf-8 -*-
"""
blog_ocr.py — Blog OCR modulu (Workshop 2)

Bu modul blog yazılarına şəkil yükləyib GPT Vision API ilə mətni çıxarır,
sonra GPT Chat API ilə mətni təmizləyir və təkmilləşdirir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
from openai import APIError, OpenAI, RateLimitError
import os
import datetime
import secrets
import base64
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
EXT_TO_MIME = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}

bp = Blueprint("blog_ocr", __name__, url_prefix="/blog")

def get_gpt_api_key():
    """
    Environment variable-dan GPT API açarını alır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key

def extract_text_with_gpt_vision(image_path: str) -> str:
    """
    GPT Vision API ilə şəkilərdən mətn çıxarır.
    """
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    ext = (os.path.splitext(image_path)[1] or "").lower().lstrip(".") or "jpg"
    mime = EXT_TO_MIME.get(ext, "image/jpeg")
    data_url = f"data:{mime};base64,{image_base64}"

    try:
        client = OpenAI(api_key=get_gpt_api_key())
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image. Return the text accurately and completely."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            max_tokens=1000,
        )
        text = (response.choices[0].message.content or "").strip()
        return text if text else "No text found"
    except (RateLimitError, APIError):
        raise
    except Exception as e:
        raise ValueError(f"GPT Vision API error: {str(e)}")

def improve_text_with_gpt(extracted_text: str) -> str:
    """
    GPT Chat API istifadə edərək OCR mətnini təmizləyir və təkmilləşdirir.
    """
    prompt = (
        "Clean this OCR result, fix errors, and structure it. "
        "Make it readable but do not change the content.\n\n"
        f"{extracted_text}"
    )
    try:
        client = OpenAI(api_key=get_gpt_api_key())
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        return (response.choices[0].message.content or "").strip()
    except (RateLimitError, APIError):
        raise
    except Exception as e:
        raise ValueError(f"GPT Chat API error: {str(e)}")

@bp.route("/<int:post_id>/ocr", methods=["GET", "POST"])
def ocr_extract(post_id: int):
    """
    Blog yazısına şəkil yükləyib GPT Vision ilə mətn çıxarır.
    
    GET: Şəkil yükləmə formu göstərir
    POST: Şəkil yükləyir, GPT Vision ilə OCR işlədir, GPT Chat ilə təmizləyir və DB-yə yazır
    """
    db = get_db()
    
    # Blog yazısını yoxla
    cursor = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        return render_template("404.html"), 404
    
    if request.method == "POST":
        if 'image' not in request.files:
            flash("Şəkil faylı seçilməyib.", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))
        
        file = request.files['image']
        if file.filename == '':
            flash("Şəkil faylı seçilməyib.", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))
        
        ext = (file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "jpg")
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            flash("İcazə verilən formatlar: JPG, JPEG, PNG, GIF, WEBP.", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))

        filename = f"{secrets.token_hex(8)}.{ext}"
        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

        try:
            file.save(image_path)
            
            # GPT Vision ilə mətn çıxar
            extracted_text = extract_text_with_gpt_vision(image_path)
            
            # GPT Chat ilə təmizlə
            improved_text = improve_text_with_gpt(extracted_text)
            
            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO blog_ocr_results (post_id, extracted_text, improved_text, image_path, created_at) VALUES (?, ?, ?, ?, ?)",
                (post_id, extracted_text, improved_text, filename, created_at)
            )
            db.commit()
            
            result_id = cursor.lastrowid
            flash("OCR uğurla tamamlandı!", "success")
            return redirect(url_for("blog_ocr.ocr_result", post_id=post_id, result_id=result_id))
            
        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))
        except RateLimitError:
            flash("API limiti aşıldı. Bir az gözləyin və yenidən cəhd edin.", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))
        except APIError as e:
            flash(f"OpenAI API xətası: {str(e)}", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("blog_ocr.ocr_extract", post_id=post_id))
    
    return render_template("blog/ocr_upload.html", post=dict(post))

@bp.route("/<int:post_id>/ocr/<int:result_id>")
def ocr_result(post_id: int, result_id: int):
    """
    OCR nəticəsini göstərir.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM blog_ocr_results WHERE id = ? AND post_id = ?",
        (result_id, post_id)
    )
    result = cursor.fetchone()
    if not result:
        return render_template("404.html"), 404

    return render_template("blog/ocr_result.html", result=dict(result), post_id=post_id)


@bp.route("/<int:post_id>/ocr/<int:result_id>/apply", methods=["POST"])
def ocr_apply_to_post(post_id: int, result_id: int):
    """
    Təkmilləşdirilmiş mətni blog yazısının məzmununa tətbiq edir.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM blog_ocr_results WHERE id = ? AND post_id = ?",
        (result_id, post_id)
    )
    result = cursor.fetchone()
    if not result:
        flash("OCR nəticəsi tapılmadı.", "error")
        return redirect(url_for("blog.detail", post_id=post_id))

    improved_text = (result["improved_text"] or "").strip()
    if not improved_text:
        flash("Təkmilləşdirilmiş mətn boşdur.", "error")
        return redirect(url_for("blog_ocr.ocr_result", post_id=post_id, result_id=result_id))

    cursor = db.execute("SELECT id FROM blog_posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        flash("Blog yazısı tapılmadı.", "error")
        return redirect(url_for("blog.list_posts"))

    db.execute("UPDATE blog_posts SET content = ? WHERE id = ?", (improved_text, post_id))
    db.commit()
    flash("Yazı məzmunu təkmilləşdirilmiş mətnlə yeniləndi.", "success")
    return redirect(url_for("blog.detail", post_id=post_id))
