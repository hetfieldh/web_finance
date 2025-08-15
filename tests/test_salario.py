# tests/test_salario.py

from datetime import date

from app import db
from app.models.salario_item_model import SalarioItem
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento


def test_create_salario_item(auth_client, app):
    """Testa a criação de uma nova verba de salário."""
    form_data = {
        "nome": "SALARIO BASE",
        "tipo": "Provento",
        "descricao": "Salario mensal",
    }
    response = auth_client.post(
        "/salario/itens/adicionar", data=form_data, follow_redirects=True
    )
    assert response.status_code == 200
    assert "Item da folha adicionado com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        assert SalarioItem.query.filter_by(nome="SALARIO BASE").first() is not None


def test_create_folha_pagamento(auth_client):
    """Testa a criação de uma folha de pagamento."""
    form_data = {"mes_referencia": "2025-08", "data_recebimento": "2025-09-05"}
    response = auth_client.post(
        "/salario/lancamento/novo", data=form_data, follow_redirects=True
    )
    assert response.status_code == 200
    assert (
        "Folha de pagamento criada. Agora adicione as verbas."
        in response.data.decode("utf-8")
    )
    assert "Gerenciar Folha de 2025-08" in response.data.decode("utf-8")


def test_add_item_to_folha(auth_client, app):
    """Testa adicionar uma verba a uma folha de pagamento."""
    with app.app_context():
        item = SalarioItem(usuario_id=1, nome="VALE REFEICAO", tipo="Benefício")
        folha = SalarioMovimento(
            usuario_id=1, mes_referencia="2025-08", data_recebimento=date(2025, 9, 5)
        )
        db.session.add_all([item, folha])
        db.session.commit()
        folha_id = folha.id
        item_id = item.id

    form_data = {"salario_item_id": item_id, "valor": 600.00}
    response = auth_client.post(
        f"/salario/lancamento/{folha_id}/gerenciar",
        data=form_data,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Verba adicionada com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        assert SalarioMovimentoItem.query.count() == 1
