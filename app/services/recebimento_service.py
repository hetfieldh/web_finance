# app/services/recebimento_service.py

from flask import current_app
from flask_login import current_user

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.salario_movimento_model import SalarioMovimento


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

        if item_tipo == "Receita":
            item = DespRecMovimento.query.get(item_id)
            item.status = "Pago"
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
                item.status = "Recebido"
            else:
                item.status = "Parcialmente Recebido"

        db.session.commit()
        return True, "Recebimento registrado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao registrar o recebimento."


def estornar_recebimento(item_id, item_tipo):
    """
    Processa a lógica de negócio para estornar um recebimento.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        movimento_bancario_id = None
        item_a_atualizar = None

        if item_tipo == "Receita":
            item_a_atualizar = DespRecMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.status = "Pendente"
                item_a_atualizar.valor_realizado = None
                item_a_atualizar.data_pagamento = None
                item_a_atualizar.movimento_bancario_id = None
        elif item_tipo in ["Salário", "Benefício"]:
            item_a_atualizar = SalarioMovimento.query.get(item_id)
            if item_a_atualizar:
                if item_tipo == "Salário":
                    movimento_bancario_id = (
                        item_a_atualizar.movimento_bancario_salario_id
                    )
                    item_a_atualizar.movimento_bancario_salario_id = None
                else:
                    movimento_bancario_id = (
                        item_a_atualizar.movimento_bancario_beneficio_id
                    )
                    item_a_atualizar.movimento_bancario_beneficio_id = None

                if (
                    item_a_atualizar.movimento_bancario_salario_id
                    or item_a_atualizar.movimento_bancario_beneficio_id
                ):
                    item_a_atualizar.status = "Parcialmente Recebido"
                else:
                    item_a_atualizar.status = "Pendente"

        if movimento_bancario_id:
            movimento_bancario = ContaMovimento.query.get(movimento_bancario_id)
            if movimento_bancario:
                conta_bancaria = Conta.query.get(movimento_bancario.conta_id)
                conta_bancaria.saldo_atual -= movimento_bancario.valor
                db.session.delete(movimento_bancario)

        db.session.commit()
        return True, "Recebimento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o recebimento."
