# app/routes/auth_routes.py

from flask import (
    Blueprint,
    Flask,
    current_app,
    flash,
    redirect,
    url_for,
    request,
    render_template,
)
from flask_sqlalchemy import (
    SQLAlchemy,
)  # Esta importação não é usada diretamente neste arquivo
from flask_login import login_user, logout_user, login_required, current_user
from app import db  # Importa a instância do SQLAlchemy
from app.models.usuario_model import Usuario  # Importa o modelo de usuário

# Cria um Blueprint para as rotas de autenticação
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Se o usuário já estiver autenticado, redireciona para o dashboard
    if current_user.is_authenticated:
        flash("Você já está logado!", "info")
        return redirect(url_for("main.dashboard"))

    # Processa o formulário de login quando a requisição é POST
    if request.method == "POST":
        login_str = request.form.get("login_ou_email")
        password = request.form.get("senha")

        # Tenta encontrar o usuário pelo login ou e-mail
        usuario = Usuario.query.filter(
            (Usuario.login == login_str) | (Usuario.email == login_str)
        ).first()

        # Verifica se o usuário existe e se a senha está correta
        if usuario and usuario.check_password(password):
            # Se a conta do usuário estiver inativa, exibe uma mensagem de aviso
            if not usuario.is_active:
                flash(
                    "Sua conta está inativa. Por favor, entre em contato com o administrador.",
                    "warning",
                )
                # Registra a tentativa de login falha (usuário inativo)
                current_app.logger.warning(
                    f"Tentativa de login falha: Usuário inativo: {login_str} (IP: {request.remote_addr})"
                )
                return redirect(url_for("auth.login"))

            # Realiza o login do usuário usando Flask-Login
            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            # Registra o login bem-sucedido no log de auditoria
            current_app.logger.info(
                f"Login bem-sucedido: Usuário {usuario.login} (ID: {usuario.id}, IP: {request.remote_addr})"
            )

            # Redireciona o usuário para a página 'next' (se houver) ou para o dashboard
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        else:
            # Exibe mensagem de erro para credenciais inválidas
            flash("Login ou senha incorretos. Tente novamente.", "danger")
            # Registra a tentativa de login falha (credenciais inválidas)
            current_app.logger.warning(
                f'Tentativa de login falha: Credenciais inválidas para "{login_str}" (IP: {request.remote_addr})'
            )
    # Renderiza o template do formulário de login (para GET ou falha na validação)
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required  # Garante que apenas usuários logados possam acessar esta rota
def logout():
    # Captura informações do usuário antes de fazer logout
    user_login = current_user.login
    user_id = current_user.id

    # Realiza o logout do usuário usando Flask-Login
    logout_user()
    flash("Você foi desconectado.", "info")
    # Registra o logout bem-sucedido no log de auditoria
    current_app.logger.info(
        f"Logout bem-sucedido: Usuário {user_login} (ID: {user_id}, IP: {request.remote_addr})"
    )
    # Redireciona para a página de login
    return redirect(url_for("auth.login"))
