# app/services/relatorios_service.py

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_item_model import SalarioItem
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.utils import (
    NATUREZA_DESPESA,
    NATUREZA_RECEITA,
    STATUS_AMORTIZADO,
    STATUS_ATRASADO,
    STATUS_PAGO,
    STATUS_PARCIAL_PAGO,
    STATUS_PARCIAL_RECEBIDO,
    STATUS_PENDENTE,
    STATUS_RECEBIDO,
    TIPO_ENTRADA,
    TIPO_SAIDA,
)


def get_resumo_folha_anual(user_id, ano):
    from app.models.salario_item_model import SalarioItem
    from app.models.salario_movimento_item_model import SalarioMovimentoItem

    itens_salario_ano = (
        db.session.query(
            SalarioMovimentoItem.valor,
            func.extract("month", SalarioMovimento.data_recebimento).label("mes"),
            SalarioItem.nome,
            SalarioItem.tipo,
        )
        .join(
            SalarioMovimento,
            SalarioMovimentoItem.salario_movimento_id == SalarioMovimento.id,
        )
        .join(SalarioItem, SalarioMovimentoItem.salario_item_id == SalarioItem.id)
        .filter(
            SalarioMovimento.usuario_id == user_id,
            func.extract("year", SalarioMovimento.data_recebimento) == ano,
        )
        .all()
    )

    dados_pivotados = defaultdict(lambda: defaultdict(Decimal))
    verbas = {}

    for item in itens_salario_ano:
        dados_pivotados[item.nome][int(item.mes)] += item.valor
        if item.nome not in verbas:
            verbas[item.nome] = item.tipo

    meses = range(1, 13)
    categorias_desejadas = ["Provento", "Benefício", "Desconto", "Imposto", "FGTS"]
    tabela = {cat: [] for cat in categorias_desejadas}

    totais_proventos_mes = defaultdict(Decimal)
    totais_beneficios_mes = defaultdict(Decimal)
    totais_descontos_mes = defaultdict(Decimal)
    totais_impostos_mes = defaultdict(Decimal)

    verbas_ordenadas = sorted(verbas.keys())

    for nome_verba in verbas_ordenadas:
        tipo_verba = verbas[nome_verba]
        linha = {"nome": nome_verba, "valores_mes": [], "total_anual": Decimal("0.00")}

        for mes in meses:
            valor = dados_pivotados[nome_verba][mes]
            linha["valores_mes"].append(valor)
            linha["total_anual"] += valor

            if tipo_verba == "Provento":
                totais_proventos_mes[mes] += valor
            elif tipo_verba == "Benefício":
                totais_beneficios_mes[mes] += valor
            elif tipo_verba == "Desconto":
                totais_descontos_mes[mes] += valor
            elif tipo_verba == "Imposto":
                totais_impostos_mes[mes] += valor

        if tipo_verba in tabela:
            tabela[tipo_verba].append(linha)

    def calcular_linha_total(nome, totais_mes):
        total_anual = sum(totais_mes.values())
        valores_mes = [totais_mes[mes] for mes in meses]
        return {"nome": nome, "valores_mes": valores_mes, "total_anual": total_anual}

    total_proventos = calcular_linha_total("Total de Proventos", totais_proventos_mes)
    total_beneficios = calcular_linha_total(
        "Total de Benefícios", totais_beneficios_mes
    )
    total_descontos = calcular_linha_total("Total de Descontos", totais_descontos_mes)
    total_impostos = calcular_linha_total("Total de Impostos", totais_impostos_mes)

    salario_liquido_mes = [
        (totais_proventos_mes[mes] + totais_beneficios_mes[mes])
        - (totais_descontos_mes[mes] + totais_impostos_mes[mes])
        for mes in meses
    ]
    salario_liquido = {
        "nome": "Salário Líquido",
        "valores_mes": salario_liquido_mes,
        "total_anual": sum(salario_liquido_mes),
    }

    return {
        "tabela": tabela,
        "totais": {
            "proventos": total_proventos,
            "beneficios": total_beneficios,
            "descontos": total_descontos,
            "impostos": total_impostos,
        },
        "salario_liquido": salario_liquido,
        "meses": meses,
    }


def get_resumo_mensal(user_id, ano, mes):
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    from app.models.conta_model import Conta

    saldo_inicial = db.session.query(func.sum(ContaMovimento.valor)).join(Conta).filter(
        Conta.usuario_id == user_id,
        Conta.tipo.in_(["Corrente", "Poupança", "Outros"]),
        ContaMovimento.data_movimento < data_inicio_mes,
    ).scalar() or Decimal("0.00")

    movimentacoes = []
    total_receitas = Decimal("0.00")
    total_despesas = Decimal("0.00")

    desp_rec_mes = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
        )
        .options(joinedload(DespRecMovimento.despesa_receita))
        .all()
    )

    for item in desp_rec_mes:
        valor = (
            item.valor_realizado
            if item.status
            in [
                STATUS_PAGO,
                STATUS_RECEBIDO,
                STATUS_PARCIAL_PAGO,
                STATUS_PARCIAL_RECEBIDO,
            ]
            else item.valor_previsto
        )
        movimentacoes.append(
            {
                "data": item.data_vencimento,
                "descricao": item.despesa_receita.nome,
                "valor": valor,
                "tipo": item.despesa_receita.natureza,
                "status": item.status,
            }
        )
        if item.despesa_receita.natureza == NATUREZA_RECEITA:
            total_receitas += valor
        else:
            total_despesas += valor

    from app.models.crediario_model import Crediario

    faturas_mes = (
        CrediarioFatura.query.join(Crediario)
        .filter(
            Crediario.usuario_id == user_id,
            CrediarioFatura.data_vencimento_fatura.between(
                data_inicio_mes, data_fim_mes
            ),
        )
        .options(joinedload(CrediarioFatura.crediario))
        .all()
    )

    for fatura in faturas_mes:
        valor = (
            fatura.valor_pago_fatura
            if fatura.status in [STATUS_PAGO, STATUS_PARCIAL_PAGO]
            else fatura.valor_total_fatura
        )
        valor_calculo = (
            fatura.valor_total_fatura - fatura.valor_pago_fatura
            if fatura.status == STATUS_PARCIAL_PAGO
            else valor
        )
        movimentacoes.append(
            {
                "data": fatura.data_vencimento_fatura,
                "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                "valor": valor_calculo,
                "tipo": NATUREZA_DESPESA,
                "status": fatura.status,
            }
        )
        total_despesas += valor_calculo

    from app.models.financiamento_model import Financiamento

    parcelas_mes = (
        FinanciamentoParcela.query.join(Financiamento)
        .filter(
            Financiamento.usuario_id == user_id,
            FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
        )
        .options(joinedload(FinanciamentoParcela.financiamento))
        .all()
    )

    for parcela in parcelas_mes:
        valor = (
            parcela.valor_pago
            if parcela.status in [STATUS_PAGO, STATUS_AMORTIZADO]
            else parcela.valor_total_previsto
        )
        movimentacoes.append(
            {
                "data": parcela.data_vencimento,
                "descricao": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                "valor": valor,
                "tipo": NATUREZA_DESPESA,
                "status": parcela.status,
            }
        )
        total_despesas += valor

    salarios_mes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
    ).all()

    for salario in salarios_mes:
        if salario.salario_liquido > 0 and salario.status in [
            STATUS_PENDENTE,
            STATUS_RECEBIDO,
            STATUS_PARCIAL_RECEBIDO,
        ]:
            movimentacoes.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Salário Líquido (Ref: {salario.mes_referencia})",
                    "valor": salario.salario_liquido,
                    "tipo": NATUREZA_RECEITA,
                    "status": salario.status,
                }
            )
            total_receitas += salario.salario_liquido

        if salario.total_beneficios > 0 and salario.status in [
            STATUS_PENDENTE,
            STATUS_RECEBIDO,
            STATUS_PARCIAL_RECEBIDO,
        ]:
            movimentacoes.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Benefícios (Ref: {salario.mes_referencia})",
                    "valor": salario.total_beneficios,
                    "tipo": NATUREZA_RECEITA,
                    "status": salario.status,
                }
            )

    movimentacoes.sort(key=lambda x: x["data"])

    saldo_final_previsto = (saldo_inicial + total_receitas) - total_despesas

    return {
        "saldo_inicial": saldo_inicial,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_final_previsto": saldo_final_previsto,
        "movimentacoes": movimentacoes,
    }


def get_contas_a_vencer(user_id):
    hoje = date.today()
    data_limite = hoje + timedelta(days=7)
    movimentos = []

    desp_rec_a_vencer = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.data_vencimento.between(hoje, data_limite),
            DespRecMovimento.status.in_(
                [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]
            ),
        )
        .options(joinedload(DespRecMovimento.despesa_receita))
        .all()
    )
    for item in desp_rec_a_vencer:
        movimentos.append(
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

    faturas_a_vencer = (
        CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.data_vencimento_fatura.between(hoje, data_limite),
            CrediarioFatura.status.in_(
                [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]
            ),
        )
        .options(joinedload(CrediarioFatura.crediario))
        .all()
    )
    for fatura in faturas_a_vencer:
        movimentos.append(
            {
                "data": fatura.data_vencimento_fatura,
                "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                "valor": fatura.valor_total_fatura - fatura.valor_pago_fatura,
                "tipo": TIPO_SAIDA,
            }
        )

    parcelas_a_vencer = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.financiamento.has(usuario_id=user_id),
            FinanciamentoParcela.data_vencimento.between(hoje, data_limite),
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        )
        .options(joinedload(FinanciamentoParcela.financiamento))
        .all()
    )
    for parcela in parcelas_a_vencer:
        movimentos.append(
            {
                "data": parcela.data_vencimento,
                "descricao": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                "valor": parcela.valor_total_previsto,
                "tipo": TIPO_SAIDA,
            }
        )

    salarios_a_receber = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento.between(hoje, data_limite),
        SalarioMovimento.status.in_([STATUS_PENDENTE, STATUS_PARCIAL_RECEBIDO]),
    ).all()

    for salario in salarios_a_receber:
        if not salario.movimento_bancario_salario_id and salario.salario_liquido > 0:
            movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Salário Líquido (Ref: {salario.mes_referencia})",
                    "valor": salario.salario_liquido,
                    "tipo": TIPO_ENTRADA,
                }
            )
        if not salario.movimento_bancario_beneficio_id and salario.total_beneficios > 0:
            movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Benefícios (Ref: {salario.mes_referencia})",
                    "valor": salario.total_beneficios,
                    "tipo": TIPO_ENTRADA,
                }
            )

    movimentos.sort(key=lambda x: x["data"])
    return movimentos


def get_contas_vencidas(user_id):
    hoje = date.today()
    movimentos = []

    desp_rec_vencidas = (
        DespRecMovimento.query.join(DespRec)
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.data_vencimento < hoje,
            DespRecMovimento.status.in_(
                [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]
            ),
        )
        .options(joinedload(DespRecMovimento.despesa_receita))
        .all()
    )
    for item in desp_rec_vencidas:
        movimentos.append(
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

    faturas_vencidas = (
        CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.data_vencimento_fatura < hoje,
            CrediarioFatura.status.in_(
                [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]
            ),
        )
        .options(joinedload(CrediarioFatura.crediario))
        .all()
    )
    for fatura in faturas_vencidas:
        movimentos.append(
            {
                "data": fatura.data_vencimento_fatura,
                "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                "valor": fatura.valor_total_fatura - fatura.valor_pago_fatura,
                "tipo": TIPO_SAIDA,
            }
        )

    parcelas_vencidas = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.financiamento.has(usuario_id=user_id),
            FinanciamentoParcela.data_vencimento < hoje,
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        )
        .options(joinedload(FinanciamentoParcela.financiamento))
        .all()
    )
    for parcela in parcelas_vencidas:
        movimentos.append(
            {
                "data": parcela.data_vencimento,
                "descricao": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                "valor": parcela.valor_total_previsto,
                "tipo": TIPO_SAIDA,
            }
        )

    salarios_vencidos = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_recebimento < hoje,
        SalarioMovimento.status.in_([STATUS_PENDENTE, STATUS_PARCIAL_RECEBIDO]),
    ).all()

    for salario in salarios_vencidos:
        if not salario.movimento_bancario_salario_id and salario.salario_liquido > 0:
            movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Salário Líquido (Ref: {salario.mes_referencia})",
                    "valor": salario.salario_liquido,
                    "tipo": TIPO_ENTRADA,
                }
            )
        if not salario.movimento_bancario_beneficio_id and salario.total_beneficios > 0:
            movimentos.append(
                {
                    "data": salario.data_recebimento,
                    "descricao": f"Benefícios (Ref: {salario.mes_referencia})",
                    "valor": salario.total_beneficios,
                    "tipo": TIPO_ENTRADA,
                }
            )

    movimentos.sort(key=lambda x: x["data"])
    return movimentos


def get_balanco_mensal(user_id, ano, mes):
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    total_receitas = Decimal("0.00")
    salarios_mes = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == user_id,
        SalarioMovimento.data_criacao.between(data_inicio_mes, data_fim_mes),
        SalarioMovimento.status.in_([STATUS_RECEBIDO, STATUS_PARCIAL_RECEBIDO]),
    ).all()

    for s in salarios_mes:
        if s.movimento_bancario_salario_id:
            total_receitas += s.salario_liquido

    outras_receitas = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRec
    ).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == STATUS_RECEBIDO,
        DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == NATUREZA_RECEITA,
    ).scalar() or Decimal(
        "0.00"
    )
    total_receitas += outras_receitas

    total_despesas = Decimal("0.00")
    despesas_gerais = db.session.query(func.sum(DespRecMovimento.valor_realizado)).join(
        DespRec
    ).filter(
        DespRecMovimento.usuario_id == user_id,
        DespRecMovimento.status == STATUS_PAGO,
        DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
        DespRec.natureza == NATUREZA_DESPESA,
    ).scalar() or Decimal(
        "0.00"
    )
    total_despesas += despesas_gerais

    faturas_pagas = db.session.query(
        func.sum(CrediarioFatura.valor_pago_fatura)
    ).filter(
        CrediarioFatura.usuario_id == user_id,
        CrediarioFatura.status.in_([STATUS_PAGO, STATUS_PARCIAL_PAGO]),
        CrediarioFatura.data_vencimento_fatura.between(data_inicio_mes, data_fim_mes),
    ).scalar() or Decimal(
        "0.00"
    )
    total_despesas += faturas_pagas

    parcelas_pagas = db.session.query(func.sum(FinanciamentoParcela.valor_pago)).filter(
        FinanciamentoParcela.status.in_([STATUS_PAGO, STATUS_AMORTIZADO]),
        FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
        FinanciamentoParcela.financiamento.has(usuario_id=user_id),
    ).scalar() or Decimal("0.00")
    total_despesas += parcelas_pagas

    comprometimento = 0
    if total_receitas > 0:
        comprometimento = round((total_despesas / total_receitas) * 100, 2)

    return {
        "receitas": total_receitas,
        "despesas": total_despesas,
        "balanco": total_receitas - total_despesas,
        "comprometimento": comprometimento,
    }


def get_fluxo_caixa_mensal_consolidado(user_id, ano, mes):
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    movimentacoes_consolidadas = []

    salarios_mes = (
        SalarioMovimento.query.options(
            joinedload(SalarioMovimento.movimento_bancario_salario).joinedload(
                ContaMovimento.conta
            ),
            joinedload(SalarioMovimento.movimento_bancario_beneficio).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            SalarioMovimento.usuario_id == user_id,
            SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
            SalarioMovimento.status.in_([STATUS_RECEBIDO, STATUS_PARCIAL_RECEBIDO]),
        )
        .all()
    )
    for s in salarios_mes:
        if s.movimento_bancario_salario_id:
            conta_info = (
                f"{s.movimento_bancario_salario.conta.nome_banco} ({s.movimento_bancario_salario.conta.tipo})"
                if s.movimento_bancario_salario
                else "N/A"
            )
            movimentacoes_consolidadas.append(
                {
                    "data": s.data_recebimento,
                    "origem": f"Salário (Ref: {s.mes_referencia})",
                    "categoria": "Salário",
                    "valor": s.salario_liquido,
                    "conta": conta_info,
                }
            )
        if s.movimento_bancario_beneficio_id:
            conta_info = (
                f"{s.movimento_bancario_beneficio.conta.nome_banco} ({s.movimento_bancario_beneficio.conta.tipo})"
                if s.movimento_bancario_beneficio
                else "N/A"
            )
            movimentacoes_consolidadas.append(
                {
                    "data": s.data_recebimento,
                    "origem": f"Benefícios (Ref: {s.mes_referencia})",
                    "categoria": "Benefício",
                    "valor": s.total_beneficios,
                    "conta": conta_info,
                }
            )

    outras_receitas = (
        DespRecMovimento.query.options(
            joinedload(DespRecMovimento.despesa_receita),
            joinedload(DespRecMovimento.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == STATUS_RECEBIDO,
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == NATUREZA_RECEITA,
        )
        .all()
    )
    for receita in outras_receitas:
        conta_info = (
            f"{receita.movimento_bancario.conta.nome_banco} ({receita.movimento_bancario.conta.tipo})"
            if receita.movimento_bancario
            else "N/A"
        )
        movimentacoes_consolidadas.append(
            {
                "data": receita.data_pagamento,
                "origem": receita.despesa_receita.nome,
                "categoria": "Receita",
                "valor": receita.valor_realizado,
                "conta": conta_info,
            }
        )

    despesas_gerais = (
        DespRecMovimento.query.options(
            joinedload(DespRecMovimento.despesa_receita),
            joinedload(DespRecMovimento.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.status == STATUS_PAGO,
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRec.natureza == NATUREZA_DESPESA,
        )
        .all()
    )
    for despesa in despesas_gerais:
        conta_info = (
            f"{despesa.movimento_bancario.conta.nome_banco} ({despesa.movimento_bancario.conta.tipo})"
            if despesa.movimento_bancario
            else "N/A"
        )
        movimentacoes_consolidadas.append(
            {
                "data": despesa.data_pagamento,
                "origem": despesa.despesa_receita.nome,
                "categoria": "Despesa",
                "valor": despesa.valor_realizado,
                "conta": conta_info,
            }
        )

    faturas_pagas = (
        CrediarioFatura.query.options(
            joinedload(CrediarioFatura.crediario),
            joinedload(CrediarioFatura.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.status.in_([STATUS_PAGO, STATUS_PARCIAL_PAGO]),
            CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
        )
        .all()
    )
    for fatura in faturas_pagas:
        conta_info = (
            f"{fatura.movimento_bancario.conta.nome_banco} ({fatura.movimento_bancario.conta.tipo})"
            if fatura.movimento_bancario
            else "N/A"
        )
        movimentacoes_consolidadas.append(
            {
                "data": fatura.data_pagamento,
                "origem": f"Fatura: {fatura.crediario.nome_crediario}",
                "categoria": "Crediário",
                "valor": fatura.valor_pago_fatura,
                "conta": conta_info,
            }
        )

    parcelas_pagas_no_mes = (
        FinanciamentoParcela.query.options(
            joinedload(FinanciamentoParcela.financiamento),
            joinedload(FinanciamentoParcela.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            FinanciamentoParcela.status.in_([STATUS_PAGO, STATUS_AMORTIZADO]),
            FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
            FinanciamentoParcela.financiamento.has(usuario_id=user_id),
        )
        .all()
    )

    financiamentos_pagos = {}
    for p in parcelas_pagas_no_mes:
        key = (p.financiamento_id, p.status)
        conta_info = (
            f"{p.movimento_bancario.conta.nome_banco} ({p.movimento_bancario.conta.tipo})"
            if p.movimento_bancario
            else "N/A"
        )
        if key not in financiamentos_pagos:
            tipo = "Amortização" if p.status == STATUS_AMORTIZADO else "Financiamento"
            financiamentos_pagos[key] = {
                "data": p.data_pagamento,
                "origem": f"{tipo}: {p.financiamento.nome_financiamento}",
                "categoria": tipo,
                "valor": Decimal("0.00"),
                "conta": conta_info,
            }
        financiamentos_pagos[key]["valor"] += p.valor_pago

    movimentacoes_consolidadas.extend(financiamentos_pagos.values())
    movimentacoes_consolidadas.sort(key=lambda x: x["data"])

    return movimentacoes_consolidadas


def get_extrato_detalhado_mensal(user_id, ano, mes):
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    movimentacoes = []

    desp_rec = (
        DespRecMovimento.query.options(
            joinedload(DespRecMovimento.despesa_receita),
            joinedload(DespRecMovimento.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            DespRecMovimento.usuario_id == user_id,
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
            DespRecMovimento.status.in_([STATUS_PAGO, STATUS_RECEBIDO]),
        )
        .all()
    )
    for item in desp_rec:
        conta_info = (
            f"{item.movimento_bancario.conta.nome_banco} ({item.movimento_bancario.conta.tipo})"
            if item.movimento_bancario
            else "N/A"
        )
        movimentacoes.append(
            {
                "data": item.data_pagamento,
                "origem": item.despesa_receita.nome,
                "categoria": item.despesa_receita.natureza,
                "valor": item.valor_realizado,
                "conta": conta_info,
            }
        )

    faturas = (
        CrediarioFatura.query.options(
            joinedload(CrediarioFatura.crediario),
            joinedload(CrediarioFatura.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
        )
        .all()
    )
    for fatura in faturas:
        conta_info = (
            f"{fatura.movimento_bancario.conta.nome_banco} ({fatura.movimento_bancario.conta.tipo})"
            if fatura.movimento_bancario
            else "N/A"
        )
        movimentacoes.append(
            {
                "data": fatura.data_pagamento,
                "origem": f"Fatura {fatura.crediario.nome_crediario}",
                "categoria": "Crediário",
                "valor": fatura.valor_pago_fatura,
                "conta": conta_info,
            }
        )

    parcelas = (
        FinanciamentoParcela.query.options(
            joinedload(FinanciamentoParcela.financiamento),
            joinedload(FinanciamentoParcela.movimento_bancario).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            FinanciamentoParcela.financiamento.has(usuario_id=user_id),
            FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
            FinanciamentoParcela.status.in_([STATUS_PAGO, STATUS_AMORTIZADO]),
        )
        .all()
    )
    for parcela in parcelas:
        descricao = f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})"
        tipo = "Amortização" if parcela.status == STATUS_AMORTIZADO else "Financiamento"
        conta_info = (
            f"{parcela.movimento_bancario.conta.nome_banco} ({parcela.movimento_bancario.conta.tipo})"
            if parcela.movimento_bancario
            else "N/A"
        )
        movimentacoes.append(
            {
                "data": parcela.data_pagamento,
                "origem": descricao,
                "categoria": tipo,
                "valor": parcela.valor_pago,
                "conta": conta_info,
            }
        )

    salarios = (
        SalarioMovimento.query.options(
            joinedload(SalarioMovimento.movimento_bancario_salario).joinedload(
                ContaMovimento.conta
            ),
            joinedload(SalarioMovimento.movimento_bancario_beneficio).joinedload(
                ContaMovimento.conta
            ),
        )
        .filter(
            SalarioMovimento.usuario_id == user_id,
            SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        )
        .all()
    )
    for salario in salarios:
        if salario.movimento_bancario_salario_id:
            conta_info = (
                f"{salario.movimento_bancario_salario.conta.nome_banco} ({salario.movimento_bancario_salario.conta.tipo})"
                if salario.movimento_bancario_salario
                else "N/A"
            )
            movimentacoes.append(
                {
                    "data": salario.data_recebimento,
                    "origem": f"Salário (Ref: {salario.mes_referencia})",
                    "categoria": "Salário",
                    "valor": salario.salario_liquido,
                    "conta": conta_info,
                }
            )
        if salario.movimento_bancario_beneficio_id:
            conta_info = (
                f"{salario.movimento_bancario_beneficio.conta.nome_banco} ({salario.movimento_bancario_beneficio.conta.tipo})"
                if salario.movimento_bancario_beneficio
                else "N/A"
            )
            movimentacoes.append(
                {
                    "data": salario.data_recebimento,
                    "origem": f"Benefícios (Ref: {salario.mes_referencia})",
                    "categoria": "Benefício",
                    "valor": salario.total_beneficios,
                    "conta": conta_info,
                }
            )

    movimentacoes.sort(key=lambda x: x["data"])

    return movimentacoes
