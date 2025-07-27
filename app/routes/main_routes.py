# app/routes/main_routes.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

# Cria um Blueprint para as rotas principais da aplicação
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required  # Rota protegida, exige que o usuário esteja logado
def dashboard():
    # Renderiza o template do dashboard (página inicial após o login)
    return render_template("dashboard.html")
