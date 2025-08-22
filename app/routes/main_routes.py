# app/routes/main_routes.py

import os
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload, subqueryload

from app import db
from app.models.conta_model import Conta
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.services import conta_service, relatorios_service

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

    proximos_movimentos = []
    desp_rec_pendentes = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.status == "Pendente",
        )
        .options(joinedload(DespRecMovimento.despesa_receita))
        .all()
    )
    for item in desp_rec_pendentes:
        proximos_movimentos.append(
            {
                "data": item.data_vencimento,
                "descricao": item.despesa_receita.nome,
                "valor": item.valor_previsto,
                "tipo": (
                    "saida" if item.despesa_receita.natureza == "Despesa" else "entrada"
                ),
            }
        )
    faturas_pendentes = (
        CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == current_user.id,
            CrediarioFatura.status == "Pendente",
        )
        .options(joinedload(CrediarioFatura.crediario))
        .all()
    )
    for fatura in faturas_pendentes:
        proximos_movimentos.append(
            {
                "data": fatura.data_vencimento_fatura,
                "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                "valor": fatura.valor_total_fatura - fatura.valor_pago_fatura,
                "tipo": "saida",
            }
        )
    parcelas_pendentes = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.status == "Pendente",
            FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
        )
        .options(joinedload(FinanciamentoParcela.financiamento))
        .all()
    )
    for parcela in parcelas_pendentes:
        proximos_movimentos.append(
            {
                "data": parcela.data_vencimento,
                "descricao": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                "valor": parcela.valor_total_previsto,
                "tipo": "saida",
            }
        )
    salarios_pendentes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.status == "Pendente",
    ).all()
    for salario in salarios_pendentes:
        if salario.salario_liquido > 0:
            proximos_movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Salário Líquido (Ref: {salario.mes_referencia})",
                    "valor": salario.salario_liquido,
                    "tipo": "entrada",
                }
            )
        if salario.total_beneficios > 0:
            proximos_movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Benefícios (Ref: {salario.mes_referencia})",
                    "valor": salario.total_beneficios,
                    "tipo": "entrada",
                }
            )
    proximos_movimentos.sort(key=lambda x: x["data"])
    financiamentos_ativos = Financiamento.query.filter_by(
        usuario_id=current_user.id
    ).all()
    crediarios_ativos = Crediario.query.filter_by(
        usuario_id=current_user.id, ativa=True
    ).all()

    pending_requests_count = 0
    if current_user.is_admin:
        pending_requests_count = SolicitacaoAcesso.query.filter_by(
            status="Pendente"
        ).count()

    return render_template(
        "dashboard.html",
        contas_do_usuario=contas_do_usuario,
        kpis=kpis,
        proximos_movimentos=proximos_movimentos[:10],
        pending_requests=pending_requests_count,
        financiamentos=financiamentos_ativos,
        crediarios=crediarios_ativos,
    )


@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(main_bp.root_path, "..", "static", "images"),
        "favicon.png",
        mimetype="image/png",
    )
