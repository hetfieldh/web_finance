# app/routes/main_routes.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.conta_model import Conta

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    contas_do_usuario = Conta.query.filter_by(usuario_id=current_user.id).all()

    return render_template("dashboard.html", contas_do_usuario=contas_do_usuario)
