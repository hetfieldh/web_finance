# tests/test_auth.py

from app import db
from app.models.usuario_model import Usuario


def test_login_page_loads(client):
    """Testa se a página de login carrega."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login ou E-mail:" in response.data.decode("utf-8")


def test_successful_login(client, app):
    """Testa um login bem-sucedido."""
    with app.app_context():
        user = Usuario(
            nome="TEST", sobrenome="USER", login="testuser", email="test@example.com"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={"login_ou_email": "testuser", "senha": "password123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Login realizado com sucesso!" in response.data.decode("utf-8")
    assert "Dashboard" in response.data.decode("utf-8")


def test_failed_login(client, app):
    """Testa um login com senha incorreta."""
    with app.app_context():
        user = Usuario(
            nome="TEST", sobrenome="FAIL", login="failuser", email="fail@example.com"
        )
        user.set_password("correct_password")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={"login_ou_email": "failuser", "senha": "wrong_password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Login ou senha incorretos. Tente novamente." in response.data.decode(
        "utf-8"
    )


def test_dashboard_redirects_anonymous_user(client):
    """Testa se um usuário não logado é redirecionado do dashboard."""
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    assert "Faça login para acessar." in response.data.decode("utf-8")


def test_logout(auth_client):
    """Testa se o logout funciona para um usuário logado."""
    response = auth_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert "Você foi desconectado." in response.data.decode("utf-8")
    assert "Login ou E-mail:" in response.data.decode("utf-8")
