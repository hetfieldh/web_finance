# app/services/graphics_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento
from app.services import relatorios_service


def get_monthly_graphics_data(user_id, year, month):
    """
    Busca e calcula todos os dados para os gráficos mensais.
    """
    data_inicio_mes = date(year, month, 1)
    data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )

    # --- Cálculo para o gráfico de rosca (Progresso) ---
    total_despesas_previsto = (
        db.session.query(func.sum(DespRecMovimento.valor_previsto))
        .join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == "Despesa",
        )
        .scalar()
        or 0
    )
    total_faturas_previsto = (
        db.session.query(func.sum(CrediarioFatura.valor_total_fatura))
        .filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.data_vencimento_fatura.between(
                data_inicio_mes, data_fim_mes
            ),
        )
        .scalar()
        or 0
    )
    total_parcelas_previsto = (
        db.session.query(func.sum(FinanciamentoParcela.valor_total_previsto))
        .filter(
            FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
            FinanciamentoParcela.financiamento.has(usuario_id=user_id),
        )
        .scalar()
        or 0
    )
    total_previsto_mes = (
        total_despesas_previsto + total_faturas_previsto + total_parcelas_previsto
    )

    balanco = relatorios_service.get_balanco_mensal(user_id, year, month)
    total_pago_mes = balanco["despesas"]
    total_pendente_mes = total_previsto_mes - total_pago_mes

    dados_progresso_valores = {
        "total": float(total_previsto_mes),
        "pago": float(total_pago_mes),
        "pendente": float(total_pendente_mes if total_pendente_mes > 0 else 0),
    }

    saidas_fixas = (
        db.session.query(func.sum(DespRecMovimento.valor_realizado))
        .join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == "Pago",
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == "Despesa",
            DespRec.tipo == "Fixa",
        )
        .scalar()
        or 0
    )
    saidas_variaveis = (
        db.session.query(func.sum(DespRecMovimento.valor_realizado))
        .join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == "Pago",
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == "Despesa",
            DespRec.tipo == "Variável",
        )
        .scalar()
        or 0
    )
    saidas_financiamento = balanco.get("financiamentos", 0)
    saidas_crediario = balanco.get("crediarios", 0)

    dados_saidas = {
        "labels": [
            "Despesas Fixas",
            "Despesas Variáveis",
            "Financiamentos",
            "Crediários",
        ],
        "valores": [
            float(saidas_fixas),
            float(saidas_variaveis),
            float(saidas_financiamento),
            float(saidas_crediario),
        ],
    }

    dados_entradas = {
        "labels": ["Receitas Totais"],
        "valores": [float(balanco["receitas"])],
    }

    return {
        "dados_progresso_valores": dados_progresso_valores,
        "dados_saidas": dados_saidas,
        "dados_entradas": dados_entradas,
    }


def get_annual_evolution_data(user_id, year):
    """
    Busca e calcula os dados de evolução de receitas e despesas para um ano inteiro
    utilizando o serviço de relatórios centralizado.
    """
    labels = [
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
    receitas_por_mes = [0.0] * 12
    despesas_por_mes = [0.0] * 12

    for month in range(1, 13):
        balanco = relatorios_service.get_balanco_mensal(user_id, year, month)
        receitas_por_mes[month - 1] = float(balanco["receitas"])
        despesas_por_mes[month - 1] = float(balanco["despesas"])

    balanco_por_mes = [r - d for r, d in zip(receitas_por_mes, despesas_por_mes)]

    return {
        "labels": labels,
        "receitas": receitas_por_mes,
        "despesas": despesas_por_mes,
        "balanco": balanco_por_mes,
    }


def get_financing_progress_data(user_id, year):
    financiamento = Financiamento.query.filter_by(usuario_id=user_id).first()

    if not financiamento:
        return None

    labels = [
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
    valores_previstos = [0.0] * 12
    valores_realizados = [0.0] * 12

    for month in range(1, 13):
        data_inicio_mes = date(year, month, 1)
        data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        previsto_mes = (
            db.session.query(func.sum(FinanciamentoParcela.valor_total_previsto))
            .filter(
                FinanciamentoParcela.financiamento_id == financiamento.id,
                FinanciamentoParcela.data_vencimento.between(
                    data_inicio_mes, data_fim_mes
                ),
            )
            .scalar()
            or 0
        )
        valores_previstos[month - 1] = float(previsto_mes)

        realizado_mes = (
            db.session.query(func.sum(FinanciamentoParcela.valor_pago))
            .filter(
                FinanciamentoParcela.financiamento_id == financiamento.id,
                FinanciamentoParcela.status.in_(["Paga", "Amortizada"]),
                FinanciamentoParcela.data_pagamento.between(
                    data_inicio_mes, data_fim_mes
                ),
            )
            .scalar()
            or 0
        )
        valores_realizados[month - 1] = float(realizado_mes)

    return {
        "nome_financiamento": financiamento.nome_financiamento,
        "labels": labels,
        "previsto": valores_previstos,
        "realizado": valores_realizados,
    }
