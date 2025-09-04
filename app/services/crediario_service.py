# app/services/crediario_service.py

from flask import current_app
from flask_login import current_user

from app import db
from app.models.crediario_model import Crediario


def criar_crediario(form):
    try:
        novo_crediario = Crediario(
            usuario_id=current_user.id,
            nome_crediario=form.nome_crediario.data.strip().upper(),
            tipo_crediario=form.tipo_crediario.data,
            identificador_final=(
                form.identificador_final.data.strip().upper()
                if form.identificador_final.data
                else None
            ),
            limite_total=form.limite_total.data,
            ativa=form.ativa.data,
        )
        db.session.add(novo_crediario)
        db.session.commit()
        current_app.logger.info(
            f'Crediário "{novo_crediario.nome_crediario}" ({novo_crediario.tipo_crediario}) adicionado por {current_user.login}.'
        )
        return True, "Crediário adicionado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar crediário: {e}", exc_info=True)
        return False, "Ocorreu um erro ao criar o crediário."


def atualizar_crediario(crediario, form):
    try:
        crediario.nome_crediario = form.nome_crediario.data.strip().upper()
        crediario.identificador_final = (
            form.identificador_final.data.strip().upper()
            if form.identificador_final.data
            else None
        )
        crediario.limite_total = form.limite_total.data
        crediario.ativa = form.ativa.data
        db.session.commit()
        current_app.logger.info(
            f'Crediário "{crediario.nome_crediario}" (ID: {crediario.id}) atualizado por {current_user.login}.'
        )
        return True, "Crediário atualizado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar crediário ID {crediario.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao atualizar o crediário."


def excluir_crediario_por_id(crediario_id):
    crediario = Crediario.query.filter_by(
        id=crediario_id, usuario_id=current_user.id
    ).first_or_404()

    if crediario.movimentos_crediario:
        return (
            False,
            "Não é possível excluir este crediário. Existem movimentos de crediário associados a ele.",
        )

    try:
        db.session.delete(crediario)
        db.session.commit()
        current_app.logger.info(
            f'Crediário "{crediario.nome_crediario}" (ID: {crediario.id}) excluído por {current_user.login}.'
        )
        return True, "Crediário excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir crediário ID {crediario.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao excluir o crediário."


def get_active_crediarios_for_user_choices():
    crediarios = (
        Crediario.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Crediario.nome_crediario.asc())
        .all()
    )
    choices = [("", "Selecione...")] + [
        (str(c.id), f"{c.nome_crediario} ({c.tipo_crediario})") for c in crediarios
    ]
    return choices
