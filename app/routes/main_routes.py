# app/routes/main_routes.py

import os
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload

from app import db
from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.models.conta_model import Conta
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.services import conta_service, relatorios_service
from app.utils import (
    NATUREZA_DESPESA,
    STATUS_ATRASADO,
    STATUS_PARCIAL_PAGO,
    STATUS_PARCIAL_RECEBIDO,
    STATUS_PENDENTE,
    TIPO_ENTRADA,
    TIPO_SAIDA,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    balance_kpis = conta_service.get_account_balance_kpis(current_user.id)
    hoje = date.today()
    balanco_do_mes = relatorios_service.get_balanco_mensal(
        current_user.id, hoje.year, hoje.month
    )
    kpis = {
        "saldo_operacional": balance_kpis["saldo_operacional"],
        "saldo_investimentos": balance_kpis["saldo_investimentos"],
        "saldo_beneficios": balance_kpis["saldo_beneficios"],
        "saldo_fgts": balance_kpis["saldo_fgts"],
        "receitas_mes": balanco_do_mes["receitas"],
        "despesas_mes": balanco_do_mes["despesas"],
        "balanco_mes": balanco_do_mes["balanco"],
    }
    contas_do_usuario = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco.asc())
        .all()
    )
    financiamentos_ativos = Financiamento.query.filter_by(
        usuario_id=current_user.id
    ).all()
    crediarios_ativos = Crediario.query.filter_by(
        usuario_id=current_user.id, ativa=True
    ).all()

    form = FluxoCaixaForm(request.args)
    mes_ano_selecionado = form.mes_ano.data
    if not mes_ano_selecionado:
        mes_ano_selecionado = hoje.strftime("%m-%Y")
        form.mes_ano.data = mes_ano_selecionado

    mes, ano = map(int, mes_ano_selecionado.split("-"))
    data_inicio_mes = date(ano, mes, 1)
    data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )

    proximos_movimentos = []

    desp_rec_mes = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
            DespRecMovimento.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        )
        .options(joinedload(DespRecMovimento.despesa_receita))
        .all()
    )
    for item in desp_rec_mes:
        proximos_movimentos.append(
            {
                "data": item.data_vencimento,
                "descricao": item.despesa_receita.nome,
                "valor": item.valor_previsto,
                "tipo": (
                    TIPO_SAIDA
                    if item.despesa_receita.natureza == NATUREZA_DESPESA
                    else TIPO_ENTRADA
                ),
            }
        )

    faturas_mes = (
        CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == current_user.id,
            CrediarioFatura.data_vencimento_fatura.between(
                data_inicio_mes, data_fim_mes
            ),
            CrediarioFatura.status.in_(
                [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]
            ),
        )
        .options(joinedload(CrediarioFatura.crediario))
        .all()
    )
    for fatura in faturas_mes:
        proximos_movimentos.append(
            {
                "data": fatura.data_vencimento_fatura,
                "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                "valor": fatura.valor_total_fatura - fatura.valor_pago_fatura,
                "tipo": TIPO_SAIDA,
            }
        )

    parcelas_mes = (
        FinanciamentoParcela.query.join(Financiamento)
        .filter(
            Financiamento.usuario_id == current_user.id,
            FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        )
        .options(joinedload(FinanciamentoParcela.financiamento))
        .all()
    )
    for parcela in parcelas_mes:
        proximos_movimentos.append(
            {
                "data": parcela.data_vencimento,
                "descricao": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                "valor": parcela.valor_total_previsto,
                "tipo": TIPO_SAIDA,
            }
        )

    salarios_mes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.status.in_([STATUS_PENDENTE, STATUS_PARCIAL_RECEBIDO]),
    ).all()
    for salario in salarios_mes:
        if not salario.movimento_bancario_salario_id and salario.salario_liquido > 0:
            proximos_movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Salário Líquido (Ref: {salario.mes_referencia})",
                    "valor": salario.salario_liquido,
                    "tipo": TIPO_ENTRADA,
                }
            )
        if not salario.movimento_bancario_beneficio_id and salario.total_beneficios > 0:
            proximos_movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Benefícios (Ref: {salario.mes_referencia})",
                    "valor": salario.total_beneficios,
                    "tipo": TIPO_ENTRADA,
                }
            )

    proximos_movimentos.sort(key=lambda x: x["data"])

    pending_requests_count = (
        SolicitacaoAcesso.query.filter_by(status=STATUS_PENDENTE).count()
        if current_user.is_admin
        else 0
    )

    return render_template(
        "dashboard.html",
        kpis=kpis,
        contas_do_usuario=contas_do_usuario,
        proximos_movimentos=proximos_movimentos,
        pending_requests=pending_requests_count,
        financiamentos=financiamentos_ativos,
        crediarios=crediarios_ativos,
        form_movimentos=form,
    )


@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(main_bp.root_path, "..", "static", "images"),
        "favicon.png",
        mimetype="image/png",
    )
