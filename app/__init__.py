# app/__init__.py

import locale
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, app, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect

from config import Config

from .template_filters import format_number

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except locale.Error:
    print("Locale pt_BR.UTF-8 não encontrado, usando o padrão do sistema.")


def create_app(config_class=Config, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if config_overrides:
        app.config.update(config_overrides)

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
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.login_message = "Faça login para acessar."

    app.jinja_env.filters["format_number"] = format_number
    app.jinja_env.filters["format_number"] = format_number

    from app.models.conta_model import Conta
    from app.models.conta_movimento_model import ContaMovimento
    from app.models.conta_transacao_model import ContaTransacao
    from app.models.crediario_fatura_model import CrediarioFatura
    from app.models.crediario_grupo_model import CrediarioGrupo
    from app.models.crediario_model import Crediario
    from app.models.crediario_movimento_model import CrediarioMovimento
    from app.models.crediario_parcela_model import CrediarioParcela
    from app.models.crediario_subgrupo_model import CrediarioSubgrupo
    from app.models.desp_rec_model import DespRec
    from app.models.desp_rec_movimento_model import DespRecMovimento
    from app.models.financiamento_model import Financiamento
    from app.models.financiamento_parcela_model import FinanciamentoParcela
    from app.models.fornecedor_model import Fornecedor
    from app.models.salario_item_model import SalarioItem
    from app.models.salario_movimento_item_model import SalarioMovimentoItem
    from app.models.salario_movimento_model import SalarioMovimento
    from app.models.solicitacao_acesso_model import SolicitacaoAcesso
    from app.models.usuario_model import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    @app.before_request
    def check_force_password_change():
        if not current_user.is_authenticated:
            return

        if current_user.precisa_alterar_senha and request.endpoint not in [
            "usuario.perfil",
            "auth.logout",
            "static",
        ]:
            flash(
                "Por segurança, você deve alterar sua senha provisória para continuar.",
                "warning",
            )
            return redirect(url_for("usuario.perfil"))

    from app.routes.auth_routes import auth_bp
    from app.routes.conta_movimento_routes import conta_movimento_bp
    from app.routes.conta_routes import conta_bp
    from app.routes.conta_transacao_routes import conta_transacao_bp
    from app.routes.crediario_fatura_routes import crediario_fatura_bp
    from app.routes.crediario_grupo_routes import crediario_grupo_bp
    from app.routes.crediario_movimento_routes import crediario_movimento_bp
    from app.routes.crediario_routes import crediario_bp
    from app.routes.crediario_subgrupo_routes import crediario_subgrupo_bp
    from app.routes.desp_rec_movimento_routes import desp_rec_movimento_bp
    from app.routes.desp_rec_routes import desp_rec_bp
    from app.routes.extrato_routes import extrato_bp
    from app.routes.financiamento_routes import financiamento_bp
    from app.routes.fluxo_caixa_routes import fluxo_caixa_bp
    from app.routes.fornecedor_routes import fornecedor_bp
    from app.routes.graphics_routes import graphics_bp
    from app.routes.main_routes import main_bp
    from app.routes.pagamentos_routes import pagamentos_bp
    from app.routes.recebimentos_routes import recebimentos_bp
    from app.routes.relatorios_routes import relatorios_bp
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
    app.register_blueprint(salario_bp)
    app.register_blueprint(pagamentos_bp)
    app.register_blueprint(recebimentos_bp)
    app.register_blueprint(fluxo_caixa_bp)
    app.register_blueprint(graphics_bp)
    app.register_blueprint(solicitacao_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(crediario_subgrupo_bp)
    app.register_blueprint(fornecedor_bp)

    @app.route("/")
    def index():
        return redirect(url_for("main.dashboard"))

    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        "logs/web_finance.log",
        maxBytes=10240,
        backupCount=10,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s [in %(pathname)s:%(lineno)d]"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)

    if app.debug or os.environ.get("LOG_TO_STDOUT"):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(stream_handler)

    app.logger.setLevel(logging.INFO)
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

    @app.context_processor
    def inject_page_config():
        from .utils import PAGE_CONFIG

        endpoint = request.endpoint or "main.dashboard"
        default_config = {"title": "Bem-vindo", "header": "Web Finance"}
        page_config = PAGE_CONFIG.get(endpoint, default_config)

        return dict(page_config=page_config)

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

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.warning(
            f"Erro CSRF: {e.description} em {request.path} por {user_info}"
        )
        return render_template("errors/400.html", reason=e.description), 400

    @app.errorhandler(400)
    def bad_request_error(error):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.warning(
            f"Erro 400: Requisição inválida em {request.path} por {user_info}"
        )
        return render_template("errors/400.html"), 400

    @app.errorhandler(405)
    def bad_request_error(error):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.warning(
            f"Erro 405: Método não permitido em {request.path} por {user_info}"
        )
        return render_template("errors/405.html"), 405

    return app
