# app/__init__.py

from flask import Flask, redirect, render_template, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

import logging
from logging.handlers import RotatingFileHandler
import os

# Inicializa extensões Flask fora da função para que possam ser usadas em modelos
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    # Importa a classe Config
    from config import Config

    # Cria a instância da aplicação Flask
    app = Flask(__name__)
    # Carrega as configurações da classe Config
    app.config.from_object(Config)

    # Inicializa as extensões com a instância do app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # Define a rota de login para o Flask-Login
    login_manager.login_view = "auth.login"
    # Define a categoria da mensagem flash para o Flask-Login
    login_manager.login_message_category = "info"

    # Importa o modelo de usuário para que o Flask-Login e Alembic o detectem
    from app.models.usuario_model import Usuario
    from app.models.conta_model import Conta

    # Função user_loader para o Flask-Login carregar usuários da sessão
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Importa e registra os Blueprints (módulos de rotas)
    from app.routes.usuario_routes import usuario_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp
    from app.routes.conta_routes import conta_bp

    app.register_blueprint(usuario_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(conta_bp)

    # Rota raiz que redireciona para o dashboard
    @app.route("/")
    def index():
        return redirect(url_for("main.dashboard"))

    # Configuração do sistema de logging
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # Configura o handler para rotação de arquivos de log
    file_handler = RotatingFileHandler(
        app.config["LOG_FILE"],
        maxBytes=app.config["LOG_MAX_BYTES"],
        backupCount=app.config["LOG_BACKUP_COUNT"],
        encoding="utf-8",
    )
    # Define o formato das mensagens de log
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(app.config["LOG_LEVEL"])

    # Adiciona o handler de arquivo ao logger da aplicação
    app.logger.addHandler(file_handler)

    # Configura o handler para exibir logs no console em desenvolvimento ou quando especificado
    if app.debug or app.config["LOG_TO_STDOUT"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(stream_handler)

    # Define o nível geral para o logger da aplicação
    app.logger.setLevel(app.config["LOG_LEVEL"])
    # Registra uma mensagem de inicialização da aplicação
    app.logger.info("Web Finance startup")

    # Hook para logar erros de requisição (códigos >= 400)
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

    # Handler para erros internos do servidor (código 500)
    @app.errorhandler(500)
    def internal_error(error):
        user_info = current_user.login if current_user.is_authenticated else "Anônimo"
        app.logger.error(
            f"Erro Interno do Servidor (500): {error} na requisição {request.method} {request.path} por {user_info}",
            exc_info=True,
        )
        # Garante que a sessão do banco de dados seja revertida após um erro
        db.session.rollback()
        # Renderiza uma página de erro 500 personalizada
        return render_template("500.html"), 500

    return app
