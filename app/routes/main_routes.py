# app/routes/main_routes.py

from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models.conta_model import Conta
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento

main_bp = Blueprint("main", __name__)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # --- DADOS BÁSICOS ---
    contas_do_usuario = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco.asc())
        .all()
    )

    # --- CÁLCULO DOS KPIs ---
    hoje = date.today()
    data_inicio_mes = hoje.replace(day=1)
    if hoje.month == 12:
        data_fim_mes = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(
            days=1
        )
    else:
        data_fim_mes = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)

    # 1. Saldos Separados
    saldo_operacional = Decimal("0.00")
    saldo_investimentos = Decimal("0.00")
    tipos_operacionais = ["Corrente", "Digital", "Dinheiro"]
    for conta in contas_do_usuario:
        if conta.tipo in tipos_operacionais:
            saldo_operacional += conta.saldo_atual
        else:
            saldo_investimentos += conta.saldo_atual

    # 2. Receitas Realizadas no Mês
    receitas_realizadas = Decimal("0.00")
    salario_recebido = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.movimento_bancario_id.isnot(None),
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

    # 3. Despesas Realizadas no Mês
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

    # 4. Balanço do Mês
    balanco_mes = receitas_realizadas - despesas_realizadas

    # --- PRÓXIMOS MOVIMENTOS (ENTRADAS E SAÍDAS) ---
    proximos_movimentos = []

    # Despesas e Receitas Pendentes
    desp_rec_pendentes = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.status == "Pendente",
            DespRecMovimento.data_vencimento >= hoje,
        )
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

    # Faturas de Crediário Abertas/Fechadas
    faturas_pendentes = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == current_user.id,
        CrediarioFatura.status.in_(["Aberta", "Fechada"]),
        CrediarioFatura.data_vencimento_fatura >= hoje,
    ).all()
    for fatura in faturas_pendentes:
        proximos_movimentos.append(
            {
                "data": fatura.data_vencimento_fatura,
                "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                "valor": fatura.valor_total_fatura - fatura.valor_pago_fatura,
                "tipo": "saida",
            }
        )

    # Parcelas de Financiamento a Pagar
    parcelas_pendentes = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.status == "A Pagar",
            FinanciamentoParcela.data_vencimento >= hoje,
            FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
        )
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

    # Salários e Benefícios Pendentes de Recebimento
    salarios_pendentes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.movimento_bancario_id.is_(None),
        SalarioMovimento.data_recebimento >= hoje,
    ).all()
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

    # Ordena a lista final por data e pega os 10 primeiros
    proximos_movimentos.sort(key=lambda x: x["data"])

    kpis = {
        "saldo_operacional": saldo_operacional,
        "saldo_investimentos": saldo_investimentos,
        "receitas_mes": receitas_realizadas,
        "despesas_mes": despesas_realizadas,
        "balanco_mes": balanco_mes,
    }

    return render_template(
        "dashboard.html",
        contas_do_usuario=contas_do_usuario,
        kpis=kpis,
        proximos_movimentos=proximos_movimentos[:10],
    )
