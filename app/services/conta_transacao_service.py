# app/services/conta_transacao_service.py

from flask import current_app
from flask_login import current_user

from app import db
from app.models.conta_transacao_model import ContaTransacao


def criar_tipo_transacao(form):
    """
    Processa a criação de um novo tipo de transação.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        novo_tipo_transacao = ContaTransacao(
            usuario_id=current_user.id,
            transacao_tipo=form.transacao_tipo.data.strip().upper(),
            tipo=form.tipo.data,
        )
        db.session.add(novo_tipo_transacao)
        db.session.commit()
        current_app.logger.info(
            f'Tipo de transação "{novo_tipo_transacao.transacao_tipo}" ({novo_tipo_transacao.tipo}) adicionado por {current_user.login}.'
        )
        return True, "Tipo de transação adicionado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar tipo de transação: {e}", exc_info=True)
        return False, "Ocorreu um erro ao criar o tipo de transação."


def atualizar_tipo_transacao(tipo_transacao, form):
    """
    Processa a atualização de um tipo de transação.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        tipo_transacao.transacao_tipo = form.transacao_tipo.data.strip().upper()
        db.session.commit()
        current_app.logger.info(
            f'Tipo de transação "{tipo_transacao.transacao_tipo}" (ID: {tipo_transacao.id}) atualizado por {current_user.login}.'
        )
        return True, "Tipo de transação atualizado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar tipo de transação ID {tipo_transacao.id}: {e}",
            exc_info=True,
        )
        return False, "Ocorreu um erro ao atualizar o tipo de transação."


def excluir_tipo_transacao_por_id(tipo_transacao_id):
    """
    Processa a exclusão de um tipo de transação, validando as regras de negócio.
    Retorna uma tupla (sucesso, mensagem).
    """
    tipo_transacao = ContaTransacao.query.filter_by(
        id=tipo_transacao_id, usuario_id=current_user.id
    ).first_or_404()

    if tipo_transacao.movimentos:
        return (
            False,
            "Não é possível excluir este tipo de transação. Existem movimentações associadas a ele.",
        )

    try:
        nome_transacao = tipo_transacao.transacao_tipo
        db.session.delete(tipo_transacao)
        db.session.commit()
        current_app.logger.info(
            f'Tipo de transação "{nome_transacao}" (ID: {tipo_transacao_id}) excluído por {current_user.login}.'
        )
        return True, "Tipo de transação excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir tipo de transação ID {tipo_transacao_id}: {e}",
            exc_info=True,
        )
        return False, "Ocorreu um erro ao excluir o tipo de transação."


def get_all_transaction_types_for_user_choices():
    """
    Busca todos os tipos de transação de um usuário e formata como choices.
    """
    transacoes = (
        ContaTransacao.query.filter_by(usuario_id=current_user.id)
        .order_by(ContaTransacao.transacao_tipo.asc())
        .all()
    )
    choices = [("", "Selecione...")] + [
        (ct.id, f"{ct.transacao_tipo} ({ct.tipo})") for ct in transacoes
    ]
    return choices


def get_debit_transaction_types_for_user_choices():
    """
    Busca os tipos de transação de débito de um usuário e formata como choices.
    """
    transacoes_debito = (
        ContaTransacao.query.filter_by(usuario_id=current_user.id, tipo="Débito")
        .order_by(ContaTransacao.transacao_tipo.asc())
        .all()
    )
    choices = [("", "Selecione...")] + [
        (ct.id, f"{ct.transacao_tipo}") for ct in transacoes_debito
    ]
    return choices
