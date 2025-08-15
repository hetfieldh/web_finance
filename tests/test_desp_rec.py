# tests/test_desp_rec.py

from datetime import date

from app import db
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento


def test_create_desp_rec(auth_client, app):
    form_data = {
        "nome": "CONTA DE LUZ",
        "natureza": "Despesa",
        "tipo": "Fixa",
        "dia_vencimento": 10,
    }
    response = auth_client.post(
        "/despesas_receitas/adicionar", data=form_data, follow_redirects=True
    )

    assert response.status_code == 200
    assert "Cadastro adicionado com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        cadastro = DespRec.query.filter_by(nome="CONTA DE LUZ").first()
        assert cadastro is not None
        assert cadastro.natureza == "Despesa"
        assert cadastro.dia_vencimento == 10


def test_create_duplicate_desp_rec_fails(auth_client, app):
    form_data = {
        "nome": "SALARIO MENSAL",
        "natureza": "Receita",
        "tipo": "Fixa",
        "dia_vencimento": 5,
    }
    auth_client.post("/despesas_receitas/adicionar", data=form_data)

    response = auth_client.post(
        "/despesas_receitas/adicionar", data=form_data, follow_redirects=True
    )

    assert response.status_code == 200
    assert (
        "Já existe um cadastro com este nome, natureza e tipo."
        in response.data.decode("utf-8")
    )
    with app.app_context():
        cadastros = DespRec.query.filter_by(nome="SALARIO MENSAL").all()
        assert len(cadastros) == 1


def test_update_desp_rec(auth_client, app):
    with app.app_context():
        cadastro = DespRec(
            usuario_id=1,
            nome="INTERNET",
            natureza="Despesa",
            tipo="Fixa",
            dia_vencimento=15,
            ativo=True,
        )
        db.session.add(cadastro)
        db.session.commit()
        cadastro_id = cadastro.id

    update_data = {
        "dia_vencimento": 20,
        "ativo": "y",
    }
    response = auth_client.post(
        f"/despesas_receitas/editar/{cadastro_id}",
        data=update_data,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Cadastro atualizado com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        cadastro_atualizado = db.session.get(DespRec, cadastro_id)
        assert cadastro_atualizado.dia_vencimento == 20
        assert cadastro_atualizado.ativo is True


def test_delete_desp_rec_fails_if_in_use(auth_client, app):
    with app.app_context():
        cadastro = DespRec(
            usuario_id=1, nome="ALUGUEL", natureza="Despesa", tipo="Fixa"
        )
        movimento = DespRecMovimento(
            usuario_id=1,
            despesa_receita=cadastro,
            data_vencimento=date.today(),
            valor_previsto=1500,
        )
        db.session.add_all([cadastro, movimento])
        db.session.commit()
        cadastro_id = cadastro.id

    response = auth_client.post(
        f"/despesas_receitas/excluir/{cadastro_id}", follow_redirects=True
    )

    assert response.status_code == 200
    assert (
        "Não é possível excluir este cadastro, pois existem lançamentos associados a ele."
        in response.data.decode("utf-8")
    )
    with app.app_context():
        assert db.session.get(DespRec, cadastro_id) is not None


def test_delete_desp_rec_successfully(auth_client, app):
    with app.app_context():
        cadastro = DespRec(
            usuario_id=1, nome="TAXA EXTRA", natureza="Despesa", tipo="Variável"
        )
        db.session.add(cadastro)
        db.session.commit()
        cadastro_id = cadastro.id

    response = auth_client.post(
        f"/despesas_receitas/excluir/{cadastro_id}", follow_redirects=True
    )

    assert response.status_code == 200
    assert "Cadastro excluído com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        assert db.session.get(DespRec, cadastro_id) is None
