# app/services/salario_service.py

from datetime import date

from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_login import current_user

from app import db
from app.models.salario_item_model import SalarioItem
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.utils import FormChoices


def get_quinto_dia_util(ano, mes):
    data_base = date(ano, mes, 1) + relativedelta(months=1)
    dia = 1
    dias_uteis = 0

    while dias_uteis < 5:
        data_atual = date(data_base.year, data_base.month, dia)
        if data_atual.weekday() < 5:
            dias_uteis += 1

        if dias_uteis < 5:
            dia += 1

    return date(data_base.year, data_base.month, dia)


def criar_folha_pagamento(mes_referencia, tipo_folha, data_recebimento_form):
    movimento_existente = SalarioMovimento.query.filter_by(
        usuario_id=current_user.id, mes_referencia=mes_referencia, tipo=tipo_folha
    ).first()

    if movimento_existente:
        msg = f"Já existe uma folha do tipo '{tipo_folha}' para o mês {mes_referencia}."
        return False, msg, movimento_existente

    try:
        data_final = data_recebimento_form

        if tipo_folha == FormChoices.TipoFolha.MENSAL.value:
            ano, mes = map(int, mes_referencia.split("-"))
            data_final = get_quinto_dia_util(ano, mes)

        novo_movimento = SalarioMovimento(
            usuario_id=current_user.id,
            mes_referencia=mes_referencia,
            tipo=tipo_folha,
            data_recebimento=data_final,
        )
        db.session.add(novo_movimento)
        db.session.commit()
        return (
            True,
            "Folha de pagamento criada. Agora adicione as verbas.",
            novo_movimento,
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar SalarioMovimento: {e}", exc_info=True)
        return False, "Erro ao criar a folha de pagamento.", None


def adicionar_item_folha(movimento_id, form):
    movimento = db.session.get(SalarioMovimento, movimento_id)
    if not movimento or movimento.usuario_id != current_user.id:
        return False, "Folha de pagamento não encontrada.", None

    if (
        movimento.movimento_bancario_salario_id
        or movimento.movimento_bancario_beneficio_id
    ):
        return (
            False,
            "Não é possível adicionar verbas a uma folha de pagamento já recebida.",
            None,
        )

    try:
        novo_item = SalarioMovimentoItem(
            salario_movimento_id=movimento.id,
            salario_item_id=form.salario_item_id.data,
            valor=form.valor.data,
        )
        db.session.add(novo_item)
        db.session.commit()
        item_data = {
            "id": novo_item.id,
            "nome": novo_item.salario_item.nome,
            "tipo": novo_item.salario_item.tipo,
            "valor": float(novo_item.valor),
        }
        return True, "Verba adicionada com sucesso!", item_data
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao adicionar SalarioMovimentoItem: {e}", exc_info=True
        )
        return False, "Erro ao adicionar verba.", None


def excluir_item_folha(item_id):
    item = db.session.get(SalarioMovimentoItem, item_id)
    if not item or item.movimento_pai.usuario_id != current_user.id:
        return False, "Item não encontrado.", None

    movimento = item.movimento_pai
    if (
        movimento.movimento_bancario_salario_id
        or movimento.movimento_bancario_beneficio_id
    ):
        return (
            False,
            "Não é possível remover verbas de uma folha de pagamento já recebida.",
            None,
        )

    try:
        db.session.delete(item)
        db.session.commit()
        return True, "Verba removida com sucesso!", item_id
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir SalarioMovimentoItem ID {item_id}: {e}", exc_info=True
        )
        return False, "Erro ao remover verba.", None


def excluir_folha_pagamento(movimento_id):
    movimento = SalarioMovimento.query.filter_by(
        id=movimento_id, usuario_id=current_user.id
    ).first_or_404()

    salario_pago = movimento.movimento_bancario_salario_id is not None

    algum_beneficio_pago = any(
        item.movimento_bancario_id is not None
        for item in movimento.itens
        if item.salario_item.tipo == "Benefício"
    )

    if salario_pago or algum_beneficio_pago:
        return (
            False,
            "Não é possível excluir uma folha com itens já recebidos. Estorne todos os recebimentos primeiro.",
        )

    try:
        db.session.delete(movimento)
        db.session.commit()
        current_app.logger.info(
            f"Folha de pagamento ID {movimento_id} excluída por {current_user.login}."
        )
        return True, "Folha de pagamento excluída com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir folha de pagamento ID {movimento_id}: {e}", exc_info=True
        )
        return False, "Erro ao excluir a folha de pagamento."


def get_active_salario_items_for_user_choices():
    itens = (
        SalarioItem.query.filter_by(usuario_id=current_user.id, ativo=True)
        .order_by(SalarioItem.tipo, SalarioItem.nome)
        .all()
    )
    choices = [("", "Selecione...")] + [
        (item.id, f"{item.nome} ({item.tipo})") for item in itens
    ]
    return choices


def has_fgts_salario_item():
    return (
        SalarioItem.query.filter_by(
            usuario_id=current_user.id, tipo="FGTS", ativo=True
        ).first()
        is not None
    )


def verificar_regras_recebimento(movimento_id):
    movimento = SalarioMovimento.query.get(movimento_id)
    if not movimento:
        return False, "Movimento não encontrado."

    tem_fgts = any(
        item.salario_item.tipo == FormChoices.TipoSalarioItem.FGTS.value
        and item.valor > 0
        for item in movimento.itens
    )

    if movimento.tipo == FormChoices.TipoFolha.MENSAL.value:
        if not tem_fgts:
            return (
                False,
                "Recebimento bloqueado: A folha 'Mensal' deve possuir um item de FGTS com valor.",
            )

    else:
        if not tem_fgts:
            return (
                True,
                "ATENÇÃO: Esta folha não possui FGTS. Caso seja necessário, estorne o pagamento e ajuste.",
            )

    return True, None
