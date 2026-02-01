# -*- coding: utf-8 -*-
"""
gallery_detection.py — Gallery Object Detection modulu (Workshop 2)

Bu modul şəkillərdə obyektləri GPT Vision API ilə tapır,
sonra GPT Chat API ilə təbii dildə təsvir edir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import get_db
import os
import datetime
import secrets
import json
import base64
from dotenv import load_dotenv

load_dotenv()

bp = Blueprint("gallery_detection", __name__, url_prefix="/gallery")


def get_gpt_api_key():
    """
    Environment variable-dan GPT API açarını alır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
    return api_key


def _normalize_detection(obj: dict) -> dict:
    """
    Ensures a single detection matches the output spec: class (lowercase singular),
    confidence in [0, 1], bbox [x1, y1, x2, y2] as integers.
    """
    class_name = (obj.get("class") or "object")
    if not isinstance(class_name, str):
        class_name = str(class_name)
    class_name = class_name.strip().lower()
    if not class_name:
        class_name = "object"

    confidence = obj.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    bbox = obj.get("bbox") or []
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        try:
            bbox = [int(round(float(bbox[0]))), int(round(float(bbox[1]))), int(round(float(bbox[2]))),
                    int(round(float(bbox[3])))]
        except (TypeError, ValueError):
            bbox = []
    else:
        bbox = []

    return {"class": class_name, "confidence": confidence, "bbox": bbox}


def analyze_image_brightness(image_path: str) -> dict:
    """
    Şəkilin tünd və ya işıqlı olduğunu müəyyən edir.
    Grayscale ortalama parlaqlığa əsasən "dark" və ya "light" qaytarır.

    Returns:
        dict: {"label": "dark"|"light", "brightness": 0-255}
    """
    import cv2
    if not os.path.isfile(image_path):
        return {"label": "unknown", "brightness": 0}
    img = cv2.imread(image_path)
    if img is None:
        return {"label": "unknown", "brightness": 0}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    label = "light" if brightness >= 128 else "dark"
    return {"label": label, "brightness": round(brightness, 1)}


def detect_objects_with_gpt_vision(image_path: str) -> list:
    """
    YOLOv8n ilə şəkillərdə obyektləri tapır. Nəticə formatı: class (lowercase singular),
    confidence (0-1), bbox [x1, y1, x2, y2] piksel. Heç bir obyekt tapılmazsa [] qaytarır.
    """
    if not os.path.isfile(image_path):
        return []

    try:
        from ultralytics import YOLO
    except ImportError:
        raise ValueError("ultralytics quraşdırılmayıb. pip install ultralytics edin.")

    model = YOLO("yolov8n.pt")
    results = model(image_path, verbose=False)

    out = []
    for r in results:
        if r.boxes is None:
            continue
        names = r.names or {}
        for box in r.boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            class_name = (names.get(cls_id) or "object").strip().lower()
            if not class_name:
                class_name = "object"
            out.append({
                "class": class_name,
                "confidence": round(conf, 4),
                "bbox": [int(round(x)) for x in xyxy]
            })

    return out


def draw_boxes(image_path: str, detections: list, output_path: str):
    """
    OpenCV ilə şəkil üzərində qutular çəkir. Hər detection üçün bbox varsa düzbucaqlı
    və class + confidence etiketini çəkir, nəticəni output_path-ə yazır.
    """
    import cv2

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Şəkil oxuna bilmədi: {image_path}")

    for det in detections:
        bbox = det.get("bbox", [])
        if len(bbox) >= 4:
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            class_name = det.get("class", "object")
            confidence = det.get("confidence", 0.0)
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imwrite(output_path, img)


def describe_objects_with_gpt(detected_objects: list) -> str:
    """
    GPT Chat API istifadə edərək tapılan obyektləri təbii dildə təsvir edir.
    """
    api_key = get_gpt_api_key()

    if not detected_objects:
        return "Şəkildə heç bir obyekt tapılmadı."

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    objects_str = json.dumps(detected_objects, ensure_ascii=False, indent=2)
    prompt = (
        "Bu şəkildə tapılan obyektləri təbii dildə, maraqlı və informativ şəkildə təsvir et. "
        "Obyektlərin sayını, növlərini və ümumi mənzərəni izah et.\n\n"
        f"Tapılan obyektlər:\n{objects_str}\n\n"
        "Cavabı Azərbaycan dilində, 3-4 cümlə ilə qaytar."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip() or "Təsvir alınmadı."
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")


@bp.route("/<int:image_id>/detect", methods=["GET", "POST"])
def detect(image_id: int):
    """
    Şəkil üzərində obyekt tapma.

    GET: Detection başlatma formu
    POST: GPT Vision ilə detection işlədir, qutular çəkir, GPT Chat ilə təsvir edir və DB-yə yazır
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

            # GPT Vision ilə obyektləri tap
            detected_objects = detect_objects_with_gpt_vision(image_path)

            # Qutular çək (əgər bbox varsa)
            result_filename = f"detection_{secrets.token_hex(8)}.jpg"
            result_path = os.path.join(current_app.config["DETECTIONS_FOLDER"], "gallery", result_filename)
            os.makedirs(os.path.dirname(result_path), exist_ok=True)

            if detected_objects and any("bbox" in obj for obj in detected_objects):
                draw_boxes(image_path, detected_objects, result_path)
            else:
                # Bbox yoxdursa, orijinal şəkili kopyala
                import shutil
                shutil.copy(image_path, result_path)

            # GPT ilə təsvir et
            gpt_description = describe_objects_with_gpt(detected_objects)

            # DB-yə yaz
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor = db.execute(
                "INSERT INTO gallery_detections (image_id, detected_objects_json, gpt_description, result_image_path, created_at) VALUES (?, ?, ?, ?, ?)",
                (image_id, json.dumps(detected_objects, ensure_ascii=False), gpt_description, result_filename,
                 created_at)
            )
            db.commit()

            result_id = cursor.lastrowid
            flash("Detection uğurla tamamlandı!", "success")
            return redirect(url_for("gallery_detection.detection_result", image_id=image_id, result_id=result_id))

        except ValueError as e:
            flash(f"Xəta: {str(e)}", "error")
            return redirect(url_for("gallery_detection.detect", image_id=image_id))
        except Exception as e:
            flash(f"Gözlənilməz xəta: {str(e)}", "error")
            return redirect(url_for("gallery_detection.detect", image_id=image_id))

    return render_template("gallery/detection_upload.html", image=dict(image))


@bp.route("/<int:image_id>/detect/<int:result_id>")
def detection_result(image_id: int, result_id: int):
    """
    Detection nəticəsini göstərir.
    """
    db = get_db()
    cursor = db.execute(
        "SELECT * FROM gallery_detections WHERE id = ? AND image_id = ?",
        (result_id, image_id)
    )
    result = cursor.fetchone()
    if not result:
        return render_template("404.html"), 404

    result_dict = dict(result)
    if result_dict.get("detected_objects_json"):
        result_dict["detected_objects"] = json.loads(result_dict["detected_objects_json"])
    else:
        result_dict["detected_objects"] = []

    return render_template("gallery/detection_result.html", result=result_dict, image_id=image_id)