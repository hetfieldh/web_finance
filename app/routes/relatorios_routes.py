# app/routes/relatorios_routes.py

from datetime import date

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.services import relatorios_service

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/resumo-mensal", methods=["GET"])
@login_required
def resumo_mensal():
    form = FluxoCaixaForm(request.args)
    hoje = date.today()

    mes_ano_selecionado = form.mes_ano.data
    if not mes_ano_selecionado:
        mes_ano_selecionado = hoje.strftime("%m-%Y")
        form.mes_ano.data = mes_ano_selecionado

    mes, ano = map(int, mes_ano_selecionado.split("-"))

    dados_resumo = relatorios_service.get_resumo_mensal(current_user.id, ano, mes)

    return render_template(
        "extratos/resumo_mensal.html", form=form, dados=dados_resumo, mes=mes, ano=ano
    )
