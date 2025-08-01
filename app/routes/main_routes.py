# app/routes/main_routes.py

from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models.conta_model import Conta
from app.models.crediario_fatura_model import CrediarioFatura

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    contas_do_usuario = (
        Conta.query.filter_by(usuario_id=current_user.id)
        .order_by(Conta.nome_banco.asc())
        .all()
    )

    hoje = date.today()
    mes_ano_str = f"{hoje.year}-{hoje.month:02d}"

    faturas_do_mes = (
        CrediarioFatura.query.filter_by(
            usuario_id=current_user.id, mes_referencia=mes_ano_str
        )
        .order_by(CrediarioFatura.data_vencimento_fatura.asc())
        .all()
    )

    return render_template(
        "dashboard.html",
        contas_do_usuario=contas_do_usuario,
        faturas_do_mes=faturas_do_mes,
    )
