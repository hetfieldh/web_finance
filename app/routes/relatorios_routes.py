# app/routes/relatorios_routes.py

from datetime import (
    date,
    datetime,
)

from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.forms.relatorios_forms import ResumoAnualForm
from app.models.salario_movimento_model import SalarioMovimento
from app.services import relatorios_service
from app.services.relatorios_service import (
    get_detalhes_parcelas_por_grupo,
    get_gastos_crediario_por_grupo_anual,
)

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
        "relatorios/resumo_folha.html",
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
        "relatorios/resumo_mensal.html", form=form, dados=dados_resumo, mes=mes, ano=ano
    )


@relatorios_bp.route("/gastos_por_grupo")
@login_required
def gastos_por_grupo():
    ano_atual = datetime.now().year
    dados_grupo, dados_destino = get_gastos_crediario_por_grupo_anual()

    template_path = "relatorios/gastos_por_grupo.html"

    return render_template(
        template_path,
        title=f"Gastos por Grupo ({ano_atual})",
        dados_grupo=dados_grupo,
        dados_destino=dados_destino,
        ano=ano_atual,
    )


@relatorios_bp.route("/detalhe_grupo_crediario/<int:grupo_id>/<int:ano>")
@login_required
def detalhe_grupo_crediario(grupo_id, ano):
    dados_detalhe = get_detalhes_parcelas_por_grupo(grupo_id, ano)

    if dados_detalhe is None:
        abort(404)

    return render_template(
        "relatorios/detalhe_grupo_crediario.html",
        title=f"Detalhes: {dados_detalhe['grupo_nome']} ({ano})",
        dados=dados_detalhe,
    )
