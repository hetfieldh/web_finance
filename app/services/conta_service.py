# app/services/conta_service.py

from decimal import Decimal

from flask import current_app
from flask_login import current_user

from app import db
from app.models.conta_model import Conta


def criar_conta(form):
    """
    Processa a lógica de negócio para criar uma nova conta bancária.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        nome_banco = form.nome_banco.data.strip().upper()
        agencia = form.agencia.data.strip()
        conta_num = form.conta.data.strip()
        tipo = form.tipo.data

        existing_account = Conta.query.filter_by(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
        ).first()

        if existing_account:
            return (
                False,
                "Você já possui uma conta com este banco, agência, número e tipo.",
            )

        nova_conta = Conta(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
            saldo_inicial=form.saldo_inicial.data,
            saldo_atual=form.saldo_inicial.data,
            limite=form.limite.data,
            ativa=form.ativa.data,
        )
        db.session.add(nova_conta)
        db.session.commit()

        current_app.logger.info(
            f"Conta {nome_banco}-{conta_num} adicionada por {current_user.login}."
        )
        return True, "Conta bancária adicionada com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar conta: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao criar a conta."


def atualizar_conta(conta, form):
    """
    Processa a lógica de negócio para atualizar uma conta bancária.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        if not form.ativa.data and Decimal(str(conta.saldo_atual)) != Decimal("0.00"):
            return (
                False,
                "Não é possível inativar a conta. O saldo atual deve ser zero.",
            )

        conta.limite = form.limite.data
        conta.ativa = form.ativa.data
        db.session.commit()

        current_app.logger.info(
            f"Conta {conta.nome_banco}-{conta.conta} (ID: {conta.id}) atualizada por {current_user.login}."
        )
        return True, "Conta bancária atualizada com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar conta ID {conta.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro inesperado ao atualizar a conta."


def excluir_conta_por_id(conta_id):
    """
    Processa a lógica de negócio para excluir uma conta bancária.
    Retorna uma tupla (sucesso, mensagem).
    """
    conta = Conta.query.filter_by(
        id=conta_id, usuario_id=current_user.id
    ).first_or_404()

    if conta.movimentos:
        return (
            False,
            "Não é possível excluir a conta. Existem movimentações associadas a ela.",
        )

    if Decimal(str(conta.saldo_atual)) != Decimal("0.00"):
        return False, "Não é possível excluir a conta. O saldo atual deve ser zero."

    try:
        db.session.delete(conta)
        db.session.commit()
        current_app.logger.info(
            f"Conta {conta.nome_banco}-{conta.conta} (ID: {conta.id}) excluída por {current_user.login}."
        )
        return True, "Conta bancária excluída com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir conta ID {conta.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro inesperado ao excluir a conta."
