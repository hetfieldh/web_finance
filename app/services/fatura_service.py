# app/services/fatura_service.py

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela


def gerar_fatura(crediario_id, mes_ano_str):
    """
    Processa a lógica de negócio para gerar uma nova fatura de crediário.
    Retorna uma tupla (sucesso, mensagem, objeto_fatura_ou_none).
    """
    try:
        fatura_existente = CrediarioFatura.query.filter_by(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            mes_referencia=mes_ano_str,
        ).first()

        if fatura_existente:
            return (
                False,
                "Fatura para este período e crediário já existe. Visualizando...",
                fatura_existente,
            )

        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = date(ano, mes, 1)
        data_fim_mes = (data_inicio_mes + timedelta(days=31)).replace(
            day=1
        ) - timedelta(days=1)

        valor_total_calculado = (
            db.session.query(
                func.coalesce(func.sum(CrediarioParcela.valor_parcela), Decimal("0.00"))
            )
            .join(CrediarioMovimento)
            .filter(
                CrediarioMovimento.id == CrediarioParcela.crediario_movimento_id,
                CrediarioMovimento.crediario_id == crediario_id,
                CrediarioMovimento.usuario_id == current_user.id,
                CrediarioParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
            )
            .scalar()
        )

        if valor_total_calculado <= 0:
            return False, "Não há movimentações para gerar fatura neste período.", None

        nova_fatura = CrediarioFatura(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            mes_referencia=mes_ano_str,
            valor_total_fatura=valor_total_calculado,
            data_fechamento=date.today(),
            data_vencimento_fatura=data_fim_mes,
            status="Pendente",
        )
        db.session.add(nova_fatura)
        db.session.commit()

        current_app.logger.info(
            f"Fatura (ID: {nova_fatura.id}) para o mês {mes_ano_str} gerada por {current_user.login}."
        )
        return True, "Fatura gerada com sucesso!", nova_fatura

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro inesperado ao gerar fatura: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado ao gerar a fatura.", None


def recalcular_fatura(fatura_id):
    """
    Processa a lógica de negócio para recalcular o valor de uma fatura existente.
    Retorna uma tupla (sucesso, mensagem).
    """
    fatura = CrediarioFatura.query.filter_by(
        id=fatura_id, usuario_id=current_user.id
    ).first_or_404()

    if fatura.status in ["Paga", "Parcialmente Paga"]:
        return (
            False,
            "Não é possível recalcular uma fatura que já está paga ou parcialmente paga.",
        )

    try:
        ano, mes = map(int, fatura.mes_referencia.split("-"))
        data_inicio_mes = date(ano, mes, 1)
        data_fim_mes = (data_inicio_mes + timedelta(days=31)).replace(
            day=1
        ) - timedelta(days=1)

        valor_total_recalculado = (
            db.session.query(
                func.coalesce(func.sum(CrediarioParcela.valor_parcela), Decimal("0.00"))
            )
            .join(CrediarioMovimento)
            .filter(
                CrediarioMovimento.id == CrediarioParcela.crediario_movimento_id,
                CrediarioMovimento.crediario_id == fatura.crediario_id,
                CrediarioMovimento.usuario_id == current_user.id,
                CrediarioParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
            )
            .scalar()
        )

        fatura.valor_total_fatura = valor_total_recalculado
        db.session.commit()
        current_app.logger.info(
            f"Fatura (ID: {fatura.id}) recalculada por {current_user.login}."
        )
        return True, "Fatura atualizada com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao recalcular fatura (ID: {fatura.id}): {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao atualizar a fatura."


def automatizar_geracao_e_atualizacao_faturas(user_id):
    """
    Usa o SQLAlchemy ORM para analisar todas as parcelas de crediário não pagas e,
    para cada combinação de (crediário, mês), cria ou atualiza a fatura correspondente.
    """
    try:
        current_app.logger.info(
            f"Iniciando sincronização (ORM) para user ID: {user_id}"
        )

        # 1. Busca Simples: Carregar todas as parcelas pendentes do usuário.
        parcelas_pendentes = (
            CrediarioParcela.query.join(CrediarioMovimento)
            .filter(
                CrediarioMovimento.usuario_id == user_id,
                CrediarioParcela.pago == False,
            )
            .options(
                joinedload(CrediarioParcela.movimento_pai).joinedload(
                    CrediarioMovimento.crediario
                )
            )
            .all()
        )

        if not parcelas_pendentes:
            current_app.logger.info(
                "Nenhuma parcela pendente encontrada para processar."
            )
            return (
                True,
                "Não foram encontradas novas parcelas para gerar ou atualizar faturas.",
            )

        # 2. Agrupamento em Python: Agrupar as parcelas por crediário e mês.
        totais_por_fatura = defaultdict(
            lambda: {"valor": Decimal("0.00"), "vencimento": None}
        )
        for parcela in parcelas_pendentes:
            mes_referencia = parcela.data_vencimento.strftime("%Y-%m")
            chave = (parcela.movimento_pai.crediario_id, mes_referencia)

            totais_por_fatura[chave]["valor"] += parcela.valor_parcela
            if (
                totais_por_fatura[chave]["vencimento"] is None
                or parcela.data_vencimento > totais_por_fatura[chave]["vencimento"]
            ):
                data_fim_mes = (
                    parcela.data_vencimento.replace(day=28) + timedelta(days=4)
                ).replace(day=1) - timedelta(days=1)
                totais_por_fatura[chave]["vencimento"] = data_fim_mes

        # 3. Obter faturas existentes
        faturas_pendentes_existentes = CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.status.in_(["Pendente", "Atrasada"]),
        ).all()
        lookup_faturas = {
            (f.crediario_id, f.mes_referencia): f for f in faturas_pendentes_existentes
        }

        faturas_criadas = 0
        faturas_atualizadas = 0

        # 4. Iterar sobre os grupos para criar ou atualizar faturas
        for (crediario_id, mes_ano_str), dados in totais_por_fatura.items():
            valor_total_real = dados["valor"]
            data_vencimento_fatura = dados["vencimento"]

            fatura_existente = lookup_faturas.get((crediario_id, mes_ano_str))

            if fatura_existente:
                if fatura_existente.valor_total_fatura != valor_total_real:
                    fatura_existente.valor_total_fatura = valor_total_real
                    faturas_atualizadas += 1
            else:
                nova_fatura = CrediarioFatura(
                    usuario_id=user_id,
                    crediario_id=crediario_id,
                    mes_referencia=mes_ano_str,
                    valor_total_fatura=valor_total_real,
                    data_vencimento_fatura=data_vencimento_fatura,
                    status="Pendente",
                )
                db.session.add(nova_fatura)
                faturas_criadas += 1

        db.session.commit()

        mensagem = f"{faturas_criadas} nova(s) fatura(s) gerada(s) e {faturas_atualizadas} fatura(s) atualizada(s) com sucesso!"
        current_app.logger.info(
            f"Sincronização de faturas para user {user_id}: {mensagem}"
        )
        return True, mensagem

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao automatizar faturas com ORM: {e}", exc_info=True
        )
        return False, "Ocorreu um erro inesperado durante a sincronização das faturas."
