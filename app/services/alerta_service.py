# app\services\alerta_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask_login import current_user
from sqlalchemy import and_, func, or_

from app import db
from app.models.conta_model import Conta
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento
from app.utils import (
    NATUREZA_DESPESA,
    NATUREZA_RECEITA,
    STATUS_ATRASADO,
    STATUS_PARCIAL_PAGO,
    STATUS_PARCIAL_RECEBIDO,
    STATUS_PENDENTE,
)

STATUS_NAO_PAGO = [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]
STATUS_NAO_RECEBIDO = [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_RECEBIDO]
TWO_PLACES = Decimal("0.01")


def _formatar_item_despesa(item):
    return {
        "data": item.data_vencimento,
        "descricao": item.despesa_receita.nome,
        "valor": item.valor_previsto - (item.valor_realizado or 0),
        "natureza": NATUREZA_DESPESA,
        "id_original": item.id,
        "tipo_item": "Despesa",
        "valor_para_modal": item.valor_previsto,
    }


def _formatar_item_financiamento(item):
    return {
        "data": item.data_vencimento,
        "descricao": f"{item.financiamento.nome_financiamento} ({item.numero_parcela}/{item.financiamento.prazo_meses})",
        "valor": item.valor_total_previsto - (item.valor_pago or 0),
        "natureza": NATUREZA_DESPESA,
        "id_original": item.id,
        "tipo_item": "Financiamento",
        "valor_para_modal": item.valor_total_previsto,
    }


def _formatar_item_crediario(item):
    soma_parcelas_query = (
        db.session.query(func.sum(CrediarioParcela.valor_parcela))
        .join(
            CrediarioMovimento,
            CrediarioMovimento.id == CrediarioParcela.crediario_movimento_id,
        )
        .filter(
            CrediarioMovimento.crediario_id == item.crediario_id,
            func.date_format(CrediarioParcela.data_vencimento, "%Y-%m")
            == item.mes_referencia,
        )
        .scalar()
    )
    soma_parcelas = soma_parcelas_query or Decimal("0.00")

    valor_fatura_rounded = (item.valor_total_fatura or Decimal("0.00")).quantize(
        TWO_PLACES
    )
    soma_parcelas_rounded = soma_parcelas.quantize(TWO_PLACES)
    desatualizada = valor_fatura_rounded != soma_parcelas_rounded

    valor_pendente = item.valor_total_fatura - (item.valor_pago_fatura or 0)
    return {
        "data": item.data_vencimento_fatura,
        "descricao": f"FATURA {item.crediario.nome_crediario}",
        "valor": valor_pendente,
        "natureza": NATUREZA_DESPESA,
        "id_original": item.id,
        "tipo_item": "Crediário",
        "valor_para_modal": valor_pendente,
        "desatualizada": desatualizada,
    }


def _formatar_item_receita(item):
    return {
        "data": item.data_vencimento,
        "descricao": item.despesa_receita.nome,
        "valor": item.valor_previsto - (item.valor_realizado or 0),
        "natureza": NATUREZA_RECEITA,
        "id_original": item.id,
        "tipo_item": "Receita",
        "valor_para_modal": item.valor_previsto,
        "conta_sugerida_id": None,
        "folha_tem_fgts": False,
    }


def _formatar_item_salario(item):
    folha_tem_fgts = any(
        it.salario_item.tipo == "FGTS" and it.valor > 0 for it in item.itens
    )
    return {
        "data": item.data_recebimento,
        "descricao": f"SALÁRIO REF. {item.mes_referencia}",
        "valor": item.salario_liquido,
        "natureza": NATUREZA_RECEITA,
        "id_original": item.id,
        "tipo_item": "Salário Líquido",
        "valor_para_modal": item.salario_liquido,
        "conta_sugerida_id": None,
        "folha_tem_fgts": folha_tem_fgts,
    }


def get_contas_vencidas():
    hoje = date.today()
    movimentos = []

    despesas = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento < hoje,
            DespRecMovimento.despesa_receita.has(natureza=NATUREZA_DESPESA),
            DespRecMovimento.status.in_(STATUS_NAO_PAGO),
        )
        .all()
    )
    movimentos.extend([_formatar_item_despesa(d) for d in despesas])

    parcelas = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.data_vencimento < hoje,
            FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            FinanciamentoParcela.status.in_(STATUS_NAO_PAGO),
        )
        .all()
    )
    movimentos.extend([_formatar_item_financiamento(p) for p in parcelas])

    faturas = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == current_user.id,
        CrediarioFatura.data_vencimento_fatura < hoje,
        CrediarioFatura.status.in_(STATUS_NAO_PAGO),
    ).all()
    movimentos.extend([_formatar_item_crediario(f) for f in faturas])

    receitas = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento < hoje,
            DespRecMovimento.despesa_receita.has(natureza=NATUREZA_RECEITA),
            DespRecMovimento.status.in_(STATUS_NAO_RECEBIDO),
        )
        .all()
    )
    movimentos.extend([_formatar_item_receita(r) for r in receitas])

    salarios_query = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.data_recebimento < hoje,
        SalarioMovimento.status.in_(STATUS_NAO_RECEBIDO),
    ).all()
    salarios_filtrados = [s for s in salarios_query if s.salario_liquido > 0]
    movimentos.extend([_formatar_item_salario(s) for s in salarios_filtrados])

    movimentos.sort(key=lambda x: x["data"])
    return movimentos


def get_contas_a_vencer(dias=7):
    hoje = date.today()
    data_limite = hoje + timedelta(days=dias)
    movimentos = []

    despesas = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento.between(hoje, data_limite),
            DespRecMovimento.despesa_receita.has(natureza=NATUREZA_DESPESA),
            DespRecMovimento.status.in_(STATUS_NAO_PAGO),
        )
        .all()
    )
    movimentos.extend([_formatar_item_despesa(d) for d in despesas])

    parcelas = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.data_vencimento.between(hoje, data_limite),
            FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            FinanciamentoParcela.status.in_(STATUS_NAO_PAGO),
        )
        .all()
    )
    movimentos.extend([_formatar_item_financiamento(p) for p in parcelas])

    faturas = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == current_user.id,
        CrediarioFatura.data_vencimento_fatura.between(hoje, data_limite),
        CrediarioFatura.status.in_(STATUS_NAO_PAGO),
    ).all()
    movimentos.extend([_formatar_item_crediario(f) for f in faturas])

    receitas = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento.between(hoje, data_limite),
            DespRecMovimento.despesa_receita.has(natureza=NATUREZA_RECEITA),
            DespRecMovimento.status.in_(STATUS_NAO_RECEBIDO),
        )
        .all()
    )
    movimentos.extend([_formatar_item_receita(r) for r in receitas])

    salarios_query = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.data_recebimento.between(hoje, data_limite),
        SalarioMovimento.status.in_(STATUS_NAO_RECEBIDO),
    ).all()
    salarios_filtrados = [s for s in salarios_query if s.salario_liquido > 0]
    movimentos.extend([_formatar_item_salario(s) for s in salarios_filtrados])

    movimentos.sort(key=lambda x: x["data"])
    return movimentos
