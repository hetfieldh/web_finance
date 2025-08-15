# tests/test_basic.py (Com instrução de debug)

import pytest

from app import create_app, db
from config import TestConfig


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_login_page_loads(client):
    """Testa se a página de login carrega."""
    response = client.get("/login")

    # --- PASSO DE DEBUG ---
    # A linha abaixo vai imprimir o HTML completo que o teste está vendo
    print(
        "\n--- CONTEÚDO DA RESPOSTA HTML ---\n",
        response.data.decode("utf-8"),
        "\n--- FIM DO CONTEÚDO ---",
    )

    assert response.status_code == 200
    assert "Login ou E-mail:" in response.data.decode("utf-8")
