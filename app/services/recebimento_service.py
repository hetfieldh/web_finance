# app/services/recebimento_service.py

from datetime import date, timedelta
from decimal import Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import and_

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.services import conta_service
from app.utils import (
    NATUREZA_RECEITA,
    STATUS_PARCIAL_RECEBIDO,
    STATUS_PENDENTE,
    STATUS_RECEBIDO,
)


def get_contas_a_receber_por_mes(ano, mes):
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, 28) + timedelta(days=4)
    ultimo_dia = ultimo_dia - timedelta(days=ultimo_dia.day)

    query_filter = and_(
        DespRecMovimento.usuario_id == current_user.id,
        DespRecMovimento.despesa_receita.has(natureza=NATUREZA_RECEITA),
        DespRecMovimento.data_vencimento.between(primeiro_dia, ultimo_dia),
    )
    receitas_recorrentes = DespRecMovimento.query.filter(query_filter).all()

    lista_contas = []
    for receita in receitas_recorrentes:
        recebido_em = None
        if receita.movimento_bancario and receita.movimento_bancario.conta:
            recebido_em = f"{receita.movimento_bancario.conta.nome_banco} ({receita.movimento_bancario.conta.tipo})"

        lista_contas.append(
            {
                "id_original": receita.id,
                "origem": receita.despesa_receita.nome,
                "tipo": NATUREZA_RECEITA,
                "vencimento": receita.data_vencimento,
                "valor_previsto": receita.valor_previsto,
                "valor_recebido": receita.valor_realizado or Decimal(0),
                "data_pagamento": receita.data_pagamento,
                "recebido_em": recebido_em,
                "status": receita.status,
                "conta_sugerida_id": None,
            }
        )

    salarios = SalarioMovimento.query.filter(
        SalarioMovimento.usuario_id == current_user.id,
        SalarioMovimento.data_recebimento.between(primeiro_dia, ultimo_dia),
    ).all()

    for salario in salarios:
        salario_liquido = salario.salario_liquido
        if salario_liquido > 0:
            is_pago = salario.movimento_bancario_salario_id is not None
            recebido_em_salario = None
            if is_pago and salario.movimento_bancario_salario:
                recebido_em_salario = f"{salario.movimento_bancario_salario.conta.nome_banco} ({salario.movimento_bancario_salario.conta.tipo})"

            folha_tem_fgts = any(
                item.salario_item.tipo == "FGTS" and item.valor > 0
                for item in salario.itens
            )

            lista_contas.append(
                {
                    "id_original": salario.id,
                    "origem": f"SALÁRIO REF. {salario.mes_referencia}",
                    "tipo": "Salário Líquido",
                    "vencimento": salario.data_recebimento,
                    "valor_previsto": salario_liquido,
                    "valor_recebido": salario_liquido if is_pago else Decimal(0),
                    "data_pagamento": (
                        salario.movimento_bancario_salario.data_movimento
                        if is_pago and salario.movimento_bancario_salario
                        else None
                    ),
                    "recebido_em": recebido_em_salario,
                    "status": STATUS_RECEBIDO if is_pago else STATUS_PENDENTE,
                    "conta_sugerida_id": None,
                    "folha_tem_fgts": folha_tem_fgts,
                }
            )
        beneficios_itens = [
            item for item in salario.itens if item.salario_item.tipo == "Benefício"
        ]
        for item_beneficio in beneficios_itens:
            is_beneficio_pago = item_beneficio.movimento_bancario_id is not None
            recebido_em_beneficio = None
            if is_beneficio_pago and item_beneficio.movimento_bancario:
                recebido_em_beneficio = f"{item_beneficio.movimento_bancario.conta.nome_banco} ({item_beneficio.movimento_bancario.conta.tipo})"

            lista_contas.append(
                {
                    "id_original": item_beneficio.id,
                    "origem": item_beneficio.salario_item.nome,
                    "tipo": "Benefício",
                    "vencimento": salario.data_recebimento,
                    "valor_previsto": item_beneficio.valor,
                    "valor_recebido": (
                        item_beneficio.valor if is_beneficio_pago else Decimal(0)
                    ),
                    "data_pagamento": (
                        item_beneficio.movimento_bancario.data_movimento
                        if is_beneficio_pago and item_beneficio.movimento_bancario
                        else None
                    ),
                    "recebido_em": recebido_em_beneficio,
                    "status": STATUS_RECEBIDO if is_beneficio_pago else STATUS_PENDENTE,
                    "conta_sugerida_id": item_beneficio.salario_item.id_conta_destino,
                }
            )

    lista_contas.sort(key=lambda x: x["vencimento"])
    return lista_contas


def _atualizar_status_folha(salario_movimento):
    salario_pago = salario_movimento.movimento_bancario_salario_id is not None
    beneficios_itens = [
        item
        for item in salario_movimento.itens
        if item.salario_item.tipo == "Benefício"
    ]

    beneficios_pagos = all(
        item.movimento_bancario_id is not None for item in beneficios_itens
    )

    if not beneficios_itens:
        beneficios_pagos = True

    if salario_pago and beneficios_pagos:
        salario_movimento.status = STATUS_RECEBIDO
    elif salario_pago or any(item.movimento_bancario_id for item in beneficios_itens):
        salario_movimento.status = STATUS_PARCIAL_RECEBIDO
    else:
        salario_movimento.status = STATUS_PENDENTE


def registrar_recebimento(form):
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

        elif item_tipo == "Salário Líquido":
            item = SalarioMovimento.query.get(item_id)
            item.movimento_bancario_salario_id = novo_movimento.id
            _processar_fgts(item, form.data_recebimento.data, tipo_transacao_credito)
            _atualizar_status_folha(item)

        elif item_tipo == "Benefício":
            item = SalarioMovimentoItem.query.get(item_id)
            if not item:
                raise ValueError("Item de benefício não encontrado.")
            item.movimento_bancario_id = novo_movimento.id
            _atualizar_status_folha(item.movimento_pai)

        db.session.commit()
        return True, "Recebimento registrado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao registrar o recebimento."


def estornar_recebimento(item_id, item_tipo):
    try:
        item_a_atualizar = None
        movimento_bancario_id = None

        if item_tipo == "Receita":
            item_a_atualizar = DespRecMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.status = STATUS_PENDENTE
                item_a_atualizar.valor_realizado = None
                item_a_atualizar.data_pagamento = None
                item_a_atualizar.movimento_bancario_id = None

        elif item_tipo == "Salário Líquido":
            item_a_atualizar = SalarioMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_salario_id
                item_a_atualizar.movimento_bancario_salario_id = None
                _estornar_fgts(item_a_atualizar)
                _atualizar_status_folha(item_a_atualizar)
        elif item_tipo == "Benefício":
            item_a_atualizar = SalarioMovimentoItem.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.movimento_bancario_id = None
                _atualizar_status_folha(item_a_atualizar.movimento_pai)

        if not movimento_bancario_id:
            return False, "Movimentação bancária associada não encontrada para estorno."

        movimento_a_estornar = ContaMovimento.query.get(movimento_bancario_id)
        if not movimento_a_estornar:
            return False, "Movimentação bancária para estorno não existe mais."

        valor_a_debitar = movimento_a_estornar.valor
        conta_bancaria = movimento_a_estornar.conta
        conta_bancaria.saldo_atual -= valor_a_debitar
        db.session.delete(movimento_a_estornar)

        db.session.commit()
        return True, "Recebimento estornado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao estornar recebimento: {e}", exc_info=True)
        return False, "Ocorreu um erro ao estornar o recebimento."


def _processar_fgts(salario_movimento, data_movimento, transacao_fallback):
    fgts_valor = salario_movimento.total_fgts
    if not (fgts_valor and fgts_valor > 0):
        return

    conta_fgts = Conta.query.filter(
        Conta.usuario_id == current_user.id,
        Conta.tipo == "FGTS",
    ).first()

    if conta_fgts:
        tipo_transacao_fgts = (
            ContaTransacao.query.filter_by(
                usuario_id=current_user.id,
                transacao_tipo="RECEBIMENTO_FGTS",
                tipo="Crédito",
            ).first()
            or transacao_fallback
        )

        novo_movimento_fgts = ContaMovimento(
            usuario_id=current_user.id,
            conta_id=conta_fgts.id,
            conta_transacao_id=tipo_transacao_fgts.id,
            data_movimento=data_movimento,
            valor=fgts_valor,
            descricao=f"Crédito de FGTS - Ref: {salario_movimento.mes_referencia}",
        )
        db.session.add(novo_movimento_fgts)
        db.session.flush()
        conta_fgts.saldo_atual += fgts_valor
        salario_movimento.movimento_bancario_fgts_id = novo_movimento_fgts.id
    else:
        current_app.logger.warning("Conta bancária do FGTS não encontrada.")


def _estornar_fgts(salario_movimento):
    if not salario_movimento.movimento_bancario_fgts_id:
        return

    movimento_fgts_a_estornar = ContaMovimento.query.get(
        salario_movimento.movimento_bancario_fgts_id
    )

    if movimento_fgts_a_estornar:
        movimento_fgts_a_estornar.conta.saldo_atual -= movimento_fgts_a_estornar.valor
        db.session.delete(movimento_fgts_a_estornar)

    salario_movimento.movimento_bancario_fgts_id = None
