# tests\test_usuario_crud.py

from app import db
from app.models.usuario_model import Usuario


def test_admin_can_list_users(admin_auth_client):
    response = admin_auth_client.get("/usuarios/")
    assert response.status_code == 200
    assert b"Gerenciamento de Usu\xc3\xa1rios" in response.data


def test_non_admin_is_redirected(auth_client):
    response = auth_client.get("/usuarios/", follow_redirects=True)
    assert response.status_code == 200
    assert "Dashboard" in response.data.decode("utf-8")
    assert "Você não tem permissão para acessar esta página" in response.data.decode(
        "utf-8"
    )


def test_admin_can_create_user(admin_auth_client, app):
    form_data = {
        "nome": "Novo",
        "sobrenome": "Usuario",
        "email": "novo@usuario.com",
        "login": "novousuario",
        "senha": "Password123!",
        "confirmar_senha": "Password123!",
    }
    response = admin_auth_client.post(
        "/usuarios/adicionar", data=form_data, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Usuário adicionado com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        assert Usuario.query.filter_by(login="novousuario").first() is not None
