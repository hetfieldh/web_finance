from flask import Flask, redirect, render_template, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from config import Config

import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from app.models.usuario_model import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from app.routes.usuario_routes import usuario_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp

    app.register_blueprint(usuario_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.route("/")
    def index():
        return redirect(url_for("main.dashboard"))

    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        app.config["LOG_FILE"],
        maxBytes=app.config["LOG_MAX_BYTES"],
        backupCount=app.config["LOG_BACKUP_COUNT"],
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(app.config["LOG_LEVEL"])

    app.logger.addHandler(file_handler)

    if app.debug or app.config["LOG_TO_STDOUT"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(stream_handler)

    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.info("Web Finance startup")

    @app.after_request
    def log_response(response):
        if response.status_code >= 400:
            user_info = (
                current_user.login if current_user.is_authenticated else "Anônimo"
            )
            app.logger.error(
                f"Erro na requisição: {response.status_code} {request.method} {request.path} por {user_info}"
            )
        return response

    @app.errorhandler(500)
    def internal_error(error):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.error(
            f"Erro Interno do Servidor (500): {error} na requisição {request.method} {request.path} por {user_info}",
            exc_info=True,
        )
        db.session.rollback()
        return render_template("500.html"), 500

    return app
