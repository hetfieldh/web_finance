# app/services/usuario_service.py (Completo e Atualizado)

from flask import current_app
from flask_login import current_user
from werkzeug.security import generate_password_hash

from app import db
from app.models.conta_transacao_model import ContaTransacao
from app.models.usuario_model import Usuario


def _criar_transacoes_padrao(novo_usuario):
    """
    Cria um conjunto de tipos de transação padrão para um novo usuário.
    """
    transacoes_padrao = [
        {"transacao_tipo": "PAGAMENTO", "tipo": "Débito"},
        {"transacao_tipo": "RECEBIMENTO", "tipo": "Crédito"},
        {"transacao_tipo": "AMORTIZAÇÃO", "tipo": "Débito"},
        {"transacao_tipo": "TRANSFERÊNCIA", "tipo": "Débito"},
        {"transacao_tipo": "TRANSFERÊNCIA", "tipo": "Crédito"},
        {"transacao_tipo": "SALÁRIO", "tipo": "Crédito"},
        {"transacao_tipo": "DEPÓSITO", "tipo": "Crédito"},
        {"transacao_tipo": "SAQUE", "tipo": "Débito"},
        {"transacao_tipo": "APORTE", "tipo": "Débito"},
        {"transacao_tipo": "APORTE", "tipo": "Crédito"},
        {"transacao_tipo": "RESGATE", "tipo": "Crédito"},
        {"transacao_tipo": "PIX", "tipo": "Crédito"},
        {"transacao_tipo": "PIX", "tipo": "Débito"},
    ]

    for transacao_data in transacoes_padrao:
        nova_transacao = ContaTransacao(
            usuario_id=novo_usuario.id,
            transacao_tipo=transacao_data["transacao_tipo"],
            tipo=transacao_data["tipo"],
        )
        db.session.add(nova_transacao)


def criar_novo_usuario(form):
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
        db.session.flush()

        _criar_transacoes_padrao(novo_usuario)

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
    usuario_a_excluir = Usuario.query.get_or_404(usuario_id)

    if current_user.id == usuario_a_excluir.id:
        current_app.logger.warning(
            f"Tentativa de auto-exclusão bloqueada para {current_user.login}."
        )
        return False, "Você não pode excluir seu próprio usuário."

    if (
        usuario_a_excluir.contas
        or usuario_a_excluir.movimentos
        or usuario_a_excluir.tipos_transacao
    ):
        return (
            False,
            "Não é possível excluir o usuário. Existem dados associados a ele.",
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


def atualizar_perfil_usuario(usuario, form):
    try:
        usuario.nome = form.nome.data.strip().upper()
        usuario.sobrenome = form.sobrenome.data.strip().upper()
        usuario.email = form.email.data.strip()

        if form.nova_senha.data:
            if not usuario.check_password(form.senha_atual.data):
                return False, {"senha_atual": ["A senha atual está incorreta."]}

            usuario.set_password(form.nova_senha.data)
            usuario.precisa_alterar_senha = False

        db.session.commit()
        current_app.logger.info(
            f"Perfil do usuário {usuario.login} atualizado com sucesso."
        )
        return True, "Perfil atualizado com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao atualizar perfil do usuário {usuario.login}: {e}", exc_info=True
        )
        return False, {"form": ["Ocorreu um erro inesperado ao atualizar o perfil."]}
