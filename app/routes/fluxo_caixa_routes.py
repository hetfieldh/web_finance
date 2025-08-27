# app/routes/fluxo_caixa_routes.py

from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.services import relatorios_service

fluxo_caixa_bp = Blueprint("fluxo_caixa", __name__, url_prefix="/fluxo_caixa")


@fluxo_caixa_bp.route("/painel", methods=["GET"])
@login_required
def painel():
    form = FluxoCaixaForm(request.args)

    if not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%m-%Y")

    mes_ano_str = form.mes_ano.data
    kpis = {}
    movimentacoes = []

    if mes_ano_str:
        try:
            mes, ano = map(int, mes_ano_str.split("-"))
        except (ValueError, TypeError):
            flash("Formato de data inválido.", "danger")
            return redirect(url_for("fluxo_caixa.painel"))

        kpis = relatorios_service.get_balanco_mensal(current_user.id, ano, mes)
        movimentacoes = relatorios_service.get_fluxo_caixa_mensal_consolidado(
            current_user.id, ano, mes
        )

    return render_template(
        "fluxo_caixa/painel.html",
        form=form,
        movimentacoes=movimentacoes,
        kpis=kpis,
        title="Fluxo de Caixa Mensal",
    )
