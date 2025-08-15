# app/services/movimento_service.py (Completo e Corrigido)

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


def registrar_movimento(form):
    """
    Processa a lógica de negócio para registrar uma movimentação bancária.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        tipo_operacao = form.tipo_operacao.data
        conta_origem_id = form.conta_id.data
        data_movimento = form.data_movimento.data
        valor = form.valor.data
        descricao_manual = form.descricao.data.strip() if form.descricao.data else None

        conta_origem = db.session.get(Conta, conta_origem_id)

        if valor <= 0:
            return False, "O valor da movimentação deve ser maior que zero."

        # Validação de Saldo
        is_debit_operation = False
        if tipo_operacao == "simples":
            tipo_transacao = db.session.get(
                ContaTransacao, form.conta_transacao_id.data
            )
            if tipo_transacao and tipo_transacao.tipo == "Débito":
                is_debit_operation = True
        elif tipo_operacao == "transferencia":
            is_debit_operation = True

        if is_debit_operation:
            saldo_disponivel = conta_origem.saldo_atual
            if conta_origem.tipo in ["Corrente", "Digital"] and conta_origem.limite:
                saldo_disponivel += conta_origem.limite
            if valor > saldo_disponivel:
                return (
                    False,
                    f"Saldo e limite insuficientes na conta {conta_origem.nome_banco}. Saldo disponível: R$ {saldo_disponivel:.2f}",
                )

        # Lógica de Criação dos Registros
        if tipo_operacao == "simples":
            tipo_transacao = db.session.get(
                ContaTransacao, form.conta_transacao_id.data
            )
            movimento = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_origem_id,
                conta_transacao_id=form.conta_transacao_id.data,
                data_movimento=data_movimento,
                valor=valor,
                descricao=descricao_manual,
            )
            db.session.add(movimento)
            if tipo_transacao.tipo == "Débito":
                conta_origem.saldo_atual -= valor
            else:
                conta_origem.saldo_atual += valor

        elif tipo_operacao == "transferencia":
            conta_destino = db.session.get(Conta, form.conta_destino_id.data)
            tipo_transacao_debito = db.session.get(
                ContaTransacao, form.transferencia_tipo_id.data
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

            nome_origem = f"{conta_origem.nome_banco} - {conta_origem.conta}"
            nome_destino = f"{conta_destino.nome_banco} - {conta_destino.conta}"
            desc_origem = f"{tipo_transacao_debito.transacao_tipo} para {nome_destino}"
            desc_destino = f"{tipo_transacao_debito.transacao_tipo} de {nome_origem}"
            if descricao_manual:
                desc_origem += f" ({descricao_manual})"
                desc_destino += f" ({descricao_manual})"

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
        return True, "Movimentação registrada com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar movimento: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao registrar a movimentação."


def excluir_movimento(movimento_id):
    """
    Processa a lógica de negócio para excluir uma movimentação bancária.
    Retorna uma tupla (sucesso, mensagem).
    """
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

        # Quebrar a dependência circular ANTES de qualquer outra coisa
        if movimento_relacionado:
            movimento.id_movimento_relacionado = None
            movimento_relacionado.id_movimento_relacionado = None
            db.session.flush()

        # Reverter o saldo da conta principal
        conta_afetada = db.session.get(Conta, movimento.conta_id)
        if conta_afetada:
            if movimento.tipo_transacao.tipo == "Débito":
                conta_afetada.saldo_atual += movimento.valor
            else:
                conta_afetada.saldo_atual -= movimento.valor

        # Se houver movimento relacionado, reverter o saldo da outra conta e deletá-lo
        if movimento_relacionado:
            conta_destino = db.session.get(Conta, movimento_relacionado.conta_id)
            if conta_destino:
                if movimento_relacionado.tipo_transacao.tipo == "Débito":
                    conta_destino.saldo_atual += movimento_relacionado.valor
                else:
                    conta_destino.saldo_atual -= movimento_relacionado.valor
            db.session.delete(movimento_relacionado)

        # Deletar o movimento principal
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
