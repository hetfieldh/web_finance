# app/__init__.py

import locale
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_class=Config):
    from config import Config

    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "Portuguese_Brazil.1252")
        except locale.Error:
            app.logger.warning(
                "Não foi possível configurar o locale para pt-BR. Os nomes dos meses podem aparecer em inglês."
            )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "Faça login para acessar."

    from app.models.conta_model import Conta
    from app.models.conta_movimento_model import ContaMovimento
    from app.models.conta_transacao_model import ContaTransacao
    from app.models.crediario_fatura_model import CrediarioFatura
    from app.models.crediario_grupo_model import CrediarioGrupo
    from app.models.crediario_model import Crediario
    from app.models.crediario_movimento_model import CrediarioMovimento
    from app.models.crediario_parcela_model import CrediarioParcela
    from app.models.desp_rec_model import DespRec
    from app.models.desp_rec_movimento_model import DespRecMovimento
    from app.models.financiamento_model import Financiamento
    from app.models.financiamento_parcela_model import FinanciamentoParcela
    from app.models.salario_item_model import SalarioItem
    from app.models.salario_movimento_item_model import SalarioMovimentoItem
    from app.models.salario_movimento_model import SalarioMovimento
    from app.models.solicitacao_acesso_model import SolicitacaoAcesso
    from app.models.usuario_model import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    from app.routes.auth_routes import auth_bp
    from app.routes.conta_movimento_routes import conta_movimento_bp
    from app.routes.conta_routes import conta_bp
    from app.routes.conta_transacao_routes import conta_transacao_bp
    from app.routes.crediario_fatura_routes import crediario_fatura_bp
    from app.routes.crediario_grupo_routes import crediario_grupo_bp
    from app.routes.crediario_movimento_routes import crediario_movimento_bp
    from app.routes.crediario_routes import crediario_bp
    from app.routes.desp_rec_movimento_routes import desp_rec_movimento_bp
    from app.routes.desp_rec_routes import desp_rec_bp
    from app.routes.extrato_desp_rec_routes import extrato_desp_rec_bp
    from app.routes.extrato_routes import extrato_bp
    from app.routes.financiamento_routes import financiamento_bp
    from app.routes.fluxo_caixa_routes import fluxo_caixa_bp
    from app.routes.graphics_routes import graphics_bp
    from app.routes.main_routes import main_bp
    from app.routes.pagamentos_routes import pagamentos_bp
    from app.routes.recebimentos_routes import recebimentos_bp
    from app.routes.salario_routes import salario_bp
    from app.routes.solicitacao_routes import solicitacao_bp
    from app.routes.usuario_routes import usuario_bp

    app.register_blueprint(usuario_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(conta_bp)
    app.register_blueprint(conta_transacao_bp)
    app.register_blueprint(conta_movimento_bp)
    app.register_blueprint(extrato_bp)
    app.register_blueprint(crediario_bp)
    app.register_blueprint(crediario_grupo_bp)
    app.register_blueprint(crediario_movimento_bp)
    app.register_blueprint(crediario_fatura_bp)
    app.register_blueprint(financiamento_bp)
    app.register_blueprint(desp_rec_bp)
    app.register_blueprint(desp_rec_movimento_bp)
    app.register_blueprint(extrato_desp_rec_bp)
    app.register_blueprint(salario_bp)
    app.register_blueprint(pagamentos_bp)
    app.register_blueprint(recebimentos_bp)
    app.register_blueprint(fluxo_caixa_bp)
    app.register_blueprint(graphics_bp)
    app.register_blueprint(solicitacao_bp)

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

    @app.errorhandler(404)
    def not_found_error(error):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.warning(
            f"Erro 404: Página não encontrada em {request.path} por {user_info}"
        )
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.error(
            f"Erro Interno do Servidor (500): {error} na requisição {request.method} {request.path} por {user_info}",
            exc_info=True,
        )
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
