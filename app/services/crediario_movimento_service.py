# app/services/crediario_movimento_service.py

from decimal import Decimal

from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_login import current_user

from app import db
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela


def adicionar_movimento(form):
    """
    Processa a lógica de negócio para adicionar um movimento de crediário e suas parcelas.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        crediario_id = form.crediario_id.data
        data_primeira_parcela_obj = form.data_primeira_parcela.data

        mes_ano_referencia = data_primeira_parcela_obj.strftime("%Y-%m")
        fatura_existente = CrediarioFatura.query.filter_by(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            mes_referencia=mes_ano_referencia,
        ).first()

        if fatura_existente and fatura_existente.status in [
            "Paga",
            "Parcialmente Paga",
        ]:
            msg = f"Não é possível adicionar uma compra cuja primeira parcela vence em {mes_ano_referencia.split('-')[1]}/{mes_ano_referencia.split('-')[0]}, pois a fatura para este período já foi paga."
            return False, msg

        valor_total_compra = form.valor_total_compra.data
        if form.crediario_grupo_id.data:
            grupo = db.session.get(CrediarioGrupo, form.crediario_grupo_id.data)
            if grupo and grupo.tipo_grupo_crediario == "Estorno":
                valor_total_compra = -valor_total_compra

        numero_parcelas = form.numero_parcelas.data
        if numero_parcelas <= 0:
            return False, "O número de parcelas deve ser no mínimo 1."

        novo_movimento = CrediarioMovimento(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            crediario_grupo_id=(
                form.crediario_grupo_id.data if form.crediario_grupo_id.data else None
            ),
            data_compra=form.data_compra.data,
            valor_total_compra=valor_total_compra,
            descricao=form.descricao.data.strip(),
            data_primeira_parcela=data_primeira_parcela_obj,
            numero_parcelas=numero_parcelas,
        )
        db.session.add(novo_movimento)
        db.session.flush()

        valor_por_parcela = valor_total_compra / Decimal(str(numero_parcelas))
        for i in range(numero_parcelas):
            data_vencimento = data_primeira_parcela_obj + relativedelta(months=i)
            nova_parcela = CrediarioParcela(
                crediario_movimento_id=novo_movimento.id,
                numero_parcela=i + 1,
                data_vencimento=data_vencimento,
                valor_parcela=valor_por_parcela,
                pago=False,
            )
            db.session.add(nova_parcela)

        db.session.commit()
        return True, "Compra no crediário registrada e parcelas geradas com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao adicionar movimento de crediário: {e}", exc_info=True
        )
        return False, "Ocorreu um erro inesperado ao adicionar o movimento."


def editar_movimento(movimento, form):
    """
    Processa a lógica de negócio para editar um movimento de crediário e suas parcelas.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        nova_data_primeira_parcela = form.data_primeira_parcela.data
        if nova_data_primeira_parcela != movimento.data_primeira_parcela:
            mes_ano_referencia = nova_data_primeira_parcela.strftime("%Y-%m")
            fatura_existente = CrediarioFatura.query.filter_by(
                usuario_id=current_user.id,
                crediario_id=movimento.crediario_id,
                mes_referencia=mes_ano_referencia,
            ).first()
            if fatura_existente and fatura_existente.status in [
                "Paga",
                "Parcialmente Paga",
            ]:
                msg = f"Não é possível mover a primeira parcela para {mes_ano_referencia.split('-')[1]}/{mes_ano_referencia.split('-')[0]}, pois a fatura para este período já foi paga."
                return False, msg

        if any(p.pago for p in movimento.parcelas):
            return (
                False,
                "Não é possível editar esta compra, pois ela possui parcelas que já foram pagas.",
            )

        valor_total_compra = form.valor_total_compra.data
        if (
            movimento.crediario_grupo
            and movimento.crediario_grupo.tipo_grupo_crediario == "Estorno"
        ):
            valor_total_compra = -abs(valor_total_compra)

        movimento.data_compra = form.data_compra.data
        movimento.valor_total_compra = valor_total_compra
        movimento.data_primeira_parcela = form.data_primeira_parcela.data
        movimento.numero_parcelas = form.numero_parcelas.data
        movimento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )

        CrediarioParcela.query.filter_by(crediario_movimento_id=movimento.id).delete()
        db.session.flush()

        valor_por_parcela = valor_total_compra / Decimal(str(form.numero_parcelas.data))
        for i in range(form.numero_parcelas.data):
            data_vencimento = form.data_primeira_parcela.data + relativedelta(months=i)
            nova_parcela = CrediarioParcela(
                crediario_movimento_id=movimento.id,
                numero_parcela=i + 1,
                data_vencimento=data_vencimento,
                valor_parcela=valor_por_parcela,
                pago=False,
            )
            db.session.add(nova_parcela)

        db.session.commit()
        return True, "Movimento de crediário atualizado com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao editar movimento de crediário: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao atualizar a compra."


def excluir_movimento(movimento_id):
    """
    Processa a lógica de negócio para excluir um movimento de crediário.
    Retorna uma tupla (sucesso, mensagem).
    """
    movimento = CrediarioMovimento.query.filter_by(
        id=movimento_id, usuario_id=current_user.id
    ).first_or_404()

    for parcela in movimento.parcelas:
        mes_referencia = parcela.data_vencimento.strftime("%Y-%m")
        fatura = CrediarioFatura.query.filter_by(
            crediario_id=movimento.crediario_id,
            usuario_id=current_user.id,
            mes_referencia=mes_referencia,
        ).first()
        if fatura:
            return (
                False,
                f"Não é possível excluir esta compra. A fatura do mês {mes_referencia} já foi gerada.",
            )

    if any(parcela.pago for parcela in movimento.parcelas):
        return (
            False,
            "Não é possível excluir esta compra. Existem parcelas associadas que já foram pagas.",
        )

    try:
        db.session.delete(movimento)
        db.session.commit()
        current_app.logger.info(
            f"Movimentação {movimento.id} excluída por {current_user.login}."
        )
        return True, "Compra no crediário excluída com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir movimento de crediário: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao excluir o movimento."
