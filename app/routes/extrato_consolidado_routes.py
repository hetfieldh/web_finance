# app/routes/extrato_consolidado_routes.py

from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.extrato_forms import ExtratoConsolidadoForm
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento
from app.services import relatorios_service

extrato_consolidado_bp = Blueprint(
    "extrato_consolidado", __name__, url_prefix="/extratos"
)


@extrato_consolidado_bp.route("/consolidado", methods=["GET"])
@login_required
def extrato_consolidado():
    form = ExtratoConsolidadoForm(request.args)
    movimentacoes = []

    if not form.mes_ano.data:
        hoje = date.today()
        form.mes_ano.data = f"{hoje.month:02d}-{hoje.year}"

    mes_ano_str = form.mes_ano.data
    kpis = {}

    if mes_ano_str:
        try:
            mes, ano = map(int, mes_ano_str.split("-"))
        except (ValueError, TypeError):
            flash("Formato de data inválido.", "danger")
            return redirect(url_for("extrato_consolidado.extrato_consolidado"))

        # A lógica para buscar os KPIs e a lista de movimentações
        # é centralizada nos serviços.
        kpis = relatorios_service.get_balanco_mensal(current_user.id, ano, mes)
        movimentacoes = relatorios_service.get_fluxo_caixa_mensal_consolidado(
            current_user.id, ano, mes
        )

    return render_template(
        "extratos/consolidado.html",
        form=form,
        movimentacoes=movimentacoes,
        kpis=kpis,
        title="Extrato Consolidado",
    )
