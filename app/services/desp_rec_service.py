# app/services/desp_rec_service.py (Completo e Atualizado)

from datetime import date

from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_login import current_user
from sqlalchemy import extract

from app import db
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento


def gerar_previsoes(form):
    try:
        desp_rec_id = form.desp_rec_id.data
        valor_previsto = form.valor_previsto.data
        data_inicio = form.data_inicio.data
        numero_meses = form.numero_meses.data
        descricao = form.descricao.data.strip() if form.descricao.data else None

        cadastro_base = db.session.get(DespRec, desp_rec_id)
        if not cadastro_base:
            return False, "Cadastro base не encontrado."

        datas_a_verificar = [
            data_inicio + relativedelta(months=i) for i in range(numero_meses)
        ]
        meses_anos_a_verificar = {(d.year, d.month) for d in datas_a_verificar}

        conflitos = DespRecMovimento.query.filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.desp_rec_id == desp_rec_id,
            extract("year", DespRecMovimento.data_vencimento).in_(
                [y for y, m in meses_anos_a_verificar]
            ),
            extract("month", DespRecMovimento.data_vencimento).in_(
                [m for y, m in meses_anos_a_verificar]
            ),
        ).all()

        if conflitos:
            meses_conflito = sorted(
                {c.data_vencimento.strftime("%m/%Y") for c in conflitos}
            )
            return (
                False,
                f"Erro: Já existem lançamentos para '{cadastro_base.nome}' nos seguintes meses: {', '.join(meses_conflito)}. Nenhuma previsão foi gerada.",
            )

        novos_lancamentos = []
        for i in range(numero_meses):
            data_vencimento_atual = data_inicio + relativedelta(months=i)
            dia_venc = cadastro_base.dia_vencimento or data_vencimento_atual.day
            try:
                data_vencimento_final = data_vencimento_atual.replace(day=dia_venc)
            except ValueError:
                ultimo_dia_mes = (
                    data_vencimento_atual.replace(day=28) + relativedelta(days=4)
                ).replace(day=1) - relativedelta(days=1)
                data_vencimento_final = ultimo_dia_mes

            novo_movimento = DespRecMovimento(
                usuario_id=current_user.id,
                desp_rec_id=desp_rec_id,
                data_vencimento=data_vencimento_final,
                valor_previsto=valor_previsto,
                descricao=descricao,
                status="Pendente",
            )
            novos_lancamentos.append(novo_movimento)

        db.session.bulk_save_objects(novos_lancamentos)
        db.session.commit()
        return True, f"{numero_meses} lançamentos previstos gerados com sucesso!"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao gerar previsões: {e}", exc_info=True)
        return False, "Erro ao gerar previsões. Tente novamente."


def criar_cadastro(form):
    """
    Processa a criação de um novo cadastro de Despesa/Receita.
    A validação de duplicidade já é feita no formulário.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        novo_cadastro = DespRec(
            usuario_id=current_user.id,
            nome=form.nome.data.strip().upper(),
            natureza=form.natureza.data,
            tipo=form.tipo.data,
            dia_vencimento=form.dia_vencimento.data,
            ativo=form.ativo.data,
        )
        db.session.add(novo_cadastro)
        db.session.commit()
        current_app.logger.info(
            f"Cadastro de Despesa/Receita '{novo_cadastro.nome}' criado por {current_user.login}."
        )
        return True, "Cadastro adicionado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao adicionar DespRec: {e}", exc_info=True)
        return False, "Erro ao adicionar o cadastro. Tente novamente."


def atualizar_cadastro(cadastro, form):
    """
    Processa a atualização de um cadastro de Despesa/Receita.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        cadastro.dia_vencimento = form.dia_vencimento.data
        cadastro.ativo = form.ativo.data
        db.session.commit()
        current_app.logger.info(
            f"Cadastro de Despesa/Receita ID {cadastro.id} atualizado por {current_user.login}."
        )
        return True, "Cadastro atualizado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao editar DespRec ID {cadastro.id}: {e}", exc_info=True
        )
        return False, "Erro ao atualizar o cadastro. Tente novamente."


def excluir_cadastro_por_id(cadastro_id):
    """
    Processa a exclusão de um cadastro de Despesa/Receita.
    Retorna uma tupla (sucesso, mensagem).
    """
    cadastro = DespRec.query.filter_by(
        id=cadastro_id, usuario_id=current_user.id
    ).first_or_404()

    if cadastro.movimentos:
        return (
            False,
            "Não é possível excluir este cadastro, pois existem lançamentos associados a ele.",
        )

    try:
        db.session.delete(cadastro)
        db.session.commit()
        current_app.logger.info(
            f"Cadastro de Despesa/Receita ID {cadastro_id} ('{cadastro.nome}') excluído por {current_user.login}."
        )
        return True, "Cadastro excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir DespRec ID {cadastro_id}: {e}", exc_info=True
        )
        return False, "Erro ao excluir o cadastro. Tente novamente."
