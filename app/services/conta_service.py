# app/services/conta_service.py

from decimal import Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao


def criar_conta(form):
    try:
        nome_banco = form.nome_banco.data.strip().upper()
        agencia = form.agencia.data.strip()
        conta_num = form.conta.data.strip()
        tipo = form.tipo.data

        if tipo == "FGTS":
            if nome_banco != "FGTS":
                erros = {
                    "form": [
                        "Para contas do tipo FGTS, o nome do banco deve ser 'FGTS'."
                    ]
                }
                return False, erros

            conta_fgts_existente = Conta.query.filter_by(
                usuario_id=current_user.id, tipo="FGTS"
            ).first()
            if conta_fgts_existente:
                erros = {
                    "form": [
                        "Não é permitido cadastrar mais de uma conta do tipo FGTS."
                    ]
                }
                return False, erros

        existing_account = Conta.query.filter_by(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
        ).first()

        if existing_account:
            erros = {
                "form": [
                    "Você já possui uma conta com este banco, agência, número e tipo de conta."
                ]
            }
            return False, erros

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
        return False, {"form": ["Ocorreu um erro inesperado ao criar a conta."]}


def atualizar_conta(conta, form):
    try:
        if not form.ativa.data and Decimal(str(conta.saldo_atual)) != Decimal("0.00"):
            return (
                False,
                "Não é possível inativar a conta. O saldo atual deve ser zero.",
            )

        novo_limite = Decimal(str(form.limite.data or 0))
        saldo_atual = Decimal(str(conta.saldo_atual))

        if saldo_atual < 0 and novo_limite < abs(saldo_atual):
            return (
                False,
                f"O limite não pode ser menor que {abs(saldo_atual):.2f}, "
                f"pois a conta já está negativa em {saldo_atual:.2f}.",
            )

        conta.limite = novo_limite
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


def get_active_accounts_for_user_choices():
    contas_ativas = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco.asc())
        .all()
    )
    choices = [("", "Selecione...")] + [
        (c.id, f"{c.nome_banco} - {c.tipo} (Saldo: {c.saldo_atual:.2f})")
        for c in contas_ativas
    ]
    return choices


def get_active_accounts_for_user_choices_simple():
    contas_ativas = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco.asc())
        .all()
    )
    choices = [("", "Selecione...")] + [
        (c.id, f"{c.nome_banco} - {c.conta} ({c.tipo})") for c in contas_ativas
    ]
    return choices


def get_account_balance_kpis(user_id):
    saldos = (
        db.session.query(
            func.sum(
                case(
                    (
                        Conta.tipo.in_(["Corrente", "Digital", "Dinheiro"]),
                        Conta.saldo_atual,
                    ),
                    else_=0,
                )
            ).label("operacional"),
            func.sum(
                case(
                    (
                        Conta.tipo.in_(["Poupança", "Caixinha", "Investimento"]),
                        Conta.saldo_atual,
                    ),
                    else_=0,
                )
            ).label("investimentos"),
            func.sum(
                case((Conta.tipo == "Benefício", Conta.saldo_atual), else_=0)
            ).label("beneficios"),
            func.sum(case((Conta.tipo == "FGTS", Conta.saldo_atual), else_=0)).label(
                "fgts"
            ),
        )
        .filter(Conta.usuario_id == user_id, Conta.ativa.is_(True))
        .one()
    )

    return {
        "saldo_operacional": saldos.operacional or Decimal("0.00"),
        "saldo_investimentos": saldos.investimentos or Decimal("0.00"),
        "saldo_beneficios": saldos.beneficios or Decimal("0.00"),
        "saldo_fgts": saldos.fgts or Decimal("0.00"),
    }


def validar_estorno_saldo(conta, valor_a_debitar):
    saldo_disponivel = conta.saldo_atual
    if conta.tipo in ["Corrente", "Digital"] and conta.limite:
        saldo_disponivel += conta.limite

    if valor_a_debitar > saldo_disponivel:
        mensagem = (
            f"Estorno não permitido. Saldo insuficiente na conta {conta.nome_banco}. "
            f"Saldo disponível (com limite): {saldo_disponivel:.2f}"
        )
        return False, mensagem

    return True, "Validação de saldo para estorno bem-sucedida."


def has_fgts_account():
    return (
        Conta.query.filter_by(
            usuario_id=current_user.id, tipo="FGTS", ativa=True
        ).first()
        is not None
    )


def get_ultimos_movimentos_bancarios(user_id, limit=10):
    movimentos = (
        ContaMovimento.query.join(Conta, ContaMovimento.conta_id == Conta.id)
        .join(ContaTransacao, ContaMovimento.conta_transacao_id == ContaTransacao.id)
        .filter(ContaMovimento.usuario_id == user_id)
        .options(
            joinedload(ContaMovimento.conta), joinedload(ContaMovimento.tipo_transacao)
        )
        .order_by(ContaMovimento.data_movimento.desc(), ContaMovimento.id.desc())
        .limit(limit)
        .all()
    )
    return movimentos


def get_contas_json():
    contas = (
        Conta.query.filter(
            Conta.usuario_id == current_user.id,
            Conta.ativa == True,
        )
        .order_by(Conta.nome_banco.asc())
        .all()
    )

    contas_list = []
    for conta in contas:
        contas_list.append(
            {
                "id": conta.id,
                "nome": conta.nome_banco,
                "tipo": conta.tipo,
                "saldo_atual": float(conta.saldo_atual or 0),
                "limite": float(conta.limite or 0),
            }
        )
    return contas_list


def get_fgts_info_json():
    has_account = (
        Conta.query.filter_by(
            usuario_id=current_user.id, tipo="FGTS", ativa=True
        ).count()
        > 0
    )

    return {"has_account": has_account}
