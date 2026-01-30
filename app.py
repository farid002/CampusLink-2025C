
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template
from database import init_db
from blog import bp as blog_bp
from events import bp as events_bp
from forum import bp as forum_bp
from gallery import bp as gallery_bp
from polls import bp as polls_bp
from feedback import bp as feedback_bp

# Workshop 2 - AI/ML modulları
from blog_ocr import bp as blog_ocr_bp
from blog_tts import bp as blog_tts_bp
from events_speech import bp as events_speech_bp
from gallery_detection import bp as gallery_detection_bp
from gallery_faces import bp as gallery_faces_bp
from forum_tts import bp as forum_tts_bp
from polls_speech import bp as polls_speech_bp

def create_app():
    """Flask tətbiq obyektini yaradır və bütün blueprint-ləri qeydiyyatdan keçirir."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-change-me"
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["AUDIO_FOLDER"] = os.path.join(app.root_path, "static", "audio")
    app.config["DETECTIONS_FOLDER"] = os.path.join(app.root_path, "static", "detections")
    
    # Static qovluqları yarat
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["AUDIO_FOLDER"], "blog"), exist_ok=True)
    os.makedirs(os.path.join(app.config["AUDIO_FOLDER"], "forum"), exist_ok=True)
    os.makedirs(os.path.join(app.config["DETECTIONS_FOLDER"], "gallery"), exist_ok=True)

    # Məlumat bazasını qur
    init_db()

    # Modulları qoş
    app.register_blueprint(blog_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(polls_bp)
    app.register_blueprint(feedback_bp)
    
    # Workshop 2 - AI/ML modulları
    app.register_blueprint(blog_ocr_bp)
    app.register_blueprint(blog_tts_bp)
    app.register_blueprint(events_speech_bp)
    app.register_blueprint(gallery_detection_bp)
    app.register_blueprint(gallery_faces_bp)
    app.register_blueprint(forum_tts_bp)
    app.register_blueprint(polls_speech_bp)

    @app.route("/")
    def index():
        """
        Ana səhifə:
        - Layihənin qısa təqdimatı
        - Naviqasiya üçün başlanğıc
        """
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
