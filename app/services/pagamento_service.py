# app/services/pagamento_service.py

from decimal import Decimal

from flask import current_app
from flask_login import current_user

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela


def registrar_pagamento(form):
    """
    Processa a lógica de negócio para registrar um pagamento.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        conta_debito = Conta.query.get(form.conta_id.data)
        valor_pago = form.valor_pago.data

        saldo_disponivel = conta_debito.saldo_atual
        if conta_debito.tipo in ["Corrente", "Digital"] and conta_debito.limite:
            saldo_disponivel += conta_debito.limite

        if valor_pago > saldo_disponivel:
            return (
                False,
                f"Saldo insuficiente na conta {conta_debito.nome_banco}. Saldo disponível (com limite): R$ {saldo_disponivel:.2f}",
            )

        tipo_transacao_debito = ContaTransacao.query.filter_by(
            usuario_id=current_user.id, transacao_tipo="PAGAMENTO", tipo="Débito"
        ).first()
        if not tipo_transacao_debito:
            return (
                False,
                'Tipo de transação "PAGAMENTO" (Débito) não encontrado. Por favor, cadastre-o primeiro.',
            )

        novo_movimento = ContaMovimento(
            usuario_id=current_user.id,
            conta_id=conta_debito.id,
            conta_transacao_id=tipo_transacao_debito.id,
            data_movimento=form.data_pagamento.data,
            valor=valor_pago,
            descricao=form.item_descricao.data,
        )
        db.session.add(novo_movimento)
        conta_debito.saldo_atual -= valor_pago
        db.session.flush()

        item_id = form.item_id.data
        item_tipo = form.item_tipo.data

        if item_tipo == "Despesa":
            item = DespRecMovimento.query.get(item_id)
            item.status = "Pago"
            item.valor_realizado = valor_pago
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id
        elif item_tipo == "Financiamento":
            item = FinanciamentoParcela.query.get(item_id)
            item.status = "Paga"
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id
        elif item_tipo == "Crediário":
            item = CrediarioFatura.query.get(item_id)
            item.valor_pago_fatura += valor_pago
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id
            if item.valor_pago_fatura >= item.valor_total_fatura:
                item.status = "Paga"
            else:
                item.status = "Parcialmente Paga"

        db.session.commit()
        return True, "Pagamento registrado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar pagamento: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao registrar o pagamento."


def estornar_pagamento(item_id, item_tipo):
    """
    Processa a lógica de negócio para estornar um pagamento.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        movimento_bancario_id = None
        item_a_atualizar = None

        if item_tipo == "Despesa":
            item_a_atualizar = DespRecMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.status = "Pendente"
                item_a_atualizar.valor_realizado = None
                item_a_atualizar.data_pagamento = None
                item_a_atualizar.movimento_bancario_id = None
        elif item_tipo == "Financiamento":
            item_a_atualizar = FinanciamentoParcela.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.status = "Pendente"
                item_a_atualizar.data_pagamento = None
                item_a_atualizar.movimento_bancario_id = None
        elif item_tipo == "Crediário":
            item_a_atualizar = CrediarioFatura.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.valor_pago_fatura = Decimal("0.00")
                item_a_atualizar.status = "Pendente"
                item_a_atualizar.data_pagamento = None
                item_a_atualizar.movimento_bancario_id = None

        if movimento_bancario_id:
            movimento_bancario = ContaMovimento.query.get(movimento_bancario_id)
            if movimento_bancario:
                conta_bancaria = Conta.query.get(movimento_bancario.conta_id)
                conta_bancaria.saldo_atual += movimento_bancario.valor
                db.session.delete(movimento_bancario)

        db.session.commit()
        return True, "Pagamento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar pagamento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o pagamento."
