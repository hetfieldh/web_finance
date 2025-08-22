# app\services\pagamento_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
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
            item.pago = True
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id
            item.valor_pago = valor_pago
            data_formatada = form.data_pagamento.data.strftime("%d/%m/%Y")
            item.observacoes = f"Paga em {data_formatada}"

            financiamento_pai = item.financiamento
            novo_saldo_devedor = db.session.query(
                func.sum(FinanciamentoParcela.valor_principal)
            ).filter(
                FinanciamentoParcela.financiamento_id == financiamento_pai.id,
                FinanciamentoParcela.status != "Paga",
            ).scalar() or Decimal(
                "0.00"
            )

            financiamento_pai.saldo_devedor_atual = novo_saldo_devedor

        elif item_tipo == "Crediário":
            item = CrediarioFatura.query.get(item_id)
            item.valor_pago_fatura += valor_pago
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id
            if item.valor_pago_fatura >= item.valor_total_fatura:
                item.status = "Paga"
            else:
                item.status = "Parcialmente Paga"

            ano, mes = map(int, item.mes_referencia.split("-"))
            data_inicio_mes = date(ano, mes, 1)
            if mes == 12:
                data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
            else:
                data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

            parcelas_da_fatura = (
                CrediarioParcela.query.join(CrediarioMovimento)
                .filter(
                    CrediarioMovimento.crediario_id == item.crediario_id,
                    CrediarioParcela.data_vencimento.between(
                        data_inicio_mes, data_fim_mes
                    ),
                )
                .all()
            )

            for parcela in parcelas_da_fatura:
                parcela.pago = True
                parcela.data_pagamento = form.data_pagamento.data

        db.session.commit()
        return True, "Pagamento registrado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar pagamento: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao registrar o pagamento."


def estornar_pagamento(item_id, item_tipo):
    """
    Processa a lógica de negócio para estornar um pagamento.
    """
    try:
        movimento_bancario_id = None
        item_a_atualizar = None

        if item_tipo == "Despesa":
            item_a_atualizar = DespRecMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
        elif item_tipo == "Financiamento":
            item_a_atualizar = FinanciamentoParcela.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
        elif item_tipo == "Crediário":
            item_a_atualizar = CrediarioFatura.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id

        if not movimento_bancario_id:
            return False, "Movimentação bancária associada não encontrada para estorno."

        movimento_a_estornar = ContaMovimento.query.get(movimento_bancario_id)
        if not movimento_a_estornar:
            return False, "Movimentação bancária para estorno não existe mais."

        if item_tipo == "Despesa":
            item_a_atualizar.status = "Pendente"
            item_a_atualizar.valor_realizado = None
            item_a_atualizar.data_pagamento = None
            item_a_atualizar.movimento_bancario_id = None

        elif item_tipo == "Financiamento":
            item_a_atualizar.status = "Pendente"
            item_a_atualizar.data_pagamento = None
            item_a_atualizar.pago = False
            item_a_atualizar.movimento_bancario_id = None
            item_a_atualizar.valor_pago = None
            item_a_atualizar.observacoes = None

            financiamento_pai = item_a_atualizar.financiamento
            novo_saldo_devedor = db.session.query(
                func.sum(FinanciamentoParcela.valor_principal)
            ).filter(
                FinanciamentoParcela.financiamento_id == financiamento_pai.id,
                FinanciamentoParcela.status != "Paga",
            ).scalar() or Decimal(
                "0.00"
            )
            financiamento_pai.saldo_devedor_atual = novo_saldo_devedor

        elif item_tipo == "Crediário":
            item_a_atualizar.valor_pago_fatura = Decimal("0.00")
            item_a_atualizar.status = "Pendente"
            item_a_atualizar.data_pagamento = None
            item_a_atualizar.movimento_bancario_id = None

            ano, mes = map(int, item_a_atualizar.mes_referencia.split("-"))
            data_inicio_mes = date(ano, mes, 1)
            if mes == 12:
                data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
            else:
                data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)
            parcelas_da_fatura = (
                CrediarioParcela.query.join(CrediarioMovimento)
                .filter(
                    CrediarioMovimento.crediario_id == item_a_atualizar.crediario_id,
                    CrediarioParcela.data_vencimento.between(
                        data_inicio_mes, data_fim_mes
                    ),
                )
                .all()
            )
            for parcela in parcelas_da_fatura:
                parcela.pago = False
                parcela.data_pagamento = None

        conta_bancaria = Conta.query.get(movimento_a_estornar.conta_id)
        conta_bancaria.saldo_atual += movimento_a_estornar.valor
        db.session.delete(movimento_a_estornar)

        db.session.commit()
        return True, "Pagamento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar pagamento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o pagamento."
