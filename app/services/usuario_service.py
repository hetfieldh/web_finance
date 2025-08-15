# app/services/usuario_service.py

from flask import current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash

from app import db
from app.models.usuario_model import Usuario


def criar_novo_usuario(form):
    """
    Processa a lógica de negócio para criar um novo usuário.
    Retorna uma tupla (sucesso, mensagem, objeto_usuario_ou_none).
    """
    try:
        novo_usuario = Usuario(
            nome=form.nome.data.strip().upper(),
            sobrenome=form.sobrenome.data.strip().upper(),
            email=form.email.data.strip(),
            login=form.login.data.strip().lower(),
            is_admin=form.is_admin.data,
        )
        novo_usuario.set_password(form.senha.data)

        db.session.add(novo_usuario)
        db.session.commit()

        current_app.logger.info(
            f"Usuário {novo_usuario.login} adicionado por {current_user.login}."
        )
        return True, "Usuário adicionado com sucesso!", novo_usuario
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar novo usuário: {e}", exc_info=True)
        return False, "Ocorreu um erro ao criar o usuário.", None


def excluir_usuario_por_id(usuario_id):
    """
    Processa a lógica de negócio para excluir um usuário.
    Retorna uma tupla (sucesso, mensagem).
    """
    usuario_a_excluir = Usuario.query.get_or_404(usuario_id)

    if current_user.id == usuario_a_excluir.id:
        current_app.logger.warning(
            f"Tentativa de auto-exclusão bloqueada para {current_user.login}."
        )
        return False, "Você не pode excluir seu próprio usuário."

    if usuario_a_excluir.contas:
        return (
            False,
            "Não é possível excluir o usuário. Existem contas bancárias associadas a ele.",
        )
    if usuario_a_excluir.movimentos:
        return (
            False,
            "Não é possível excluir o usuário. Existem movimentações associadas a ele.",
        )
    if usuario_a_excluir.tipos_transacao:
        return (
            False,
            "Não é possível excluir o usuário. Existem tipos de transação associados a ele.",
        )

    try:
        db.session.delete(usuario_a_excluir)
        db.session.commit()
        current_app.logger.info(
            f"Usuário {usuario_a_excluir.login} (ID: {usuario_a_excluir.id}) excluído por {current_user.login}."
        )
        return True, "Usuário excluído com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao excluir usuário ID {usuario_id}: {e}", exc_info=True
        )
        return False, "Ocorreu um erro inesperado ao excluir o usuário."
