# tests/conftest.py

import pytest

from app import create_app, db
from app.models.usuario_model import Usuario
from config import TestConfig


@pytest.fixture(scope="function")
def app():
    """Cria uma instância do app para cada teste."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Um cliente de teste para o app."""
    return app.test_client()


@pytest.fixture()
def auth_client(client, app):
    """Um cliente de teste já autenticado com um usuário padrão."""
    with app.app_context():
        user = Usuario(
            nome="DEFAULT",
            sobrenome="USER",
            login="defaultuser",
            email="default@test.com",
        )
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/login", data={"login_ou_email": "defaultuser", "senha": "password"})
    yield client
    client.get("/logout")


@pytest.fixture()
def admin_auth_client(client, app):
    """Um cliente de teste já autenticado com um usuário ADMIN."""
    with app.app_context():
        admin_user = Usuario(
            nome="ADMIN",
            sobrenome="USER",
            login="adminuser",
            email="admin@test.com",
            is_admin=True,
        )
        admin_user.set_password("password")
        db.session.add(admin_user)
        db.session.commit()

    client.post("/login", data={"login_ou_email": "adminuser", "senha": "password"})
    yield client
    client.get("/logout")
