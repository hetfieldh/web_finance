# tests/test_basic.py (Completo com 10 testes)

from decimal import Decimal

import pytest

from app import create_app, db
from app.models.conta_model import Conta
from app.models.usuario_model import Usuario
from config import TestConfig


@pytest.fixture()
def app():
    """Cria e configura uma nova instância do app para cada teste."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    """Um cliente de teste para o app."""
    return app.test_client()


# (Os 9 testes anteriores permanecem aqui, inalterados)
def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login ou E-mail:" in response.data.decode("utf-8")


def test_successful_login(client, app):
    with app.app_context():
        test_user = Usuario(
            nome="TEST", sobrenome="USER", login="testuser", email="test@example.com"
        )
        test_user.set_password("password123")
        db.session.add(test_user)
        db.session.commit()
    response = client.post(
        "/login",
        data={"login_ou_email": "testuser", "senha": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    response_text = response.data.decode("utf-8")
    assert "Dashboard" in response_text
    assert "Bem-vindo(a)" in response_text
    assert "Login realizado com sucesso!" in response_text


def test_failed_login_with_wrong_password(client, app):
    with app.app_context():
        test_user = Usuario(
            nome="TEST", sobrenome="USER2", login="testuser2", email="test2@example.com"
        )
        test_user.set_password("correct_password")
        db.session.add(test_user)
        db.session.commit()
    response = client.post(
        "/login",
        data={"login_ou_email": "testuser2", "senha": "wrong_password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    response_text = response.data.decode("utf-8")
    assert "Dashboard" not in response_text
    assert "Login ou senha incorretos. Tente novamente." in response_text


def test_dashboard_redirects_anonymous_user(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200
    response_text = response.data.decode("utf-8")
    assert "Login ou E-mail:" in response_text
    assert "Faça login para acessar." in response_text


def test_create_bank_account(client, app):
    with app.app_context():
        test_user = Usuario(
            nome="TEST",
            sobrenome="ACCOUNTS",
            login="test_account_user",
            email="accounts@test.com",
        )
        test_user.set_password("password")
        db.session.add(test_user)
        db.session.commit()
    client.post(
        "/login", data={"login_ou_email": "test_account_user", "senha": "password"}
    )
    form_data = {
        "nome_banco": "BANCO DE TESTE",
        "agencia": "1234",
        "conta": "567890",
        "tipo": "Corrente",
        "saldo_inicial": 1000.50,
        "limite": 500.00,
    }
    response = client.post("/contas/adicionar", data=form_data, follow_redirects=True)
    assert response.status_code == 200
    response_text = response.data.decode("utf-8")
    assert "Conta bancária adicionada com sucesso!" in response_text
    assert "BANCO DE TESTE" in response_text
    with app.app_context():
        conta = Conta.query.filter_by(nome_banco="BANCO DE TESTE").first()
        assert conta is not None
        assert conta.agencia == "1234"
        assert conta.saldo_atual == Decimal("1000.50")


def test_create_duplicate_bank_account_fails(client, app):
    with app.app_context():
        test_user = Usuario(
            nome="TEST",
            sobrenome="DUPLICATE",
            login="duplicate_user",
            email="duplicate@test.com",
        )
        test_user.set_password("password")
        db.session.add(test_user)
        db.session.commit()
    client.post(
        "/login", data={"login_ou_email": "duplicate_user", "senha": "password"}
    )
    form_data = {
        "nome_banco": "BANCO DUPLICADO",
        "agencia": "4321",
        "conta": "098765",
        "tipo": "Poupança",
        "saldo_inicial": 100.00,
    }
    response1 = client.post("/contas/adicionar", data=form_data, follow_redirects=True)
    assert response1.status_code == 200
    assert "Conta bancária adicionada com sucesso!" in response1.data.decode("utf-8")
    response2 = client.post("/contas/adicionar", data=form_data, follow_redirects=True)
    assert response2.status_code == 200
    response_text = response2.data.decode("utf-8")
    assert "Conta bancária adicionada com sucesso!" not in response_text
    assert (
        "Você já possui uma conta com este banco, agência, número e tipo de conta."
        in response_text
    )
    with app.app_context():
        contas = Conta.query.filter_by(nome_banco="BANCO DUPLICADO").all()
        assert len(contas) == 1


def test_delete_account_with_balance_fails(client, app):
    with app.app_context():
        user = Usuario(
            nome="TEST",
            sobrenome="DELETE",
            login="delete_user",
            email="delete@test.com",
        )
        user.set_password("password")
        conta = Conta(
            usuario=user,
            nome_banco="BANCO COM SALDO",
            agencia="1111",
            conta="2222",
            tipo="Corrente",
            saldo_inicial=100.00,
            saldo_atual=100.00,
        )
        db.session.add_all([user, conta])
        db.session.commit()
        conta_id = conta.id
    client.post("/login", data={"login_ou_email": "delete_user", "senha": "password"})
    response = client.post(f"/contas/excluir/{conta_id}", follow_redirects=True)
    assert response.status_code == 200
    assert (
        "Não é possível excluir a conta. O saldo atual deve ser zero."
        in response.data.decode("utf-8")
    )
    with app.app_context():
        conta_ainda_existe = db.session.get(Conta, conta_id)
        assert conta_ainda_existe is not None


def test_delete_account_successfully(client, app):
    with app.app_context():
        user = Usuario(
            nome="TEST",
            sobrenome="DELETE_OK",
            login="delete_ok_user",
            email="delete_ok@test.com",
        )
        user.set_password("password")
        conta = Conta(
            usuario=user,
            nome_banco="BANCO ZERADO",
            agencia="3333",
            conta="4444",
            tipo="Poupança",
            saldo_inicial=0.00,
            saldo_atual=0.00,
        )
        db.session.add_all([user, conta])
        db.session.commit()
        conta_id = conta.id
    client.post(
        "/login", data={"login_ou_email": "delete_ok_user", "senha": "password"}
    )
    response = client.post(f"/contas/excluir/{conta_id}", follow_redirects=True)
    assert response.status_code == 200
    assert "Conta bancária excluída com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        conta_removida = db.session.get(Conta, conta_id)
        assert conta_removida is None


def test_account_list_is_isolated_per_user(client, app):
    with app.app_context():
        user_a = Usuario(nome="USER", sobrenome="A", login="usera", email="a@test.com")
        user_a.set_password("password_a")
        user_b = Usuario(nome="USER", sobrenome="B", login="userb", email="b@test.com")
        user_b.set_password("password_b")
        conta_a = Conta(
            usuario=user_a,
            nome_banco="BANCO DO USUARIO A",
            agencia="1111",
            conta="AAA",
            tipo="Corrente",
            saldo_inicial=0.00,
            saldo_atual=0.00,
        )
        conta_b = Conta(
            usuario=user_b,
            nome_banco="BANCO SECRETO DO B",
            agencia="2222",
            conta="BBB",
            tipo="Poupança",
            saldo_inicial=0.00,
            saldo_atual=0.00,
        )
        db.session.add_all([user_a, user_b, conta_a, conta_b])
        db.session.commit()
    client.post("/login", data={"login_ou_email": "usera", "senha": "password_a"})
    response = client.get("/contas/")
    response_text = response.data.decode("utf-8")
    assert response.status_code == 200
    assert "BANCO DO USUARIO A" in response_text
    assert "BANCO SECRETO DO B" not in response_text


# <-- ADICIONE O NOVO TESTE ABAIXO -->
def test_update_bank_account(client, app):
    """
    GIVEN um cliente de teste logado
    WHEN ele edita os dados de uma conta existente
    THEN os dados devem ser atualizados no banco de dados.
    """
    # Arrange: Cria usuário e conta, depois faz o login
    with app.app_context():
        user = Usuario(
            nome="TEST",
            sobrenome="UPDATE",
            login="update_user",
            email="update@test.com",
        )
        user.set_password("password")
        conta = Conta(
            usuario=user,
            nome_banco="BANCO ORIGINAL",
            agencia="5555",
            conta="6666",
            tipo="Digital",
            saldo_inicial=100.00,
            saldo_atual=100.00,
            limite=Decimal("50.00"),
        )
        db.session.add_all([user, conta])
        db.session.commit()
        conta_id = conta.id

    client.post("/login", data={"login_ou_email": "update_user", "senha": "password"})

    # Act: Envia dados atualizados para a rota de edição
    update_data = {
        "limite": 250.75,
        "ativa": "y",
    }
    response = client.post(
        f"/contas/editar/{conta_id}", data=update_data, follow_redirects=True
    )

    # Assert: Verifica a resposta e o estado final no banco de dados
    assert response.status_code == 200
    assert "Conta bancária atualizada com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        conta_atualizada = db.session.get(Conta, conta_id)
        assert conta_atualizada is not None
        assert conta_atualizada.limite == Decimal("250.75")
