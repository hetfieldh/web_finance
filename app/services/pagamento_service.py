# app/services/pagamento_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.utils import (
    NATUREZA_DESPESA,
    STATUS_ATRASADO,
    STATUS_PAGO,
    STATUS_PARCIAL_PAGO,
    STATUS_PENDENTE,
)


def get_contas_a_pagar_por_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = (primeiro_dia + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    contas_a_pagar = []
    TWO_PLACES = Decimal("0.01")

    faturas = CrediarioFatura.query.filter(
        CrediarioFatura.usuario_id == current_user.id,
        CrediarioFatura.data_vencimento_fatura.between(primeiro_dia, ultimo_dia),
    ).all()
    for fatura in faturas:
        pago_com = None
        if fatura.movimento_bancario and fatura.movimento_bancario.conta:
            pago_com = f"{fatura.movimento_bancario.conta.nome_banco} ({fatura.movimento_bancario.conta.tipo})"

        soma_parcelas_query = (
            db.session.query(func.sum(CrediarioParcela.valor_parcela))
            .join(
                CrediarioMovimento,
                CrediarioMovimento.id == CrediarioParcela.crediario_movimento_id,
            )
            .filter(
                CrediarioMovimento.crediario_id == fatura.crediario_id,
                func.date_format(CrediarioParcela.data_vencimento, "%Y-%m")
                == fatura.mes_referencia,
            )
            .scalar()
        )
        soma_parcelas = soma_parcelas_query or Decimal("0.00")

        valor_fatura_rounded = (fatura.valor_total_fatura or Decimal("0.00")).quantize(
            TWO_PLACES
        )
        soma_parcelas_rounded = soma_parcelas.quantize(TWO_PLACES)
        desatualizada = valor_fatura_rounded != soma_parcelas_rounded

        contas_a_pagar.append(
            {
                "vencimento": fatura.data_vencimento_fatura,
                "origem": f"FATURA {fatura.crediario.nome_crediario}",
                "valor_display": fatura.valor_total_fatura,
                "valor_pago": fatura.valor_pago_fatura or Decimal("0.00"),
                "status": fatura.status,
                "data_pagamento": fatura.data_pagamento,
                "id_original": fatura.id,
                "tipo": "Crediário",
                "pago_com": pago_com,
                "valor_pendente": fatura.valor_total_fatura
                - (fatura.valor_pago_fatura or 0),
                "desatualizada": desatualizada,
            }
        )

    parcelas = (
        FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
        .filter(
            FinanciamentoParcela.data_vencimento.between(primeiro_dia, ultimo_dia),
            Financiamento.usuario_id == current_user.id,
        )
        .all()
    )
    for parcela in parcelas:
        pago_com = None
        if parcela.movimento_bancario and parcela.movimento_bancario.conta:
            pago_com = f"{parcela.movimento_bancario.conta.nome_banco} ({parcela.movimento_bancario.conta.tipo})"

        contas_a_pagar.append(
            {
                "vencimento": parcela.data_vencimento,
                "origem": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                "valor_display": parcela.valor_total_previsto,
                "valor_pago": parcela.valor_pago or Decimal("0.00"),
                "status": parcela.status,
                "data_pagamento": parcela.data_pagamento,
                "id_original": parcela.id,
                "tipo": "Financiamento",
                "pago_com": pago_com,
                "valor_pendente": parcela.valor_total_previsto
                - (parcela.valor_pago or 0),
            }
        )

    despesas = (
        DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
        .filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento.between(primeiro_dia, ultimo_dia),
            DespRecMovimento.despesa_receita.has(natureza="Despesa"),
        )
        .all()
    )
    for despesa in despesas:
        pago_com = None
        if despesa.movimento_bancario and despesa.movimento_bancario.conta:
            pago_com = f"{despesa.movimento_bancario.conta.nome_banco} ({despesa.movimento_bancario.conta.tipo})"

        contas_a_pagar.append(
            {
                "vencimento": despesa.data_vencimento,
                "origem": despesa.despesa_receita.nome,
                "valor_display": despesa.valor_previsto,
                "valor_pago": despesa.valor_realizado or Decimal("0.00"),
                "status": despesa.status,
                "data_pagamento": despesa.data_pagamento,
                "id_original": despesa.id,
                "tipo": "Despesa",
                "pago_com": pago_com,
                "valor_pendente": despesa.valor_previsto
                - (despesa.valor_realizado or 0),
            }
        )

    contas_a_pagar.sort(key=lambda x: x["vencimento"])
    return contas_a_pagar


def registrar_pagamento(form):
    try:
        conta_debito = Conta.query.get(form.conta_id.data)
        valor_pago = form.valor_pago.data

        saldo_disponivel = conta_debito.saldo_atual
        if conta_debito.tipo in ["Corrente", "Digital"] and conta_debito.limite:
            saldo_disponivel += conta_debito.limite

        if valor_pago > saldo_disponivel:
            return (
                False,
                f"Saldo insuficiente na conta {conta_debito.nome_banco}. Saldo disponível (com limite):  {saldo_disponivel:.2f}",
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
            item.status = STATUS_PAGO
            item.valor_realizado = valor_pago
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id

        elif item_tipo == "Financiamento":
            item = FinanciamentoParcela.query.get(item_id)
            item.status = STATUS_PAGO
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
                FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
            ).scalar() or Decimal(
                "0.00"
            )

            financiamento_pai.saldo_devedor_atual = novo_saldo_devedor

        elif item_tipo == "Crediário":
            item = CrediarioFatura.query.get(item_id)
            item.valor_pago_fatura = (item.valor_pago_fatura or 0) + valor_pago
            item.data_pagamento = form.data_pagamento.data
            item.movimento_bancario_id = novo_movimento.id
            if item.valor_pago_fatura >= item.valor_total_fatura:
                item.status = STATUS_PAGO
            else:
                item.status = STATUS_PARCIAL_PAGO

        db.session.commit()
        return True, "Pagamento registrado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar pagamento: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao registrar o pagamento."


def estornar_pagamento(item_id, item_tipo):
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

        valor_a_creditar = abs(movimento_a_estornar.valor)
        conta_bancaria = movimento_a_estornar.conta
        conta_bancaria.saldo_atual += valor_a_creditar
        db.session.delete(movimento_a_estornar)

        if item_tipo == "Despesa":
            item_a_atualizar.status = STATUS_PENDENTE
            item_a_atualizar.valor_realizado = None
            item_a_atualizar.data_pagamento = None
            item_a_atualizar.movimento_bancario_id = None

        elif item_tipo == "Financiamento":
            item_a_atualizar.status = STATUS_PENDENTE
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
                FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
            ).scalar() or Decimal(
                "0.00"
            )
            financiamento_pai.saldo_devedor_atual = (
                novo_saldo_devedor + item_a_atualizar.valor_principal
            )

        elif item_tipo == "Crediário":
            item_a_atualizar.valor_pago_fatura = Decimal("0.00")
            item_a_atualizar.status = STATUS_PENDENTE
            item_a_atualizar.data_pagamento = None
            item_a_atualizar.movimento_bancario_id = None

        db.session.commit()
        return True, "Pagamento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar pagamento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o pagamento."
