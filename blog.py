# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db, paginate_query
import datetime, re

bp = Blueprint("blog", __name__, url_prefix="/blog")

ADMIN_PASS = "admin123"  # demo


def slugify(text: str) -> str:
    """
    Verilən başlıqdan sadə slug yaradır.
    - Kiçik hərfləşdirir, boşluqları tire edir, latın olmayan simvolları silir.
    """
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:80]


@bp.route("/")
def list_posts():
    db = get_db()

    # Get query parameters
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    published = request.args.get("published", "").strip()
    page = int(request.args.get("page", 1))

    # Build WHERE conditions
    conditions = ["1=1"]
    params = []

    # Search filter
    if q:
        conditions.append("(title LIKE ? OR content LIKE ?)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term])

    # Tag filter
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{tag}%")

    # Published filter
    if published == "1":
        conditions.append("is_published = 1")
    elif published == "0":
        conditions.append("is_published = 0")

    # Build SQL query
    where_clause = " AND ".join(conditions)
    base_sql = f"SELECT * FROM blog_posts WHERE {where_clause} ORDER BY created_at DESC"

    # Pagination: 5 posts per page
    sql_with_limit, limit, offset = paginate_query(base_sql, page, 5)
    params.extend([limit, offset])

    # Execute query
    cursor = db.execute(sql_with_limit, params)
    posts = [dict(row) for row in cursor.fetchall()]

    return render_template("blog/list.html", posts=posts, q=q, tag=tag, published=published, page=page)


@bp.route("/<slug>")
def show_post(slug: str):
    db = get_db()
    cursor = db.execute("SELECT * FROM blog_posts WHERE slug = ?", (slug,))
    post_row = cursor.fetchone()

    if not post_row:
        return render_template("404.html"), 404

    post = dict(post_row)
    return render_template("blog/detail.html", post=post)


@bp.route("/<int:post_id>")
def show_post_by_id(post_id: int):
    db = get_db()
    cursor = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,))
    post_row = cursor.fetchone()

    if not post_row:
        return render_template("404.html"), 404

    post = dict(post_row)
    return render_template("blog/detail.html", post=post)


@bp.route("/detail/<int:post_id>")
def detail(post_id: int):
    return show_post_by_id(post_id)


@bp.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "GET":
        return render_template("blog/new.html")

    # POST request
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    tags = request.form.get("tags", "").strip()
    is_published = 1 if request.form.get("is_published") == "on" else 0

    # Validation
    if not title:
        flash("Başlıq boş ola bilməz.", "error")
        return redirect(url_for("blog.new_post"))

    if not content:
        flash("Məzmun boş ola bilməz.", "error")
        return redirect(url_for("blog.new_post"))

    # Generate slug
    base_slug = slugify(title)
    db = get_db()

    # Check if slug exists, make it unique if needed
    slug = base_slug
    counter = 1
    while True:
        cursor = db.execute("SELECT id FROM blog_posts WHERE slug = ?", (slug,))
        if not cursor.fetchone():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Insert into database
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute(
        "INSERT INTO blog_posts (title, content, tags, created_at, is_published, slug) VALUES (?, ?, ?, ?, ?, ?)",
        (title, content, tags, created_at, is_published, slug)
    )
    db.commit()

    flash("Yazı uğurla yaradıldı!", "success")
    return redirect(url_for("blog.list_posts"))


@bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
def edit(post_id: int):
    db = get_db()

    # Get existing post
    cursor = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,))
    post_row = cursor.fetchone()

    if not post_row:
        return render_template("404.html"), 404

    post = dict(post_row)

    # Admin password check
    password = request.args.get("password", "").strip()
    if password != ADMIN_PASS:
        return render_template("blog/edit.html", post=None, error="Admin parolu səhvdir.")

    if request.method == "GET":
        return render_template("blog/edit.html", post=post, error=None)

    # POST request
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    tags = request.form.get("tags", "").strip()
    is_published = 1 if request.form.get("is_published") == "on" else 0

    # Validation
    if not title:
        # Use form values for error display
        post["title"] = title
        post["content"] = content
        post["tags"] = tags
        post["is_published"] = is_published
        return render_template("blog/edit.html", post=post, error="Başlıq boş ola bilməz.")

    if not content:
        post["title"] = title
        post["content"] = content
        post["tags"] = tags
        post["is_published"] = is_published
        return render_template("blog/edit.html", post=post, error="Məzmun boş ola bilməz.")

    # Update database
    db.execute(
        "UPDATE blog_posts SET title=?, content=?, tags=?, is_published=? WHERE id=?",
        (title, content, tags, is_published, post_id)
    )
    db.commit()

    flash("Yazı uğurla yeniləndi!", "success")
    return redirect(url_for("blog.detail", post_id=post_id))


@bp.route("/<int:post_id>/delete")
def delete(post_id: int):
    # Admin password check
    password = request.args.get("password", "").strip()
    if password != ADMIN_PASS:
        flash("Admin parolu səhvdir. İcazə yoxdur.", "error")
        return redirect(url_for("blog.list_posts")), 403

    db = get_db()

    # Check if post exists
    cursor = db.execute("SELECT id FROM blog_posts WHERE id = ?", (post_id,))
    if not cursor.fetchone():
        return render_template("404.html"), 404

    # Delete post
    db.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    db.commit()

    flash("Yazı uğurla silindi!", "success")
    return redirect(url_for("blog.list_posts"))