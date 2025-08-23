# app/routes/fluxo_caixa_routes.py

from datetime import date
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.services import relatorios_service

fluxo_caixa_bp = Blueprint("fluxo_caixa", __name__, url_prefix="/fluxo_caixa")


@fluxo_caixa_bp.route("/painel", methods=["GET", "POST"])
@login_required
def painel():
    form = FluxoCaixaForm(request.form)

    if request.method == "GET" and not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%Y-%m")

    mes_ano_str = form.mes_ano.data
    movimentacoes = []
    kpis = {
        "receitas": Decimal("0.00"),
        "despesas": Decimal("0.00"),
        "balanco": Decimal("0.00"),
        "comprometimento": 0,
    }

    if mes_ano_str:
        ano, mes = map(int, mes_ano_str.split("-"))

        # 1. Obter os KPIs (isto permanece igual)
        balanco_mensal = relatorios_service.get_balanco_mensal(
            current_user.id, ano, mes
        )
        kpis["receitas"] = balanco_mensal["receitas"]
        kpis["despesas"] = balanco_mensal["despesas"]
        kpis["balanco"] = balanco_mensal["balanco"]
        if kpis["receitas"] > 0:
            kpis["comprometimento"] = round((kpis["despesas"] / kpis["receitas"]) * 100)

        # 2. Obter o resumo consolidado para a tabela (usando a nova função)
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
