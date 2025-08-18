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


def _simular_impacto_estorno(movimento_a_estornar):
    """
    Simula o impacto de um estorno no saldo da conta para evitar saldos negativos.
    Retorna True se o estorno for seguro, False caso contrário.
    """
    conta = movimento_a_estornar.conta
    valor_estorno = movimento_a_estornar.valor
    data_estorno = movimento_a_estornar.data_movimento

    # Calcula o saldo da conta no momento EXATO antes do movimento que será estornado
    saldo_no_momento = conta.saldo_inicial
    movimentos_anteriores = (
        ContaMovimento.query.filter(
            ContaMovimento.conta_id == conta.id,
            ContaMovimento.data_movimento < data_estorno,
        )
        .order_by(ContaMovimento.data_movimento, ContaMovimento.id)
        .all()
    )

    for mov in movimentos_anteriores:
        if mov.tipo_transacao.tipo == "Crédito":
            saldo_no_momento += mov.valor
        else:
            saldo_no_momento -= mov.valor

    # Agora, simula o futuro a partir desse ponto, mas sem o valor do estorno
    saldo_simulado = saldo_no_momento
    movimentos_posteriores = (
        ContaMovimento.query.filter(
            ContaMovimento.conta_id == conta.id,
            ContaMovimento.data_movimento >= data_estorno,
            ContaMovimento.id != movimento_a_estornar.id,
        )
        .order_by(ContaMovimento.data_movimento, ContaMovimento.id)
        .all()
    )

    limite_seguro = (
        -conta.limite if conta.limite and conta.tipo in ["Corrente", "Digital"] else 0
    )

    for mov in movimentos_posteriores:
        if mov.tipo_transacao.tipo == "Crédito":
            saldo_simulado += mov.valor
        else:
            saldo_simulado -= mov.valor

        # Se em qualquer ponto a simulação resultar em saldo insuficiente, o estorno é inseguro
        if saldo_simulado < limite_seguro:
            return False

    return True


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
            item.status = "Recebido"
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
    Processa a lógica de negócio para estornar um recebimento,
    validando o impacto no saldo futuro.
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

        if not _simular_impacto_estorno(movimento_a_estornar):
            return (
                False,
                f"Estorno não permitido. Esta ação resultaria em saldo insuficiente na conta '{movimento_a_estornar.conta.nome_banco}' em transações futuras.",
            )

        # Se a simulação passou, prossiga com o estorno
        if item_tipo == "Receita":
            item_a_atualizar.status = "Pendente"
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
                item_a_atualizar.status = "Parcialmente Recebido"
            else:
                item_a_atualizar.status = "Pendente"

        conta_bancaria = Conta.query.get(movimento_a_estornar.conta_id)
        conta_bancaria.saldo_atual -= movimento_a_estornar.valor
        db.session.delete(movimento_a_estornar)

        db.session.commit()
        return True, "Recebimento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o recebimento."
