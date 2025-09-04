# tests\conftest.py

import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app, db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.usuario_model import Usuario


@pytest.fixture(scope="module")
def test_app():
    config_overrides = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False,
        "SERVER_NAME": "localhost.local",
        "SECRET_KEY": "test-secret-key",
    }
    app = create_app(config_overrides=config_overrides)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture()
def new_user(test_app):
    with test_app.app_context():
        user = Usuario(
            nome="Test",
            sobrenome="User",
            login="testuser",
            email="test@example.com",
            precisa_alterar_senha=False,
        )
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture()
def new_desp_rec(test_app, new_user):
    with test_app.app_context():
        desp_rec = DespRec(
            usuario_id=new_user.id,
            nome="TESTE DE EXCLUSAO",
            natureza="Despesa",
            tipo="Fixa",
            dia_vencimento=15,
            ativo=True,
        )
        db.session.add(desp_rec)
        db.session.commit()
        yield desp_rec
        db.session.rollback()
        obj_to_delete = db.session.get(DespRec, desp_rec.id)
        if obj_to_delete:
            db.session.delete(obj_to_delete)
            db.session.commit()


@pytest.fixture()
def movimentos_fatura(test_app, new_user, new_crediario):
    with test_app.app_context():
        movimentos = [
            CrediarioMovimento(
                usuario_id=new_user.id,
                crediario_id=new_crediario.id,
                descricao="Compra A",
                valor=100.50,
                data=date(2025, 8, 1),
            ),
            CrediarioMovimento(
                usuario_id=new_user.id,
                crediario_id=new_crediario.id,
                descricao="Compra B",
                valor=50.00,
                data=date(2025, 8, 15),
            ),
            CrediarioMovimento(
                usuario_id=new_user.id,
                crediario_id=new_crediario.id,
                descricao="Compra C (mês anterior)",
                valor=25.00,
                data=date(2025, 7, 20),
            ),
        ]
        db.session.bulk_save_objects(movimentos)
        db.session.commit()
        yield movimentos
        db.session.rollback()
        for mov in movimentos:
            obj_to_delete = db.session.get(CrediarioMovimento, mov.id)
            if obj_to_delete:
                db.session.delete(obj_to_delete)
        db.session.commit()


@pytest.fixture()
def new_crediario(test_app, new_user):
    with test_app.app_context():
        crediario = Crediario(
            usuario_id=new_user.id,
            nome_crediario="Cartão Teste",
            tipo_crediario="Cartão Físico",
            limite_total=5000.00,
        )
        db.session.add(crediario)
        db.session.commit()
        yield crediario
        db.session.rollback()
        obj_to_delete = db.session.get(Crediario, crediario.id)
        if obj_to_delete:
            db.session.delete(obj_to_delete)
            db.session.commit()


@pytest.fixture()
def new_conta(test_app, new_user):
    with test_app.app_context():
        conta = Conta(
            usuario_id=new_user.id,
            nome_banco="BANCO TESTE",
            agencia="0001",
            conta="123456",
            tipo="Corrente",
            saldo_inicial=1000.00,
            saldo_atual=1000.00,
            limite=500.00,
        )
        db.session.add(conta)
        db.session.commit()
        yield conta
        db.session.rollback()
        obj_to_delete = db.session.get(Conta, conta.id)
        if obj_to_delete:
            db.session.delete(obj_to_delete)
            db.session.commit()


@pytest.fixture()
def new_movimento(test_app, new_user, new_conta, new_transacao):
    with test_app.app_context():
        new_conta.saldo_atual = Decimal("849.75")

        movimento = ContaMovimento(
            usuario_id=new_user.id,
            conta_id=new_conta.id,
            conta_transacao_id=new_transacao.id,
            data_movimento=date(2025, 9, 1),
            valor=Decimal("150.25"),
            descricao="MOVIMENTO PARA EXCLUIR",
        )

        db.session.add(movimento)
        db.session.commit()
        yield movimento

        db.session.rollback()
        obj_to_delete_mov = db.session.get(ContaMovimento, movimento.id)
        if obj_to_delete_mov:
            db.session.delete(obj_to_delete_mov)

        obj_to_delete_conta = db.session.get(Conta, new_conta.id)
        if obj_to_delete_conta:
            obj_to_delete_conta.saldo_atual = Decimal("1000.00")

        db.session.commit()


@pytest.fixture()
def new_transacao(test_app, new_user):
    with test_app.app_context():
        transacao = ContaTransacao(
            usuario_id=new_user.id, transacao_tipo="PAGAMENTO", tipo="Débito"
        )
        db.session.add(transacao)
        db.session.commit()
        yield transacao
        db.session.rollback()
        obj_to_delete = db.session.get(ContaTransacao, transacao.id)
        if obj_to_delete:
            db.session.delete(obj_to_delete)
            db.session.commit()


@pytest.fixture()
def new_desp_rec_with_movimento(test_app, new_user, new_desp_rec):
    with test_app.app_context():
        movimento = DespRecMovimento(
            usuario_id=new_user.id,
            desp_rec_id=new_desp_rec.id,
            data_vencimento=date(2025, 10, 15),
            valor_previsto=Decimal("200.00"),
            mes=10,
            ano=2025,
            status="Pendente",
        )
        db.session.add(movimento)
        db.session.commit()

        desp_rec_atual = db.session.get(type(new_desp_rec), new_desp_rec.id)
        db.session.refresh(desp_rec_atual)

        yield desp_rec_atual

        db.session.rollback()
        obj_to_delete = db.session.get(DespRecMovimento, movimento.id)
        if obj_to_delete:
            db.session.delete(obj_to_delete)
            db.session.commit()


@pytest.fixture()
def new_movimento_posterior(test_app, new_user, new_conta, new_movimento):
    with test_app.app_context():
        movimento_posterior = ContaMovimento(
            usuario_id=new_user.id,
            conta_id=new_conta.id,
            conta_transacao_id=1,
            data_movimento=date(2025, 9, 2),
            valor=Decimal("50.00"),
            descricao="COMPRA POSTERIOR",
        )
        db.session.add(movimento_posterior)
        db.session.commit()
        yield movimento_posterior

        db.session.rollback()
        obj_to_delete = db.session.get(ContaMovimento, movimento_posterior.id)
        if obj_to_delete:
            db.session.delete(obj_to_delete)
            db.session.commit()


@pytest.fixture()
def new_movimento_vinculado(test_app, new_user, new_conta, new_desp_rec):
    with test_app.app_context():
        pagamento = ContaMovimento(
            usuario_id=new_user.id,
            conta_id=new_conta.id,
            conta_transacao_id=1,
            data_movimento=date(2025, 10, 10),
            valor=Decimal("199.99"),
            descricao="PAGAMENTO VINCULADO",
        )
        db.session.add(pagamento)
        db.session.commit()

        despesa_movimento = DespRecMovimento(
            usuario_id=new_user.id,
            desp_rec_id=new_desp_rec.id,
            data_vencimento=date(2025, 10, 15),
            valor_previsto=Decimal("199.99"),
            mes=10,
            ano=2025,
            status="Pago",
            movimento_bancario_id=pagamento.id,
        )
        db.session.add(despesa_movimento)
        db.session.commit()

        yield pagamento

        db.session.rollback()
        obj_to_delete_desp = db.session.get(DespRecMovimento, despesa_movimento.id)
        if obj_to_delete_desp:
            db.session.delete(obj_to_delete_desp)

        obj_to_delete_pag = db.session.get(ContaMovimento, pagamento.id)
        if obj_to_delete_pag:
            db.session.delete(obj_to_delete_pag)

        db.session.commit()
