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

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    contas_do_usuario = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco.asc())
        .all()
    )

    hoje = date.today()
    data_inicio_mes = hoje.replace(day=1)
    if hoje.month == 12:
        data_fim_mes = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(
            days=1
        )
    else:
        data_fim_mes = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)

    saldo_operacional = sum(
        c.saldo_atual
        for c in contas_do_usuario
        if c.tipo in ["Corrente", "Digital", "Dinheiro"]
    )
    saldo_investimentos = sum(
        c.saldo_atual
        for c in contas_do_usuario
        if c.tipo in ["Poupança", "Caixinha", "Investimento"]
    )
    saldo_beneficios = sum(
        c.saldo_atual for c in contas_do_usuario if c.tipo == "Benefício"
    )
    saldo_fgts = sum(c.saldo_atual for c in contas_do_usuario if c.tipo == "FGTS")

    receitas_realizadas = Decimal("0.00")
    salario_recebido = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.status == "Recebido",
    ).first()
    if salario_recebido:
        receitas_realizadas += sum(
            i.valor for i in salario_recebido.itens if i.salario_item.tipo == "Provento"
        ) - sum(
            i.valor
            for i in salario_recebido.itens
            if i.salario_item.tipo in ["Imposto", "Desconto"]
        )

    outras_receitas = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRecMovimento.despesa_receita
    ).filter(
        DespRecMovimento.usuario_id == current_user.id,
        DespRecMovimento.status == "Pago",
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRecMovimento.despesa_receita.has(natureza="Receita"),
    ).scalar() or Decimal(
        "0.00"
    )
    receitas_realizadas += outras_receitas

    despesas_realizadas = Decimal("0.00")
    faturas_pagas = db.session.query(
        func.sum(CrediarioFatura.valor_pago_fatura)
    ).filter(
        CrediarioFatura.usuario_id == current_user.id,
        CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
        CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
    ).scalar() or Decimal(
        "0.00"
    )
    despesas_realizadas += faturas_pagas

    parcelas_pagas = db.session.query(
        func.sum(FinanciamentoParcela.valor_total_previsto)
    ).join(FinanciamentoParcela.financiamento).filter(
        FinanciamentoParcela.status == "Paga",
        FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
    ).scalar() or Decimal(
        "0.00"
    )
    despesas_realizadas += parcelas_pagas

    outras_despesas = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRecMovimento.despesa_receita
    ).filter(
        DespRecMovimento.usuario_id == current_user.id,
        DespRecMovimento.status == "Pago",
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRecMovimento.despesa_receita.has(natureza="Despesa"),
    ).scalar() or Decimal(
        "0.00"
    )
    despesas_realizadas += outras_despesas

    balanco_mes = receitas_realizadas - despesas_realizadas

    kpis = {
        "saldo_operacional": saldo_operacional,
        "saldo_investimentos": saldo_investimentos,
        "saldo_beneficios": saldo_beneficios,
        "saldo_fgts": saldo_fgts,
        "receitas_mes": receitas_realizadas,
        "despesas_mes": despesas_realizadas,
        "balanco_mes": balanco_mes,
    }

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

    salarios_pendentes = (
        SalarioMovimento.query.filter(
            SalarioMovimento.usuario_id == current_user.id,
            SalarioMovimento.status == "Pendente",
        )
        .options(
            subqueryload(SalarioMovimento.itens).joinedload(
                SalarioMovimentoItem.salario_item
            )
        )
        .all()
    )
    for salario in salarios_pendentes:
        salario_liquido = sum(
            i.valor for i in salario.itens if i.salario_item.tipo == "Provento"
        ) - sum(
            i.valor
            for i in salario.itens
            if i.salario_item.tipo in ["Imposto", "Desconto"]
        )
        total_beneficios = sum(
            i.valor for i in salario.itens if i.salario_item.tipo == "Benefício"
        )

        if salario_liquido > 0:
            proximos_movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Salário Líquido (Ref: {salario.mes_referencia})",
                    "valor": salario_liquido,
                    "tipo": "entrada",
                }
            )

        if total_beneficios > 0:
            proximos_movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Benefícios (Ref: {salario.mes_referencia})",
                    "valor": total_beneficios,
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
    saldos_crediarios = []
    for crediario in crediarios_ativos:
        saldo_devedor = db.session.query(func.sum(CrediarioParcela.valor_parcela)).join(
            CrediarioParcela.movimento_pai
        ).filter(
            CrediarioMovimento.crediario_id == crediario.id,
            CrediarioParcela.pago.is_(False),
        ).scalar() or Decimal(
            "0.00"
        )

        saldos_crediarios.append(
            {"nome": crediario.nome_crediario, "saldo_devedor": saldo_devedor}
        )

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
        saldos_crediarios=saldos_crediarios,
    )


@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(main_bp.root_path, "..", "static", "images"),
        "favicon.png",
        mimetype="image/png",
    )
