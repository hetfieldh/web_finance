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
