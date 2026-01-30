# -*- coding: utf-8 -*-
"""
blog_ocr.py — Blog OCR modulu (Workshop 2)

Bu modul blog yazılarına şəkil yükləyib GPT Vision API ilə mətni çıxarır,
sonra GPT Chat API ilə mətni təmizləyir və təkmilləşdirir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
import os
import datetime
import secrets
import base64
from dotenv import load_dotenv

load_dotenv()

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
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. Şəkili base64-ə çevir
    2. OpenAI client yarat
    3. GPT Vision API çağırışı et (gpt-4o-mini model)
    4. Şəkildəki mətni çıxar
    5. Cavabı qaytar
    
    Nümunə:
    import base64
    from openai import OpenAI
    
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    client = OpenAI(api_key=get_gpt_api_key())
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Bu şəkildəki bütün mətni çıxar. Mətni dəqiq və tam şəkildə qaytar."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }],
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()
    """
    # TODO: Tələbə burada kod yazmalıdır
    return "TODO: GPT Vision API çağırışı implement edilməlidir"

def improve_text_with_gpt(extracted_text: str) -> str:
    """
    GPT Chat API istifadə edərək OCR mətnini təmizləyir və təkmilləşdirir.
    
    TODO: Tələbə bu funksiyanı implement etməlidir:
    1. OpenAI client yarat
    2. Prompt hazırla (OCR nəticəsini təmizləmə üçün)
    3. API çağırışı et (gpt-3.5-turbo model)
    4. Cavabı qaytar
    
    Nümunə prompt:
    "Bu OCR nəticəsini təmizlə, səhvləri düzəlt və strukturlaşdır:\n\n{extracted_text}"
    """
    api_key = get_gpt_api_key()
    
    # TODO: Tələbə burada kod yazmalıdır
    # from openai import OpenAI
    # client = OpenAI(api_key=api_key)
    # prompt = f"Bu OCR nəticəsini təmizlə, səhvləri düzəlt və strukturlaşdır. Mətni daha oxunaqlı et, amma məzmunu dəyişmə:\n\n{extracted_text}"
    # response = client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.3,
    #     max_tokens=1000
    # )
    # return response.choices[0].message.content.strip()
    
    return "TODO: GPT API çağırışı implement edilməlidir"

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
        
        # Şəkili yüklə
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
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
