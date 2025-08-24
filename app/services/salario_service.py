# app/services/salario_service.py

from flask import current_app
from flask_login import current_user

from app import db
from app.models.salario_item_model import SalarioItem
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento


def criar_folha_pagamento(mes_referencia, data_recebimento):
    """
    Processa a criação de uma nova folha de pagamento, verificando duplicatas.
    Retorna (sucesso, mensagem, objeto_movimento).
    """
    movimento_existente = SalarioMovimento.query.filter_by(
        usuario_id=current_user.id, mes_referencia=mes_referencia
    ).first()

    if movimento_existente:
        msg = f"Já existe uma folha de pagamento para o mês {mes_referencia}."
        return False, msg, movimento_existente

    try:
        novo_movimento = SalarioMovimento(
            usuario_id=current_user.id,
            mes_referencia=mes_referencia,
            data_recebimento=data_recebimento,
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
    """
    Adiciona uma verba a uma folha de pagamento existente.
    Retorna (sucesso, mensagem, dados_do_item).
    """
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
    """
    Exclui uma verba de uma folha de pagamento.
    Retorna (sucesso, mensagem, id_do_item_excluido).
    """
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
    """
    Exclui uma folha de pagamento inteira.
    Retorna (sucesso, mensagem).
    """
    movimento = SalarioMovimento.query.filter_by(
        id=movimento_id, usuario_id=current_user.id
    ).first_or_404()

    if (
        movimento.movimento_bancario_salario_id
        or movimento.movimento_bancario_beneficio_id
    ):
        return (
            False,
            "Não é possível excluir uma folha de pagamento que já foi conciliada com uma movimentação bancária.",
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
    """
    Busca os itens de salário ativos do usuário e formata como choices.
    """
    itens = (
        SalarioItem.query.filter_by(usuario_id=current_user.id, ativo=True)
        .order_by(SalarioItem.tipo, SalarioItem.nome)
        .all()
    )
    choices = [("", "Selecione...")] + [
        (item.id, f"{item.nome} ({item.tipo})") for item in itens
    ]
    return choices
