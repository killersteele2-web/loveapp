from fileinput import filename
import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
load_dotenv()

from config import Config
from models import db
from routes.memories import memories_bp
from routes.letters import letters_bp
from routes.timeline import timeline_bp
from routes.auth import auth_bp
from routes.couples import couples_bp
from routes.profile import profile_bp


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    JWTManager(app)

    CORS(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ========================================================
    # BLUEPRINTS
    # ========================================================

    app.register_blueprint(
        memories_bp
    )

    app.register_blueprint(
        letters_bp
    )

    app.register_blueprint(
        timeline_bp
    )

    app.register_blueprint(auth_bp)

    app.register_blueprint(couples_bp)

    app.register_blueprint(profile_bp)

    

    # ========================================================
    # HOME
    # ========================================================

    @app.route("/", methods=["GET"])
    def home():

        return jsonify({
            "success": True,
            "message": "Love App Backend is running ❤️"
        })

    

    # ========================================================
    # HEALTH
    # ========================================================

    @app.route(
        "/api/health",
        methods=["GET"]
    )
    def health_check():

        return jsonify({
            "success": True,
            "status": "online",
            "database": "connected",
            "message": "Backend is healthy ❤️"
        })

    # ========================================================
    # STATIC UPLOADS - MEMORIES
    # ========================================================

    @app.route(
    "/uploads/profiles/<filename>",
    methods=["GET"]
)
    def profile_image(filename):

        return send_from_directory(
        os.path.join(
            app.root_path,
            "uploads",
            "profiles"
        ),
        filename
    )


    @app.route(
        "/uploads/memories/<filename>",
        methods=["GET"]
    )
    def memory_image(filename):

        return send_from_directory(
            os.path.join(
                app.root_path,
                "uploads",
                "memories"
            ),
            filename
        )

    # ========================================================
    # STATIC UPLOADS - TIMELINE
    # ========================================================

    @app.route(
        "/uploads/timeline/<filename>",
        methods=["GET"]
    )
    def timeline_image(filename):

        return send_from_directory(
            os.path.join(
                app.root_path,
                "uploads",
                "timeline"
            ),
            filename
        )

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )