# app/services/crediario_grupo_service.py

from flask import current_app
from flask_login import current_user

from app import db
from app.models.crediario_grupo_model import CrediarioGrupo


def criar_grupo(form):
    """
    Processa a criação de um novo grupo de crediário.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        novo_grupo = CrediarioGrupo(
            usuario_id=current_user.id,
            grupo_crediario=form.grupo_crediario.data.strip().upper(),
            tipo_grupo_crediario=form.tipo_grupo_crediario.data,
            descricao=form.descricao.data.strip() if form.descricao.data else None,
        )
        db.session.add(novo_grupo)
        db.session.commit()
        current_app.logger.info(
            f'Grupo de crediário "{novo_grupo.grupo_crediario}" ({novo_grupo.tipo_grupo_crediario}) adicionado por {current_user.login}.'
        )
        return True, "Grupo de crediário adicionado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao criar grupo de crediário: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao criar o grupo."


def atualizar_grupo(grupo, form):
    """
    Processa a atualização de um grupo de crediário.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        grupo.grupo_crediario = form.grupo_crediario.data.strip().upper()
        grupo.descricao = form.descricao.data.strip() if form.descricao.data else None
        db.session.commit()
        current_app.logger.info(
            f'Grupo de crediário "{grupo.grupo_crediario}" (ID: {grupo.id}) atualizado por {current_user.login}.'
        )
        return True, "Grupo de crediário atualizado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar grupo de crediário ID {grupo.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao atualizar o grupo."


def excluir_grupo_por_id(grupo_id):
    """
    Processa a exclusão de um grupo, validando as regras de negócio.
    Retorna uma tupla (sucesso, mensagem).
    """
    grupo = CrediarioGrupo.query.filter_by(
        id=grupo_id, usuario_id=current_user.id
    ).first_or_404()
    if grupo.movimentos:
        return (
            False,
            "Não é possível excluir este grupo. Existem movimentos de crediário associados a ele.",
        )

    try:
        db.session.delete(grupo)
        db.session.commit()
        current_app.logger.info(
            f'Grupo de crediário "{grupo.grupo_crediario}" (ID: {grupo.id}) excluído por {current_user.login}.'
        )
        return True, "Grupo de crediário excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir grupo de crediário ID {grupo.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao excluir o grupo."


def get_all_crediario_grupos_for_user_choices():
    """
    Busca todos os grupos de crediário do usuário e formata como choices.
    """
    grupos = (
        CrediarioGrupo.query.filter_by(usuario_id=current_user.id)
        .order_by(CrediarioGrupo.grupo_crediario.asc())
        .all()
    )
    choices = [("", "Nenhum")] + [
        (str(cg.id), f"{cg.grupo_crediario} ({cg.tipo_grupo_crediario})")
        for cg in grupos
    ]
    return choices
