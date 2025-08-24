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


def automatizar_geracao_e_atualizacao_faturas(user_id):
    """
    Usa o SQLAlchemy ORM para analisar todas as parcelas de crediário não pagas e,
    para cada combinação de (crediário, mês), cria ou atualiza a fatura correspondente.
    """
    try:
        current_app.logger.info(
            f"Iniciando sincronização (ORM) para user ID: {user_id}"
        )

        # 1. Encontrar todas as combinações únicas de (crediário, mês) com parcelas pendentes.
        tarefas = (
            db.session.query(
                CrediarioMovimento.crediario_id,
                func.to_char(CrediarioParcela.data_vencimento, "YYYY-MM").label(
                    "mes_referencia"
                ),
            )
            .join(
                CrediarioMovimento,
                CrediarioMovimento.id == CrediarioParcela.crediario_movimento_id,
            )
            .filter(
                CrediarioMovimento.usuario_id == user_id,
                CrediarioParcela.pago == False,
            )
            .distinct()
            .all()
        )

        current_app.logger.info(
            f"Encontradas {len(tarefas)} combinações de (crediário, mês) para processar."
        )
        if not tarefas:
            return (
                True,
                "Não foram encontradas novas parcelas para gerar ou atualizar faturas.",
            )

        # 2. Obter todas as faturas pendentes existentes para consulta rápida
        faturas_pendentes_existentes = CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == user_id,
            CrediarioFatura.status.in_(["Pendente", "Atrasada"]),
        ).all()
        lookup_faturas = {
            (f.crediario_id, f.mes_referencia): f for f in faturas_pendentes_existentes
        }

        faturas_criadas = 0
        faturas_atualizadas = 0

        # 3. Iterar sobre cada tarefa encontrada
        for tarefa in tarefas:
            crediario_id = tarefa.crediario_id
            mes_ano_str = tarefa.mes_referencia
            ano, mes = map(int, mes_ano_str.split("-"))
            data_inicio_mes = date(ano, mes, 1)
            data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
                day=1
            ) - timedelta(days=1)

            # 4. Calcular o valor total real das parcelas para aquele mês/crediário
            valor_total_real = (
                db.session.query(func.sum(CrediarioParcela.valor_parcela))
                .join(CrediarioMovimento)
                .filter(
                    CrediarioMovimento.usuario_id == user_id,
                    CrediarioMovimento.crediario_id == crediario_id,
                    CrediarioParcela.data_vencimento.between(
                        data_inicio_mes, data_fim_mes
                    ),
                )
                .scalar()
            ) or Decimal("0.00")

            # 5. Decidir se cria uma nova fatura ou atualiza uma existente
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
                    data_vencimento_fatura=data_fim_mes,
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
