# app/routes/auth_routes.py

from flask import (
    Blueprint,
    Flask,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_sqlalchemy import (
    SQLAlchemy,
)

from app import db
from app.models.usuario_model import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("Você já está logado!", "info")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        login_str = request.form.get("login_ou_email")
        password = request.form.get("senha")

        usuario = Usuario.query.filter(
            (Usuario.login == login_str) | (Usuario.email == login_str)
        ).first()

        if usuario and usuario.check_password(password):
            if not usuario.is_active:
                flash(
                    "Sua conta está inativa. Por favor, entre em contato com o administrador.",
                    "warning",
                )
                current_app.logger.warning(
                    f"Tentativa de login falha: Usuário inativo: {login_str} (IP: {request.remote_addr})"
                )
                return redirect(url_for("auth.login"))

            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            current_app.logger.info(
                f"Login bem-sucedido: Usuário {usuario.login} (ID: {usuario.id}, IP: {request.remote_addr})"
            )

            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        else:
            flash("Login ou senha incorretos.", "danger")
            current_app.logger.warning(
                f'Tentativa de login falha: Credenciais inválidas para "{login_str}" (IP: {request.remote_addr})'
            )
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    user_login = current_user.login
    user_id = current_user.id

    logout_user()
    flash("Você foi desconectado.", "info")
    current_app.logger.info(
        f"Logout bem-sucedido: Usuário {user_login} (ID: {user_id}, IP: {request.remote_addr})"
    )
    return redirect(url_for("auth.login"))
