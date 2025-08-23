# app/services/relatorios_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento


def get_balanco_mensal(user_id, ano, mes):
    """
    Calcula o balanço consolidado de receitas e despesas realizadas para um
    determinado mês.
    """
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    # --- CÁLCULO DE RECEITAS ---
    total_receitas = Decimal("0.00")
    salarios_mes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.status.in_(["Recebido", "Parcialmente Recebido"]),
    ).all()

    for s in salarios_mes:
        if s.movimento_bancario_salario_id:
            total_receitas += s.salario_liquido
        if s.movimento_bancario_beneficio_id:
            total_receitas += s.total_beneficios

    outras_receitas = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRec
    ).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == "Recebido",
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == "Receita",
    ).scalar() or Decimal(
        "0.00"
    )
    total_receitas += outras_receitas

    # --- CÁLCULO DE DESPESAS ---
    total_despesas = Decimal("0.00")
    despesas_gerais = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRec
    ).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == "Pago",
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == "Despesa",
    ).scalar() or Decimal(
        "0.00"
    )
    total_despesas += despesas_gerais

    faturas_pagas = db.session.query(
        func.sum(CrediarioFatura.valor_pago_fatura)
    ).filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
        CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
    ).scalar() or Decimal(
        "0.00"
    )
    total_despesas += faturas_pagas

    parcelas_pagas = db.session.query(func.sum(FinanciamentoParcela.valor_pago)).filter(
        FinanciamentoParcela.status.in_(["Paga", "Amortizada"]),
        FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
    ).scalar() or Decimal("0.00")
    total_despesas += parcelas_pagas

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "balanco": total_receitas - total_despesas,
    }


def get_fluxo_caixa_mensal_consolidado(user_id, ano, mes):
    """
    Busca e consolida todas as entradas e saídas de caixa realizadas em um mês,
    agrupadas por sua origem.
    """
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    movimentacoes_consolidadas = []

    # 1. Receitas (Salários e Outras)
    salarios_mes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.status.in_(["Recebido", "Parcialmente Recebido"]),
    ).all()

    for s in salarios_mes:
        if s.movimento_bancario_salario_id:
            movimentacoes_consolidadas.append(
                {
                    "data": s.data_recebimento,
                    "descricao": f"Salário (Ref: {s.mes_referencia})",
                    "categoria": "Receita",
                    "valor": s.salario_liquido,
                }
            )
        if s.movimento_bancario_beneficio_id:
            movimentacoes_consolidadas.append(
                {
                    "data": s.data_recebimento,
                    "descricao": f"Benefícios (Ref: {s.mes_referencia})",
                    "categoria": "Receita",
                    "valor": s.total_beneficios,
                }
            )

    outras_receitas = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == "Recebido",
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == "Receita",
        )
        .all()
    )
    for receita in outras_receitas:
        movimentacoes_consolidadas.append(
            {
                "data": receita.data_pagamento,
                "descricao": f"Receita: {receita.despesa_receita.nome}",
                "categoria": "Receita",
                "valor": receita.valor_realizado,
            }
        )

    # 2. Despesas (Gerais)
    despesas_gerais = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == "Pago",
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == "Despesa",
        )
        .all()
    )
    for despesa in despesas_gerais:
        movimentacoes_consolidadas.append(
            {
                "data": despesa.data_pagamento,
                "descricao": f"Despesa: {despesa.despesa_receita.nome}",
                "categoria": "Despesa",
                "valor": despesa.valor_realizado,
            }
        )

    # 3. Faturas de Crediário Pagas
    faturas_pagas = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
        CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
    ).all()
    for fatura in faturas_pagas:
        movimentacoes_consolidadas.append(
            {
                "data": fatura.data_pagamento,
                "descricao": f"Fatura: {fatura.crediario.nome_crediario}",
                "categoria": "Crediário",
                "valor": fatura.valor_pago_fatura,
            }
        )

    # 4. Parcelas de Financiamento (Separando Pagas e Amortizadas)
    parcelas_pagas_no_mes = FinanciamentoParcela.query.filter(
        FinanciamentoParcela.status.in_(["Paga", "Amortizada"]),
        FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
    ).all()

    pagamentos_financiamento = {}
    amortizacoes_financiamento = {}

    for p in parcelas_pagas_no_mes:
        key = p.financiamento_id

        if p.status == "Paga":
            if key not in pagamentos_financiamento:
                pagamentos_financiamento[key] = {
                    "data": p.data_pagamento,
                    "descricao": f"Financiamento: {p.financiamento.nome_financiamento}",
                    "categoria": "Financiamento",
                    "valor": Decimal("0.00"),
                }
            pagamentos_financiamento[key]["valor"] += p.valor_pago

        elif p.status == "Amortizada":
            if key not in amortizacoes_financiamento:
                amortizacoes_financiamento[key] = {
                    "data": p.data_pagamento,
                    "descricao": f"Amortização: {p.financiamento.nome_financiamento}",
                    "categoria": "Amortização",
                    "valor": Decimal("0.00"),
                }
            amortizacoes_financiamento[key]["valor"] += p.valor_pago

    movimentacoes_consolidadas.extend(pagamentos_financiamento.values())
    movimentacoes_consolidadas.extend(amortizacoes_financiamento.values())

    # Ordenar a lista final por data
    movimentacoes_consolidadas.sort(key=lambda x: x["data"])

    return movimentacoes_consolidadas
