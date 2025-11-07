# app/services/crediario_subgrupo_service.py

from flask import current_app, jsonify
from flask_login import current_user
from sqlalchemy.orm import joinedload

from app import db
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_subgrupo_model import CrediarioSubgrupo


def get_subgrupos_for_grupo_choices(grupo_id):
    if not grupo_id:
        return [("", "Selecione um Grupo...")]

    subgrupos = (
        CrediarioSubgrupo.query.filter_by(usuario_id=current_user.id, grupo_id=grupo_id)
        .order_by(CrediarioSubgrupo.nome.asc())
        .all()
    )
    choices = [(str(sg.id), sg.nome) for sg in subgrupos]
    if not choices:
        return [("", "Nenhum subgrupo encontrado")]
    return [("", "Selecione...")] + choices


def get_subgrupos_by_grupo_id_json(grupo_id):
    subgrupos = (
        CrediarioSubgrupo.query.filter_by(usuario_id=current_user.id, grupo_id=grupo_id)
        .order_by(CrediarioSubgrupo.nome.asc())
        .all()
    )
    return jsonify([{"id": sg.id, "nome": sg.nome} for sg in subgrupos])


def get_all_subgrupos_for_user():
    return (
        CrediarioSubgrupo.query.filter_by(usuario_id=current_user.id)
        .options(joinedload(CrediarioSubgrupo.grupo))
        .order_by(CrediarioSubgrupo.nome.asc())
        .all()
    )


def criar_subgrupo(form):
    try:
        novo_subgrupo = CrediarioSubgrupo(
            usuario_id=current_user.id,
            grupo_id=form.grupo_id.data,
            nome=form.nome.data.strip().upper(),
        )
        db.session.add(novo_subgrupo)
        db.session.commit()
        current_app.logger.info(
            f'Subgrupo "{novo_subgrupo.nome}" (Grupo ID: {novo_subgrupo.grupo_id}) adicionado por {current_user.login}.'
        )
        return True, "Subgrupo adicionado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar subgrupo: {e}", exc_info=True)
        return False, "Ocorreu um erro ao criar o subgrupo."


def atualizar_subgrupo(subgrupo, form):
    try:
        subgrupo.grupo_id = form.grupo_id.data
        subgrupo.nome = form.nome.data.strip().upper()
        db.session.commit()
        current_app.logger.info(
            f'Subgrupo "{subgrupo.nome}" (ID: {subgrupo.id}) atualizado por {current_user.login}.'
        )
        return True, "Subgrupo atualizado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar subgrupo ID {subgrupo.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao atualizar o subgrupo."


def excluir_subgrupo_por_id(subgrupo_id):
    subgrupo = CrediarioSubgrupo.query.filter_by(
        id=subgrupo_id, usuario_id=current_user.id
    ).first_or_404()

    if subgrupo.movimentos_subgrupo:
        return (
            False,
            "Não é possível excluir este subgrupo. Existem movimentos de crediário associados a ele.",
        )

    try:
        db.session.delete(subgrupo)
        db.session.commit()
        current_app.logger.info(
            f'Subgrupo "{subgrupo.nome}" (ID: {subgrupo.id}) excluído por {current_user.login}.'
        )
        return True, "Subgrupo excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir subgrupo ID {subgrupo.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao excluir o subgrupo."
