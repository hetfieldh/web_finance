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
    determinado mês, incluindo o percentual de comprometimento da renda.
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

    # --- LÓGICA DO COMPROMETIMENTO ADICIONADA AQUI ---
    comprometimento = 0
    if total_receitas > 0:
        # Arredonda para 2 casas decimais
        comprometimento = round((total_despesas / total_receitas) * 100, 2)

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "balanco": total_receitas - total_despesas,
        "comprometimento": comprometimento,  # <-- Adicionado ao retorno
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

    # Receitas (Salários e Outras)
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
                    "origem": f"Salário (Ref: {s.mes_referencia})",
                    "categoria": "Salário",
                    "valor": s.salario_liquido,
                }
            )
        if s.movimento_bancario_beneficio_id:
            movimentacoes_consolidadas.append(
                {
                    "data": s.data_recebimento,
                    "origem": f"Benefícios (Ref: {s.mes_referencia})",
                    "categoria": "Benefício",
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
                "origem": receita.despesa_receita.nome,
                "categoria": "Receita",
                "valor": receita.valor_realizado,
            }
        )

    # Despesas (Gerais)
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
                "origem": despesa.despesa_receita.nome,
                "categoria": "Despesa",
                "valor": despesa.valor_realizado,
            }
        )

    # Faturas de Crediário Pagas
    faturas_pagas = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
        CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
    ).all()
    for fatura in faturas_pagas:
        movimentacoes_consolidadas.append(
            {
                "data": fatura.data_pagamento,
                "origem": f"Fatura: {fatura.crediario.nome_crediario}",
                "categoria": "Crediário",
                "valor": fatura.valor_pago_fatura,
            }
        )

    # Parcelas de Financiamento Pagas
    parcelas_pagas_no_mes = FinanciamentoParcela.query.filter(
        FinanciamentoParcela.status.in_(["Paga", "Amortizada"]),
        FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
    ).all()

    # Agrupamento para Financiamentos
    financiamentos_pagos = {}
    for p in parcelas_pagas_no_mes:
        key = (p.financiamento_id, p.status)
        if key not in financiamentos_pagos:
            tipo = "Amortização" if p.status == "Amortizada" else "Financiamento"
            financiamentos_pagos[key] = {
                "data": p.data_pagamento,
                "origem": f"{tipo}: {p.financiamento.nome_financiamento}",
                "categoria": tipo,
                "valor": Decimal("0.00"),
            }
        financiamentos_pagos[key]["valor"] += p.valor_pago

    movimentacoes_consolidadas.extend(financiamentos_pagos.values())

    movimentacoes_consolidadas.sort(key=lambda x: x["data"])

    return movimentacoes_consolidadas


def get_extrato_detalhado_mensal(user_id, ano, mes):
    """
    Busca todas as transações individuais (entradas e saídas) realizadas
    em um determinado mês para montar um extrato cronológico.
    """
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    movimentacoes = []

    # 1. Busca Despesas e Receitas pagas/recebidas no mês
    desp_rec = DespRecMovimento.query.filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRecMovimento.status.in_(["Pago", "Recebido"]),
    ).all()
    for item in desp_rec:
        movimentacoes.append(
            {
                "data": item.data_pagamento,
                "origem": item.despesa_receita.nome,
                "categoria": item.despesa_receita.natureza,
                "valor": item.valor_realizado,
            }
        )

    # 2. Busca Faturas de Crediário pagas no mês
    faturas = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
    ).all()
    for fatura in faturas:
        movimentacoes.append(
            {
                "data": fatura.data_pagamento,
                "origem": f"Fatura {fatura.crediario.nome_crediario}",
                "categoria": "Crediário",
                "valor": fatura.valor_pago_fatura,
            }
        )

    # 3. Busca Parcelas de Financiamento pagas no mês
    parcelas = FinanciamentoParcela.query.filter(
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
        FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.status.in_(["Paga", "Amortizada"]),
    ).all()
    for parcela in parcelas:
        descricao = f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})"
        tipo = "Amortização" if parcela.status == "Amortizada" else "Financiamento"
        movimentacoes.append(
            {
                "data": parcela.data_pagamento,
                "origem": descricao,
                "categoria": tipo,
                "valor": parcela.valor_pago,
            }
        )

    # 4. Busca Salários e Benefícios recebidos no mês
    salarios = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
    ).all()
    for salario in salarios:
        if salario.movimento_bancario_salario_id:
            movimentacoes.append(
                {
                    "data": salario.data_recebimento,
                    "origem": f"Salário (Ref: {salario.mes_referencia})",
                    "categoria": "Salário",
                    "valor": salario.salario_liquido,
                }
            )
        if salario.movimento_bancario_beneficio_id:
            movimentacoes.append(
                {
                    "data": salario.data_recebimento,
                    "origem": f"Benefícios (Ref: {salario.mes_referencia})",
                    "categoria": "Benefício",
                    "valor": salario.total_beneficios,
                }
            )

    movimentacoes.sort(key=lambda x: x["data"])

    return movimentacoes
