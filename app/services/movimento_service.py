# app/services/movimento_service.py

from decimal import Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import or_

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento
from app.utils import (
    TIPO_DEBITO,
    TIPO_MOVIMENTACAO_SIMPLES,
    TIPO_MOVIMENTACAO_TRANSFERENCIA,
)


def registrar_movimento(form):
    try:
        tipo_operacao = form.tipo_operacao.data
        conta_origem_id = form.conta_id.data
        data_movimento = form.data_movimento.data
        valor = form.valor.data
        descricao_manual = form.descricao.data.strip() if form.descricao.data else None

        conta_origem = db.session.get(Conta, conta_origem_id)

        if valor <= 0:
            return False, "O valor da movimentação deve ser maior que zero."

        is_debit_operation = False
        transacao_id_para_descricao = None

        if tipo_operacao == TIPO_MOVIMENTACAO_SIMPLES:
            tipo_transacao_obj = db.session.get(
                ContaTransacao, form.conta_transacao_id.data
            )
            if tipo_transacao_obj and tipo_transacao_obj.tipo == TIPO_DEBITO:
                is_debit_operation = True
            transacao_id_para_descricao = form.conta_transacao_id.data
        elif tipo_operacao == TIPO_MOVIMENTACAO_TRANSFERENCIA:
            is_debit_operation = True
            transacao_id_para_descricao = form.transferencia_tipo_id.data

        if is_debit_operation:
            saldo_disponivel = conta_origem.saldo_atual
            if conta_origem.tipo in ["Corrente", "Digital"] and conta_origem.limite:
                saldo_disponivel += conta_origem.limite
            if valor > saldo_disponivel:
                return (
                    False,
                    f"Saldo e limite insuficientes na conta {conta_origem.nome_banco}. Saldo disponível:  {saldo_disponivel:.2f}",
                )

        descricao_final = descricao_manual
        if not descricao_final and transacao_id_para_descricao:
            tipo_transacao_fallback = db.session.get(
                ContaTransacao, transacao_id_para_descricao
            )
            if tipo_transacao_fallback:
                descricao_final = tipo_transacao_fallback.transacao_tipo

        if tipo_operacao == TIPO_MOVIMENTACAO_SIMPLES:
            tipo_transacao = db.session.get(
                ContaTransacao, form.conta_transacao_id.data
            )
            if not tipo_transacao:
                return False, "Tipo de transação inválido ou não encontrado."

            movimento = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_origem_id,
                conta_transacao_id=form.conta_transacao_id.data,
                data_movimento=data_movimento,
                valor=valor,
                descricao=descricao_final,
            )
            db.session.add(movimento)
            if tipo_transacao.tipo == TIPO_DEBITO:
                conta_origem.saldo_atual -= valor
            else:
                conta_origem.saldo_atual += valor

        elif tipo_operacao == TIPO_MOVIMENTACAO_TRANSFERENCIA:
            conta_destino = db.session.get(Conta, form.conta_destino_id.data)
            tipo_transacao_debito = db.session.get(
                ContaTransacao, form.transferencia_tipo_id.data
            )
            if not tipo_transacao_debito:
                return (
                    False,
                    "Tipo de transferência (débito) inválido ou não encontrado.",
                )

            tipo_transacao_credito = ContaTransacao.query.filter_by(
                usuario_id=current_user.id,
                transacao_tipo=tipo_transacao_debito.transacao_tipo,
                tipo="Crédito",
            ).first()

            if not tipo_transacao_credito:
                return (
                    False,
                    f'Tipo de transação de Crédito correspondente a "{tipo_transacao_debito.transacao_tipo}" não encontrado.',
                )

            descricao_base_origem = f"{tipo_transacao_debito.transacao_tipo} para {conta_destino.nome_banco} ({conta_destino.agencia}-{conta_destino.conta})"
            descricao_base_destino = f"{tipo_transacao_debito.transacao_tipo} de {conta_origem.nome_banco} ({conta_origem.agencia}-{conta_origem.conta})"

            desc_origem = (
                f"{descricao_base_origem}" if descricao_final else descricao_base_origem
            )
            desc_destino = (
                f"{descricao_base_destino}"
                if descricao_final
                else descricao_base_destino
            )

            movimento_origem = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_origem_id,
                conta_transacao_id=tipo_transacao_debito.id,
                data_movimento=data_movimento,
                valor=valor,
                descricao=desc_origem,
            )
            db.session.add(movimento_origem)
            conta_origem.saldo_atual -= valor
            db.session.flush()

            movimento_destino = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_destino.id,
                conta_transacao_id=tipo_transacao_credito.id,
                data_movimento=data_movimento,
                valor=valor,
                descricao=desc_destino,
            )
            db.session.add(movimento_destino)
            conta_destino.saldo_atual += valor
            db.session.flush()

            movimento_origem.id_movimento_relacionado = movimento_destino.id
            movimento_destino.id_movimento_relacionado = movimento_origem.id

        db.session.commit()
        current_app.logger.info(
            f"Movimentação registrada com sucesso por {current_user.login}."
        )
        return True, "Movimentação registrada com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar movimento: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao registrar a movimentação."


def excluir_movimento(movimento_id):
    movimento = ContaMovimento.query.filter_by(
        id=movimento_id, usuario_id=current_user.id
    ).first_or_404()

    is_linked = (
        DespRecMovimento.query.filter_by(movimento_bancario_id=movimento_id).first()
        or FinanciamentoParcela.query.filter_by(
            movimento_bancario_id=movimento_id
        ).first()
        or SalarioMovimento.query.filter(
            or_(
                SalarioMovimento.movimento_bancario_salario_id == movimento_id,
                SalarioMovimento.movimento_bancario_beneficio_id == movimento_id,
            )
        ).first()
    )
    if is_linked:
        return (
            False,
            "Esta movimentação não pode ser excluída, pois está vinculada a um pagamento ou recebimento. Realize o estorno pela origem.",
        )

    movimentos_posteriores = ContaMovimento.query.filter(
        ContaMovimento.usuario_id == current_user.id,
        ContaMovimento.conta_id == movimento.conta_id,
        or_(
            ContaMovimento.data_movimento > movimento.data_movimento,
            db.and_(
                ContaMovimento.data_movimento == movimento.data_movimento,
                ContaMovimento.id > movimento.id,
            ),
        ),
    ).count()

    if movimentos_posteriores > 0:
        return (
            False,
            "Não é possível excluir esta movimentação, pois existem lançamentos posteriores na mesma conta. Exclua da mais recente para a mais antiga.",
        )

    try:
        movimento_relacionado = None
        if movimento.id_movimento_relacionado:
            movimento_relacionado = db.session.get(
                ContaMovimento, movimento.id_movimento_relacionado
            )

        if movimento_relacionado:
            movimento.id_movimento_relacionado = None
            movimento_relacionado.id_movimento_relacionado = None
            db.session.flush()

        conta_afetada = db.session.get(Conta, movimento.conta_id)
        if conta_afetada:
            if movimento.tipo_transacao.tipo == "Débito":
                conta_afetada.saldo_atual += movimento.valor
            else:
                conta_afetada.saldo_atual -= movimento.valor

        if movimento_relacionado:
            conta_destino = db.session.get(Conta, movimento_relacionado.conta_id)
            if conta_destino:
                if movimento_relacionado.tipo_transacao.tipo == "Débito":
                    conta_destino.saldo_atual += movimento_relacionado.valor
                else:
                    conta_destino.saldo_atual -= movimento_relacionado.valor
            db.session.delete(movimento_relacionado)

        db.session.delete(movimento)

        db.session.commit()
        current_app.logger.info(
            f"Movimentação {movimento.id} excluída por {current_user.login}."
        )
        return True, "Movimentação excluída com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir movimentação ID {movimento_id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro inesperado ao excluir a movimentação."
