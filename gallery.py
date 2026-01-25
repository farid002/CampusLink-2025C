# -*- coding: utf-8 -*-
"""
gallery.py — Qalereya modulu (SKELETON + TƏLİMAT)

Bu faylda funksiyalar qəsdən “boş” saxlanılıb ki, tələbələr özləri
implement etsinlər. Hər funksiyanın docstring-i addım-addım nə etməli
olduqlarını göstərir.

Təhlükəsizlik qeydi:
- Fayl yükləmə həssas mövzudur. Fayl tipini, ölçüsünü və saxlanacağı yolu diqqətlə yoxlayın.
- Real layihədə əlavə təhlükəsizlik (məs., auth, MIME yoxlanışı) tövsiyə olunur.

Şablonlar:
- templates/gallery/list.html
- templates/gallery/detail.html
- templates/gallery/upload.html
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, abort
from database import get_db
import os, datetime, secrets

bp = Blueprint("gallery", __name__, url_prefix="/gallery")

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_SIZE = 3 * 1024 * 1024  # 3 MB
ADMIN_PASS = "admin123"     # demo parol (yalnız dərs məqsədi üçün)


def allowed(filename: str) -> bool:
    """
    Fayl adından genişlənməni çıxarıb ALLOWED dəstində olub-olmadığını yoxlayır.

    Bu funksiya tələbə tərəfindən GENİŞLƏNDİRİLƏ bilər:
      - MIME tipinə (məs., `file.mimetype`) də baxmaq.
      - Boş/naməlum genişlənmələri rədd etmək.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


@bp.route("/")
def grid():
    """
    Şəkillərin siyahısı (grid) + uploader-a görə filtr.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Query parametri:
         - `uploader = (request.args.get("uploader") or "").strip()`
         - Boşdursa: bütün şəkilləri gətir.
         - Doluysa: `WHERE uploader LIKE ?` ilə daralt.

      2) DB sorğuları:
         - Hamısı üçün: `SELECT * FROM gallery_images ORDER BY id DESC`
         - Filtr üçün:  `SELECT * FROM gallery_images WHERE uploader LIKE ? ORDER BY id DESC`

      3) Şablon:
         - `gallery/list.html` render et.
         - Şablona `images` və `uploader` ötür.

      4) UX ipucları:
         - Yuxarıda “Uploader-a görə filtr” input + “Axtar” düyməsi.
         - Grid üçün Bootstrap `row`/`col` + `card` istifadə edin.
         - Hər kartda: thumbnail (static/uploads/filename), title, uploader, tarix, “Detala bax” linki.

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    uploader = (request.args.get("uploader") or "").strip()
    db = get_db()
    if uploader:
        cur = db.execute(
            "SELECT * FROM gallery_images WHERE uploader LIKE ? ORDER BY id DESC",
            ("%" + uploader + "%",),
        )
    else:
        cur = db.execute("SELECT * FROM gallery_images ORDER BY id DESC")
    images = cur.fetchall()
    return render_template("gallery/list.html", images=images, uploader=uploader)


@bp.route("/<int:image_id>")
def detail(image_id: int):
    """
    Tək şəklin detal səhifəsi (böyük görüntü + metadata).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) DB sorğusu:
         - `SELECT * FROM gallery_images WHERE id=?`
         - Tapılmasa → `render_template("404.html"), 404`

      2) Şablon:
         - `gallery/detail.html` render et, `img` obyektini ötür.
         - Şəkli böyük ölçüdə göstər (src: `/static/uploads/{{ img.filename }}`).

      3) UX ipucları:
         - “Geri qalereyaya” linki.
         - Adminsə (demo): “Delete” linki (parolla qorunan route-a aparsın).

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    db = get_db()
    cur = db.execute("SELECT * FROM gallery_images WHERE id = ?", (image_id,))
    img = cur.fetchone()
    if img is None:
        return render_template("404.html"), 404
    return render_template("gallery/detail.html", img=img)


@bp.route("/<int:image_id>/edit", methods=["GET", "POST"])
def edit(image_id: int):
    """Şəkil məlumatlarını (title, uploader) düzəltmək — admin demo parolla."""
    password = (request.args.get("password") or request.form.get("password") or "").strip()
    if password != ADMIN_PASS:
        abort(403)

    db = get_db()
    cur = db.execute("SELECT * FROM gallery_images WHERE id = ?", (image_id,))
    img = cur.fetchone()
    if img is None:
        return render_template("404.html"), 404

    if request.method == "POST":
        title = (request.form.get("title") or "").strip() or "Başlıqsız"
        uploader = (request.form.get("uploader") or "").strip() or "Anonim"
        db.execute(
            "UPDATE gallery_images SET title = ?, uploader = ? WHERE id = ?",
            (title, uploader, image_id),
        )
        db.commit()
        flash("Dəyişikliklər saxlanıldı.")
        return redirect(url_for("gallery.detail", image_id=image_id))

    return render_template(
        "gallery/edit.html",
        img=img,
        image_id=image_id,
        password=request.args.get("password", ""),
    )


@bp.route("/<int:image_id>/delete", methods=["GET", "POST"])
def delete(image_id: int):
    """
    Şəkli silmək üçün route (admin demo parolla). **Tədris məqsədi** üçün sadə saxlanılıb.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Admin yoxlaması:
         - Sadə demo: ya `request.args.get("password")`, ya da POST formunda `password` alın.
         - `ADMIN_PASS` ilə müqayisə edin; uyğun deyilsə:
           - 403 qaytarın (və ya `delete.html`-də xəta göstərin).

      2) DB və fayl sistemi silinməsi:
         - DB-dən `filename` götürün:
           `SELECT filename FROM gallery_images WHERE id=?`
         - Fayl mövcuddursa silin:
           `os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))`
           - `try/except` istifadə edin ki, fayl artıq yoxdursa səhv yaratmasın.
         - Sonra DB-dən sətiri silin:
           `DELETE FROM gallery_images WHERE id=?`
         - `commit()` edin.

      3) Nəticə:
         - `redirect(url_for("gallery.grid"))` ilə siyahıya qaytarın.

      4) UX ipucları:
         - **Təsdiq səhifəsi** (GET): “Əminsiniz?” sualı + iki düymə (Sil / Geri).
         - **POST**-la silmək daha düzgündür.

    """
    password = (request.args.get("password") or request.form.get("password") or "").strip()
    if password != ADMIN_PASS:
        abort(403)

    db = get_db()
    cur = db.execute("SELECT * FROM gallery_images WHERE id = ?", (image_id,))
    img = cur.fetchone()
    if img is None:
        return render_template("404.html"), 404

    if request.method == "POST":
        filename = img["filename"]
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        try:
            os.remove(path)
        except OSError:
            pass
        db.execute("DELETE FROM gallery_images WHERE id = ?", (image_id,))
        db.commit()
        return redirect(url_for("gallery.grid"))

    return render_template(
        "gallery/delete.html",
        img=img,
        image_id=image_id,
        password=request.args.get("password", ""),
    )


@bp.route("/upload", methods=["GET", "POST"])
def upload():
    """
    Şəkil yükləmə formu (ölçü limiti, tip yoxlaması, unikal adla saxlanma).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) GET:
         - `gallery/upload.html` şablonunu render edin (title, uploader, file input).

      2) POST:
         - Formdan alın:
           - `file = request.files.get("file")`
           - `title = ... or "Başlıqsız"`
           - `uploader = ... or "Anonim"`
         - **Tip yoxlaması**:
           - Fayl var? `file.filename` boş deyil?
           - `allowed(file.filename)` → genişlənmə ALLOWED dəstindədir?
           - Yanlışdırsa: `flash("Zəhmət olmasa şəkil faylı yükləyin (png, jpg, jpeg, gif, webp).")`
             və `redirect(url_for("gallery.upload"))`.

         - **Ölçü limiti** (~3MB):
           - `file.stream.seek(0, os.SEEK_END); size = file.stream.tell(); file.stream.seek(0)`
           - `if size > MAX_SIZE:` → `flash("Fayl ölçüsü 3 MB-dən böyükdür.")` və redirect.

         - **Unikal fayl adı**:
           - `ext = file.filename.rsplit(".", 1)[1].lower()`
           - `filename = f"{secrets.token_hex(8)}.{ext}"`
           - `path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)`
           - `file.save(path)`

         - **DB-yə yaz**:
           - `INSERT INTO gallery_images (title, filename, uploader, created_at) VALUES (?, ?, ?, ?)`
           - `created_at` üçün `datetime.datetime.now().strftime("%Y-%m-%d %H:%M")`.
           - `commit()`.

         - Uğurdan sonra:
           - `redirect(url_for("gallery.grid"))`.

      3) UX ipucları:
         - Yüklənəndən sonra “Uğurla yükləndi” mesajı göstər (flash).
         - `accept="image/*"` atributu əlavə et (UX üçün; server yoxlamasını əvəz etmir).

      4) Təhlükəsizlik qeydləri:
         - Fayl adını **heç vaxt** istifadəçinin orijinal adı ilə saxlamayın (unikal token istifadə edin).
         - MIME tipini də yoxlamağı düşünün (`file.mimetype.startswith("image/")`).
         - Upload qovluğunu `app.config["UPLOAD_FOLDER"]` ilə düzgün konfiqurasiya edin (məsələn `static/uploads`).

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    if request.method == "GET":
        return render_template("gallery/upload.html")

    files = request.files.getlist("file")
    title = (request.form.get("title") or "").strip() or "Başlıqsız"
    uploader = (request.form.get("uploader") or "").strip() or "Anonim"

    if not files or all(not f or not f.filename for f in files):
        flash("Zəhmət olmasa ən azı bir şəkil faylı yükləyin (png, jpg, jpeg, gif, webp).")
        return redirect(url_for("gallery.upload"))

    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db = get_db()
    ok = 0
    for file in files:
        if not file or not file.filename:
            continue
        if not allowed(file.filename):
            continue
        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > MAX_SIZE:
            continue

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{secrets.token_hex(8)}.{ext}"
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        db.execute(
            "INSERT INTO gallery_images (title, filename, uploader, created_at) VALUES (?, ?, ?, ?)",
            (title, filename, uploader, created_at),
        )
        ok += 1

    db.commit()
    if ok:
        flash("Uğurla yükləndi." if ok == 1 else f"{ok} şəkil uğurla yükləndi.")
    else:
        flash("Heç bir şəkil yüklənmədi. Fayl tipi və ölçüyə baxın.")
    return redirect(url_for("gallery.grid"))
