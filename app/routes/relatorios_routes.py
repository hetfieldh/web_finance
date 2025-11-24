# app/routes/relatorios_routes.py

from collections import OrderedDict, defaultdict
from datetime import (
    date,
    datetime,
)

from dateutil.relativedelta import relativedelta
from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import extract, func

from app import db
from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.forms.relatorios_forms import GastosCrediarioForm, ResumoAnualForm
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.crediario_subgrupo_model import CrediarioSubgrupo
from app.models.fornecedor_model import Fornecedor
from app.models.salario_movimento_model import SalarioMovimento
from app.services import relatorios_service
from app.services.relatorios_service import (
    get_detalhes_parcelas_por_grupo,
    get_gastos_crediario_por_destino_anual,
    get_gastos_crediario_por_fornecedor_anual,
    get_gastos_crediario_por_grupo_anual,
    get_gastos_crediario_por_subgrupo_anual,
)

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


@relatorios_bp.route("/resumo_salario", methods=["GET"])
@login_required
def resumo_salario():
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
        dados_resumo = relatorios_service.get_resumo_salario_anual(
            current_user.id, ano_selecionado
        )

    return render_template(
        "relatorios/resumo_salario.html",
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


@relatorios_bp.route("/gastos_por_grupo", methods=["GET"])
@login_required
def gastos_por_grupo():
    form = GastosCrediarioForm(request.args)

    anos_disponiveis = (
        db.session.query(func.extract("year", CrediarioMovimento.data_compra))
        .filter(CrediarioMovimento.usuario_id == current_user.id)
        .distinct()
        .order_by(func.extract("year", CrediarioMovimento.data_compra).desc())
        .all()
    )

    form.ano.choices = [(ano[0], str(ano[0])) for ano in anos_disponiveis]

    ano_selecionado = form.ano.data
    if not ano_selecionado and anos_disponiveis:
        ano_selecionado = anos_disponiveis[0][0]

    if ano_selecionado:
        ano_selecionado = int(ano_selecionado)
        form.ano.data = ano_selecionado

    visualizacao_selecionada = form.visualizacao.data or "grupo"
    form.visualizacao.data = visualizacao_selecionada

    dados_destino = None
    dados_tabela = None
    titulo_tabela = ""

    if ano_selecionado:
        dados_destino = get_gastos_crediario_por_destino_anual(ano_selecionado)

        if visualizacao_selecionada == "grupo":
            titulo_tabela = f"Gastos por Grupo ({ano_selecionado})"
            dados_tabela = get_gastos_crediario_por_grupo_anual(ano_selecionado)

        elif visualizacao_selecionada == "subgrupo":
            titulo_tabela = f"Gastos por Subgrupo ({ano_selecionado})"
            dados_tabela = get_gastos_crediario_por_subgrupo_anual(ano_selecionado)

        elif visualizacao_selecionada == "fornecedor":
            titulo_tabela = f"Gastos por Fornecedor ({ano_selecionado})"
            dados_tabela = get_gastos_crediario_por_fornecedor_anual(ano_selecionado)

    template_path = "relatorios/gastos_por_grupo.html"

    return render_template(
        template_path,
        title=f"Gastos no Crediário ({ano_selecionado or 'N/A'})",
        form=form,
        dados_destino=dados_destino,
        dados_tabela=dados_tabela,
        ano_selecionado=ano_selecionado,
        visualizacao_selecionada=visualizacao_selecionada,
        titulo_tabela=titulo_tabela,
    )


@relatorios_bp.route("/crediario_resumo/<int:grupo_id>/<int:ano>")
@login_required
def crediario_resumo(grupo_id, ano):
    dados_detalhe = get_detalhes_parcelas_por_grupo(grupo_id, ano)

    if dados_detalhe is None:
        abort(404)

    return render_template(
        "relatorios/crediario_resumo.html",
        title=f"Detalhes: {dados_detalhe['grupo_nome']} ({ano})",
        dados=dados_detalhe,
    )


@relatorios_bp.route("/crediario_detalhado")
@login_required
def crediario_detalhado():
    hoje = date.today()
    primeiro_dia_mes_atual = date(hoje.year, hoje.month, 1)

    resultados = (
        db.session.query(
            CrediarioGrupo.id.label("grupo_id"),
            CrediarioGrupo.grupo_crediario.label("grupo_nome"),
            CrediarioSubgrupo.id.label("subgrupo_id"),
            CrediarioSubgrupo.nome.label("subgrupo_nome"),
            Fornecedor.nome.label("fornecedor_nome"),
            extract("year", CrediarioParcela.data_vencimento).label("ano"),
            extract("month", CrediarioParcela.data_vencimento).label("mes"),
            func.sum(CrediarioParcela.valor_parcela).label("total"),
        )
        .join(
            CrediarioMovimento,
            CrediarioParcela.crediario_movimento_id == CrediarioMovimento.id,
        )
        .outerjoin(
            CrediarioGrupo, CrediarioMovimento.crediario_grupo_id == CrediarioGrupo.id
        )
        .outerjoin(
            CrediarioSubgrupo,
            CrediarioMovimento.crediario_subgrupo_id == CrediarioSubgrupo.id,
        )
        .outerjoin(Fornecedor, CrediarioMovimento.fornecedor_id == Fornecedor.id)
        .filter(
            CrediarioMovimento.usuario_id == current_user.id,
            CrediarioParcela.data_vencimento >= primeiro_dia_mes_atual,
            CrediarioParcela.pago == False,
        )
        .group_by(
            CrediarioGrupo.id,
            CrediarioGrupo.grupo_crediario,
            CrediarioSubgrupo.id,
            CrediarioSubgrupo.nome,
            Fornecedor.nome,
            extract("year", CrediarioParcela.data_vencimento),
            extract("month", CrediarioParcela.data_vencimento),
        )
        .all()
    )

    colunas_meses = set()

    dados_organizados = defaultdict(
        lambda: {
            "id": None,
            "total_meses": defaultdict(float),
            "subgrupos": defaultdict(
                lambda: {
                    "id": None,
                    "total_meses": defaultdict(float),
                    "fornecedores": defaultdict(lambda: defaultdict(float)),
                }
            ),
        }
    )

    for row in resultados:
        grupo_id = row.grupo_id or 0
        grupo_nome = row.grupo_nome if row.grupo_nome else "Sem Grupo"
        subgrupo_id = row.subgrupo_id or 0
        subgrupo_nome = row.subgrupo_nome if row.subgrupo_nome else "Geral"
        fornecedor_nome = (
            row.fornecedor_nome if row.fornecedor_nome else "Sem Fornecedor"
        )
        mes_num = int(row.mes)
        ano_num = int(row.ano)
        chave_mes = f"{ano_num}-{mes_num:02d}"
        valor = float(row.total)
        colunas_meses.add(chave_mes)
        dados_organizados[grupo_nome]["id"] = grupo_id
        dados_organizados[grupo_nome]["total_meses"][chave_mes] += valor
        sub_ref = dados_organizados[grupo_nome]["subgrupos"][subgrupo_nome]
        sub_ref["id"] = subgrupo_id
        sub_ref["total_meses"][chave_mes] += valor
        sub_ref["fornecedores"][fornecedor_nome][chave_mes] += valor

    colunas_ordenadas = sorted(list(colunas_meses))
    meses_header = []
    nomes_meses = [
        "",
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez",
    ]

    for col in colunas_ordenadas:
        ano, mes = col.split("-")
        meses_header.append({"key": col, "label": f"{nomes_meses[int(mes)]}/{ano[2:]}"})

    return render_template(
        "relatorios/crediario_detalhado.html",
        dados=dados_organizados,
        meses=meses_header,
    )
