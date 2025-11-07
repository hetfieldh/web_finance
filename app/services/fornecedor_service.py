# app/services/fornecedor_service.py

from flask import current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.fornecedor_model import Fornecedor


def criar_fornecedor(form):
    try:
        novo_fornecedor = Fornecedor(
            usuario_id=current_user.id,
            nome=form.nome.data.strip().upper(),
            descricao=form.descricao.data.strip() if form.descricao.data else None,
        )
        db.session.add(novo_fornecedor)
        db.session.commit()
        current_app.logger.info(
            f'Fornecedor "{novo_fornecedor.nome}" (ID: {novo_fornecedor.id}) adicionado por {current_user.login}.'
        )
        return True, "Fornecedor adicionado com sucesso!"
    except IntegrityError:
        db.session.rollback()
        current_app.logger.warning(
            f"Tentativa de adicionar fornecedor duplicado: {form.nome.data.strip().upper()} por {current_user.login}."
        )
        return False, "Já existe um fornecedor com este nome."
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar fornecedor: {e}", exc_info=True)
        return False, "Ocorreu um erro ao criar o fornecedor."


def atualizar_fornecedor(fornecedor, form):
    try:
        fornecedor.nome = form.nome.data.strip().upper()
        fornecedor.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )
        db.session.commit()
        current_app.logger.info(
            f'Fornecedor "{fornecedor.nome}" (ID: {fornecedor.id}) atualizado por {current_user.login}.'
        )
        return True, "Fornecedor atualizado com sucesso!"
    except IntegrityError:
        db.session.rollback()
        current_app.logger.warning(
            f"Tentativa de atualizar fornecedor para nome duplicado: {form.nome.data.strip().upper()} por {current_user.login}."
        )
        return False, "Já existe um fornecedor com este nome."
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar fornecedor ID {fornecedor.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao atualizar o fornecedor."


def excluir_fornecedor_por_id(fornecedor_id):
    fornecedor = Fornecedor.query.filter_by(
        id=fornecedor_id, usuario_id=current_user.id
    ).first_or_404()

    if fornecedor.movimentos.count() > 0:
        return (
            False,
            "Não é possível excluir este fornecedor. Existem movimentos de crediário associados a ele.",
        )

    try:
        db.session.delete(fornecedor)
        db.session.commit()
        current_app.logger.info(
            f'Fornecedor "{fornecedor.nome}" (ID: {fornecedor.id}) excluído por {current_user.login}.'
        )
        return True, "Fornecedor excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir fornecedor ID {fornecedor.id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro ao excluir o fornecedor."


def get_all_fornecedores_for_user_choices():
    fornecedores = (
        Fornecedor.query.filter_by(usuario_id=current_user.id)
        .order_by(Fornecedor.nome.asc())
        .all()
    )
    choices = [("", "Nenhum")] + [(str(f.id), f.nome) for f in fornecedores]
    return choices
