# tests/test_conta.py

from decimal import Decimal

from app import db
from app.models.conta_model import Conta
from app.models.usuario_model import Usuario


def test_create_bank_account(auth_client, app):
    """Testa a criação de uma conta bancária com sucesso."""
    form_data = {
        "nome_banco": "BANCO DE TESTE",
        "agencia": "1234",
        "conta": "567890",
        "tipo": "Corrente",
        "saldo_inicial": 1000.50,
        "limite": 500.00,
    }
    response = auth_client.post(
        "/contas/adicionar", data=form_data, follow_redirects=True
    )

    assert response.status_code == 200
    assert "Conta bancária adicionada com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        conta = Conta.query.filter_by(nome_banco="BANCO DE TESTE").first()
        assert conta is not None
        assert conta.saldo_atual == Decimal("1000.50")


def test_create_duplicate_bank_account_fails(auth_client, app):
    """Testa a falha ao tentar criar uma conta duplicada."""
    form_data = {
        "nome_banco": "BANCO DUPLICADO",
        "agencia": "4321",
        "conta": "098765",
        "tipo": "Poupança",
        "saldo_inicial": 100.00,
    }
    auth_client.post("/contas/adicionar", data=form_data)
    response = auth_client.post(
        "/contas/adicionar", data=form_data, follow_redirects=True
    )

    assert response.status_code == 200
    assert "Você já possui uma conta com este banco" in response.data.decode("utf-8")


def test_update_bank_account(auth_client, app):
    """Testa a atualização de uma conta bancária."""
    with app.app_context():
        conta_original = Conta(
            usuario_id=1,
            nome_banco="BANCO A EDITAR",
            agencia="5555",
            conta="6666",
            tipo="Digital",
            saldo_inicial=100.00,
            saldo_atual=100.00,
            limite=Decimal("50.00"),
        )
        db.session.add(conta_original)
        db.session.commit()
        conta_id = conta_original.id

    response = auth_client.post(
        f"/contas/editar/{conta_id}",
        data={"limite": 250.75, "ativa": "y"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Conta bancária atualizada com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        conta_atualizada = db.session.get(Conta, conta_id)
        assert conta_atualizada is not None
        assert conta_atualizada.limite == Decimal("250.75")


def test_delete_account_successfully(auth_client, app):
    """Testa a exclusão bem-sucedida de uma conta válida."""
    with app.app_context():
        conta = Conta(
            usuario_id=1,
            nome_banco="BANCO A SER DELETADO",
            agencia="0000",
            conta="0000",
            tipo="Digital",
            saldo_inicial=0,
            saldo_atual=0,
        )
        db.session.add(conta)
        db.session.commit()
        conta_id = conta.id

    response = auth_client.post(f"/contas/excluir/{conta_id}", follow_redirects=True)

    assert response.status_code == 200
    assert "Conta bancária excluída com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        conta_deletada = db.session.get(Conta, conta_id)
        assert conta_deletada is None
