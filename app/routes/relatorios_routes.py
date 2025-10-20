# app/routes/relatorios_routes.py

from datetime import date

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.forms.relatorios_forms import ResumoAnualForm
from app.models.salario_movimento_model import SalarioMovimento
from app.services import relatorios_service

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/resumo-folha", methods=["GET"])
@login_required
def resumo_folha():
    form = ResumoAnualForm(request.args)

    anos_disponiveis = (
        db.session.query(func.extract("year", SalarioMovimento.data_recebimento))
        .filter(SalarioMovimento.usuario_id == current_user.id)
        .distinct()
        .order_by(func.extract("year", SalarioMovimento.data_recebimento).desc())
        .all()
    )

    form.ano.choices = [(ano[0], str(ano[0])) for ano in anos_disponiveis]

    ano_selecionado = form.ano.data
    if not ano_selecionado and anos_disponiveis:
        ano_selecionado = anos_disponiveis[0][0]
        form.ano.data = ano_selecionado

    dados_resumo = None
    if ano_selecionado:
        dados_resumo = relatorios_service.get_resumo_folha_anual(
            current_user.id, ano_selecionado
        )

    return render_template(
        "extratos/resumo_folha.html",
        form=form,
        dados=dados_resumo,
        ano_selecionado=ano_selecionado,
    )


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
