# app/services/recebimento_service.py

from datetime import date, timedelta

from flask import current_app
from flask_login import current_user

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.salario_movimento_model import SalarioMovimento
from app.services import conta_service
from app.utils import (
    NATUREZA_RECEITA,
    STATUS_PARCIAL_RECEBIDO,
    STATUS_PENDENTE,
    STATUS_RECEBIDO,
)


def registrar_recebimento(form):
    """
    Processa a lógica de negócio para registrar um recebimento.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        conta_credito = Conta.query.get(form.conta_id.data)
        valor_recebido = form.valor_recebido.data
        item_id = form.item_id.data
        item_tipo = form.item_tipo.data

        tipo_transacao_credito = ContaTransacao.query.filter_by(
            usuario_id=current_user.id,
            transacao_tipo="RECEBIMENTO",
            tipo="Crédito",
        ).first()
        if not tipo_transacao_credito:
            return (
                False,
                'Tipo de transação "RECEBIMENTO" (Crédito) não encontrado. Por favor, cadastre-o primeiro.',
            )

        novo_movimento = ContaMovimento(
            usuario_id=current_user.id,
            conta_id=conta_credito.id,
            conta_transacao_id=tipo_transacao_credito.id,
            data_movimento=form.data_recebimento.data,
            valor=valor_recebido,
            descricao=form.item_descricao.data,
        )
        db.session.add(novo_movimento)
        conta_credito.saldo_atual += valor_recebido
        db.session.flush()

        if item_tipo == NATUREZA_RECEITA:
            item = DespRecMovimento.query.get(item_id)
            item.status = STATUS_RECEBIDO
            item.valor_realizado = valor_recebido
            item.data_pagamento = form.data_recebimento.data
            item.movimento_bancario_id = novo_movimento.id
        elif item_tipo in ["Salário", "Benefício"]:
            item = SalarioMovimento.query.get(item_id)

            has_beneficios = any(i.salario_item.tipo == "Benefício" for i in item.itens)

            if item_tipo == "Salário":
                item.movimento_bancario_salario_id = novo_movimento.id
            else:
                item.movimento_bancario_beneficio_id = novo_movimento.id

            if item.movimento_bancario_salario_id and (
                not has_beneficios or item.movimento_bancario_beneficio_id
            ):
                item.status = STATUS_RECEBIDO
            else:
                item.status = STATUS_PARCIAL_RECEBIDO

        db.session.commit()
        return True, "Recebimento registrado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao registrar o recebimento."


def estornar_recebimento(item_id, item_tipo):
    """
    Processa a lógica de negócio para estornar um recebimento,
    validando o impacto no saldo atual.
    """
    try:
        movimento_bancario_id = None
        item_a_atualizar = None

        if item_tipo == "Receita":
            item_a_atualizar = DespRecMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
        elif item_tipo in ["Salário", "Benefício"]:
            item_a_atualizar = SalarioMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = (
                    item_a_atualizar.movimento_bancario_salario_id
                    if item_tipo == "Salário"
                    else item_a_atualizar.movimento_bancario_beneficio_id
                )

        if not movimento_bancario_id:
            return False, "Movimentação bancária associada não encontrada para estorno."

        movimento_a_estornar = ContaMovimento.query.get(movimento_bancario_id)
        if not movimento_a_estornar:
            return False, "Movimentação bancária para estorno não existe mais."

        valor_a_debitar = movimento_a_estornar.valor
        conta_bancaria = movimento_a_estornar.conta

        is_safe, message = conta_service.validar_estorno_saldo(
            conta_bancaria, valor_a_debitar
        )
        if not is_safe:
            return False, message

        if item_tipo == "Receita":
            item_a_atualizar.status = STATUS_PENDENTE
            item_a_atualizar.valor_realizado = None
            item_a_atualizar.data_pagamento = None
            item_a_atualizar.movimento_bancario_id = None
        elif item_tipo in ["Salário", "Benefício"]:
            if item_tipo == "Salário":
                item_a_atualizar.movimento_bancario_salario_id = None
            else:
                item_a_atualizar.movimento_bancario_beneficio_id = None

            if (
                item_a_atualizar.movimento_bancario_salario_id
                or item_a_atualizar.movimento_bancario_beneficio_id
            ):
                item_a_atualizar.status = STATUS_PARCIAL_RECEBIDO
            else:
                item_a_atualizar.status = STATUS_PENDENTE

        conta_bancaria.saldo_atual -= valor_a_debitar
        db.session.delete(movimento_a_estornar)

        db.session.commit()
        return True, "Recebimento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o recebimento."
