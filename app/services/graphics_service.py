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
from app.utils import (
    NATUREZA_DESPESA,
    NATUREZA_RECEITA,
    STATUS_AMORTIZADO,
    STATUS_PAGO,
    STATUS_PARCIAL_PAGO,
    STATUS_PENDENTE,
    STATUS_RECEBIDO,
    TIPO_FIXA,
    TIPO_VARIAVEL,
)


def get_monthly_graphics_data(user_id, year, month):
    """
    Busca e calcula todos os dados para os gráficos mensais, com lógica detalhada
    para o gráfico de progresso (incluindo descontos e custos extras).
    """
    data_inicio_mes = date(year, month, 1)
    data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )

    # --- 1. CÁLCULO DO VALOR TOTAL PREVISTO PARA O MÊS (O NOSSO 100%) ---
    despesas_vencimento = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == NATUREZA_DESPESA,
        )
        .all()
    )
    faturas_vencimento = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.data_vencimento_fatura.between(data_inicio_mes, data_fim_mes),
    ).all()
    parcelas_vencimento = FinanciamentoParcela.query.filter(
        FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
    ).all()

    total_previsto_mes = (
        sum(d.valor_previsto for d in despesas_vencimento)
        + sum(f.valor_total_fatura for f in faturas_vencimento)
        + sum(p.valor_total_previsto for p in parcelas_vencimento)
    )

    # --- 2. CÁLCULO DETALHADO DAS FATIAS DO GRÁFICO ---
    valor_pago_real = Decimal("0.00")
    valor_descontos = Decimal("0.00")
    valor_custos_extras = Decimal("0.00")
    valor_previsto_dos_itens_pagos = Decimal("0.00")

    for item in filter(lambda d: d.status == STATUS_PAGO, despesas_vencimento):
        valor_pago_real += item.valor_realizado
        valor_previsto_dos_itens_pagos += item.valor_previsto
        diferenca = item.valor_previsto - item.valor_realizado
        if diferenca > 0:
            valor_descontos += diferenca
        else:
            valor_custos_extras += abs(diferenca)

    for item in filter(
        lambda f: f.status in [STATUS_PAGO, STATUS_PARCIAL_PAGO], faturas_vencimento
    ):
        valor_pago_real += item.valor_pago_fatura
        valor_previsto_dos_itens_pagos += item.valor_total_fatura
        diferenca = item.valor_total_fatura - item.valor_pago_fatura
        if diferenca > 0 and item.status == STATUS_PAGO:
            valor_descontos += diferenca
        elif diferenca < 0:
            valor_custos_extras += abs(diferenca)

    for item in filter(
        lambda p: p.status in [STATUS_PAGO, STATUS_AMORTIZADO], parcelas_vencimento
    ):
        if item.valor_pago is not None:
            valor_pago_real += item.valor_pago
            valor_previsto_dos_itens_pagos += item.valor_total_previsto
            diferenca = item.valor_total_previsto - item.valor_pago
            if diferenca > 0:
                valor_descontos += diferenca
            else:
                valor_custos_extras += abs(diferenca)

    valor_pendente = total_previsto_mes - valor_previsto_dos_itens_pagos

    dados_progresso_valores = {
        "labels": [],
        "valores": [],
        "total": float(total_previsto_mes),
    }
    if valor_pago_real > 0:
        dados_progresso_valores["labels"].append(STATUS_PAGO)
        dados_progresso_valores["valores"].append(float(valor_pago_real))
    if valor_descontos > 0:
        dados_progresso_valores["labels"].append("Descontos")
        dados_progresso_valores["valores"].append(float(valor_descontos))
    if valor_custos_extras > 0:
        dados_progresso_valores["labels"].append("Custos Extras")
        dados_progresso_valores["valores"].append(float(valor_custos_extras))
    if valor_pendente > 0:
        dados_progresso_valores["labels"].append(STATUS_PENDENTE)
        dados_progresso_valores["valores"].append(float(valor_pendente))

    # --- 3. DADOS DOS OUTROS GRÁFICOS ---
    balanco = relatorios_service.get_balanco_mensal(user_id, year, month)
    saidas_fixas = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRec
    ).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == STATUS_PAGO,
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == NATUREZA_DESPESA,
        DespRec.tipo == TIPO_FIXA,
    ).scalar() or Decimal(
        "0.00"
    )
    saidas_variaveis = db.session.query(
        func.sum(DespRecMovimento.valor_realizado)
    ).join(DespRec).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == STATUS_PAGO,
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == NATUREZA_DESPESA,
        DespRec.tipo == TIPO_VARIAVEL,
    ).scalar() or Decimal(
        "0.00"
    )
    saidas_financiamento = db.session.query(
        func.sum(FinanciamentoParcela.valor_pago)
    ).filter(
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
        FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.status.in_([STATUS_PAGO, STATUS_AMORTIZADO]),
    ).scalar() or Decimal(
        "0.00"
    )
    saidas_crediario = db.session.query(
        func.sum(CrediarioFatura.valor_pago_fatura)
    ).filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
        CrediarioFatura.status.in_([STATUS_PAGO, STATUS_PARCIAL_PAGO]),
    ).scalar() or Decimal(
        "0.00"
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
    entradas_salario = Decimal("0.00")
    entradas_beneficios = Decimal("0.00")
    salarios_recebidos = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
    ).all()
    for salario in salarios_recebidos:
        if salario.movimento_bancario_salario_id:
            entradas_salario += salario.salario_liquido
        if salario.movimento_bancario_beneficio_id:
            entradas_beneficios += salario.total_beneficios
    outras_receitas = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRec
    ).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == STATUS_RECEBIDO,
        DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == NATUREZA_RECEITA,
    ).scalar() or Decimal(
        "0.00"
    )
    dados_entradas = {
        "labels": ["Salários", "Benefícios", "Outras Receitas"],
        "valores": [
            float(entradas_salario),
            float(entradas_beneficios),
            float(outras_receitas),
        ],
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


def get_financing_progress_data(user_id, year, financiamento_id):
    """
    Busca os dados para o gráfico de progresso de um financiamento específico.
    """
    if not financiamento_id:
        return None

    financiamento = Financiamento.query.filter_by(
        id=financiamento_id, usuario_id=user_id
    ).first()

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
                FinanciamentoParcela.status == STATUS_PAGO,
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


def get_financing_summary_data(user_id, financiamento_id=None):
    """
    Busca a contagem de parcelas de financiamento por status.
    Se um financiamento_id for fornecido, filtra para apenas esse financiamento.
    """
    query = (
        db.session.query(
            FinanciamentoParcela.status,
            func.count(FinanciamentoParcela.id).label("total"),
        )
        .join(Financiamento)
        .filter(Financiamento.usuario_id == user_id)
    )

    if financiamento_id:
        query = query.filter(Financiamento.id == financiamento_id)

    counts = (
        query.group_by(FinanciamentoParcela.status)
        .order_by(func.count(FinanciamentoParcela.id).desc())
        .all()
    )

    if not counts:
        return None

    labels = [item.status for item in counts]
    valores = [item.total for item in counts]

    return {"labels": labels, "valores": valores}
