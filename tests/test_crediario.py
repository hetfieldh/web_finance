# tests/test_crediario.py

from datetime import date

from app import db
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento


def test_create_crediario(auth_client, app):
    form_data = {
        "nome_crediario": "CARTAO TESTE",
        "tipo_crediario": "Cartão Físico",
        "limite_total": 2000.00,
    }
    response = auth_client.post(
        "/crediarios/adicionar", data=form_data, follow_redirects=True
    )

    assert response.status_code == 200
    assert "Crediário adicionado com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        assert (
            Crediario.query.filter_by(nome_crediario="CARTAO TESTE").first() is not None
        )


def test_delete_crediario_fails_if_in_use(auth_client, app):
    """Testa a falha ao excluir um crediário com movimentos."""
    with app.app_context():
        crediario = Crediario(
            usuario_id=1,
            nome_crediario="USADO",
            tipo_crediario="Boleto",
            limite_total=1000,
        )
        movimento = CrediarioMovimento(
            usuario_id=1,
            crediario=crediario,
            data_compra=date(2025, 1, 1),
            valor_total_compra=100,
            descricao="teste",
            data_primeira_parcela=date(2025, 2, 1),
        )
        db.session.add_all([crediario, movimento])
        db.session.commit()
        crediario_id = crediario.id

    response = auth_client.post(
        f"/crediarios/excluir/{crediario_id}", follow_redirects=True
    )
    assert response.status_code == 200
    assert "Não é possível excluir este crediário" in response.data.decode("utf-8")
