# app/services/graphics_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento


def get_monthly_graphics_data(user_id, year, month):
    """
    Busca e calcula todos os dados para os gráficos mensais (progresso, saídas, entradas).
    Retorna um dicionário com todos os dados consolidados.
    """
    data_inicio_mes = date(year, month, 1)
    data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )

    # --- DADOS PARA GRÁFICO DE PROGRESSO ---
    total_obrigacoes = 0
    obrigacoes_concluidas = 0

    despesas_mes = DespRecMovimento.query.filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
        DespRecMovimento.despesa_receita.has(natureza="Despesa"),
    ).all()
    faturas_mes = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.data_vencimento_fatura.between(data_inicio_mes, data_fim_mes),
    ).all()
    parcelas_mes = FinanciamentoParcela.query.filter(
        FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
    ).all()

    total_obrigacoes += len(despesas_mes) + len(faturas_mes) + len(parcelas_mes)
    obrigacoes_concluidas += sum(1 for d in despesas_mes if d.status == "Pago")
    obrigacoes_concluidas += sum(1 for f in faturas_mes if f.status == "Paga")
    obrigacoes_concluidas += sum(1 for p in parcelas_mes if p.status == "Paga")

    salarios_mes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
    ).all()
    receitas_mes = DespRecMovimento.query.filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
        DespRecMovimento.despesa_receita.has(natureza="Receita"),
    ).all()

    total_obrigacoes += len(salarios_mes) + len(receitas_mes)
    obrigacoes_concluidas += sum(1 for s in salarios_mes if s.status == "Recebido")
    obrigacoes_concluidas += sum(1 for r in receitas_mes if r.status == "Recebido")

    progresso_percentual = (
        (obrigacoes_concluidas / total_obrigacoes * 100) if total_obrigacoes > 0 else 0
    )

    dados_progresso = {
        "concluidas": obrigacoes_concluidas,
        "pendentes": total_obrigacoes - obrigacoes_concluidas,
        "percentual": round(progresso_percentual),
    }

    # --- DADOS PARA GRÁFICO DE SAÍDAS ---
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

    saidas_financiamento = (
        db.session.query(func.sum(ContaMovimento.valor))
        .join(
            FinanciamentoParcela,
            FinanciamentoParcela.movimento_bancario_id == ContaMovimento.id,
        )
        .filter(
            FinanciamentoParcela.status == "Paga",
            FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
            FinanciamentoParcela.financiamento.has(usuario_id=user_id),
        )
        .scalar()
        or 0
    )

    saidas_crediario = (
        db.session.query(func.sum(CrediarioFatura.valor_pago_fatura))
        .filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
            CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
        )
        .scalar()
        or 0
    )

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

    # --- DADOS PARA GRÁFICO DE ENTRADAS ---
    salario_liquido_mes = Decimal("0.00")
    beneficios_mes = Decimal("0.00")

    salarios_recebidos = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.status.in_(["Recebido", "Parcialmente Recebido"]),
    ).all()

    for s in salarios_recebidos:
        salario_liquido_mes += sum(
            i.valor for i in s.itens if i.salario_item.tipo == "Provento"
        ) - sum(
            i.valor for i in s.itens if i.salario_item.tipo in ["Imposto", "Desconto"]
        )
        beneficios_mes += sum(
            i.valor for i in s.itens if i.salario_item.tipo == "Benefício"
        )

    outras_receitas_mes = (
        db.session.query(func.sum(DespRecMovimento.valor_realizado))
        .join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == "Recebido",
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == "Receita",
        )
        .scalar()
        or 0
    )

    dados_entradas = {
        "labels": ["Salário Líquido", "Benefícios", "Outras Receitas"],
        "valores": [
            float(salario_liquido_mes),
            float(beneficios_mes),
            float(outras_receitas_mes),
        ],
    }

    return {
        "dados_progresso": dados_progresso,
        "dados_saidas": dados_saidas,
        "dados_entradas": dados_entradas,
    }


def get_annual_evolution_data(user_id, year):
    """
    Busca e calcula os dados de evolução de receitas e despesas para um ano inteiro.
    Retorna um dicionário com os dados para o gráfico de evolução.
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
        data_inicio_mes = date(year, month, 1)
        data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        total_receitas_mes = Decimal("0.00")
        salarios_mes = SalarioMovimento.query.filter(
            SalarioMovimento.usuario_id == user_id,
            SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
            SalarioMovimento.status.in_(["Recebido", "Parcialmente Recebido"]),
        ).all()
        for s in salarios_mes:
            total_receitas_mes += sum(
                i.valor
                for i in s.itens
                if i.salario_item.tipo in ["Provento", "Benefício"]
            ) - sum(
                i.valor
                for i in s.itens
                if i.salario_item.tipo in ["Imposto", "Desconto"]
            )

        outras_receitas_mes = (
            db.session.query(func.sum(DespRecMovimento.valor_realizado))
            .join(DespRec)
            .filter(
                DespRecMovimento.usuario_id == user_id,
                DespRecMovimento.status == "Recebido",
                DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
                DespRec.natureza == "Receita",
            )
            .scalar()
            or 0
        )
        total_receitas_mes += outras_receitas_mes
        receitas_por_mes[month - 1] = float(total_receitas_mes)

        total_despesas_mes = Decimal("0.00")
        despesas_normais = (
            db.session.query(func.sum(DespRecMovimento.valor_realizado))
            .join(DespRec)
            .filter(
                DespRecMovimento.usuario_id == user_id,
                DespRecMovimento.status == "Pago",
                DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
                DespRec.natureza == "Despesa",
            )
            .scalar()
            or 0
        )
        total_despesas_mes += despesas_normais

        financiamentos_mes = (
            db.session.query(func.sum(FinanciamentoParcela.valor_total_previsto))
            .filter(
                FinanciamentoParcela.status == "Paga",
                FinanciamentoParcela.data_pagamento.between(
                    data_inicio_mes, data_fim_mes
                ),
                FinanciamentoParcela.financiamento.has(usuario_id=user_id),
            )
            .scalar()
            or 0
        )
        total_despesas_mes += financiamentos_mes

        crediarios_mes = (
            db.session.query(func.sum(CrediarioFatura.valor_pago_fatura))
            .filter(
                CrediarioFatura.usuario_id == user_id,
                CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
                CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
            )
            .scalar()
            or 0
        )
        total_despesas_mes += crediarios_mes
        despesas_por_mes[month - 1] = float(total_despesas_mes)

    balanco_por_mes = [r - d for r, d in zip(receitas_por_mes, despesas_por_mes)]

    return {
        "labels": labels,
        "receitas": receitas_por_mes,
        "despesas": despesas_por_mes,
        "balanco": balanco_por_mes,
    }


def get_financing_progress_data(user_id, year):
    """
    Busca os dados de progresso de pagamento de um financiamento para um ano.
    Foca no primeiro financiamento encontrado para o usuário.
    """
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
            db.session.query(func.sum(ContaMovimento.valor))
            .join(
                FinanciamentoParcela,
                FinanciamentoParcela.movimento_bancario_id == ContaMovimento.id,
            )
            .filter(
                FinanciamentoParcela.financiamento_id == financiamento.id,
                FinanciamentoParcela.status == "Paga",
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
