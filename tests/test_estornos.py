# tests/test_estornos.py

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app import db
from app.models.conta_model import Conta
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_model import DespRec
from app.services.pagamento_service import registrar_pagamento
from app.services.recebimento_service import registrar_recebimento


def test_estornar_pagamento_com_sucesso(auth_client, app):
    """
    Testa se o estorno de um pagamento funciona corretamente.
    Um estorno de pagamento é um crédito, então sempre deve ser bem-sucedido.
    """
    with app.app_context():
        # 1. Setup: Criar conta, transação e um item de despesa
        conta = Conta(
            usuario_id=1,
            nome_banco="BANCO ESTORNO PAG",
            agencia="1111",
            conta="1111",
            tipo="Corrente",
            saldo_inicial=1000,
            saldo_atual=1000,
        )
        desp_rec = DespRec(
            usuario_id=1, nome="DESPESA PARA ESTORNO", natureza="Despesa", tipo="Fixa"
        )
        db.session.add_all([conta, desp_rec])
        db.session.commit()

        # Simula o formulário de pagamento
        form_pagamento = SimpleNamespace(
            conta_id=SimpleNamespace(data=conta.id),
            valor_pago=SimpleNamespace(data=Decimal("200.00")),
            data_pagamento=SimpleNamespace(data=date.today()),
            item_id=SimpleNamespace(data=1),  # Supondo que será o ID 1
            item_tipo=SimpleNamespace(data="Despesa"),
            item_descricao=SimpleNamespace(data="Pagamento Teste"),
        )
        registrar_pagamento(
            form_pagamento
        )  # Assume que DespRecMovimento com id 1 existe

        # Verifica o estado inicial após o pagamento
        assert conta.saldo_atual == Decimal("800.00")

    # 2. Ação: Realizar o estorno via rota
    response = auth_client.post(
        "/pagamentos/estornar",
        data={"item_id": 1, "item_tipo": "Despesa"},
        follow_redirects=True,
    )

    # 3. Asserts: Verificar o resultado
    assert response.status_code == 200
    assert "Pagamento estornado com sucesso!" in response.data.decode("utf-8")

    with app.app_context():
        conta_final = db.session.get(Conta, conta.id)
        assert conta_final.saldo_atual == Decimal(
            "1000.00"
        )  # Saldo deve ter sido restaurado


def test_estornar_recebimento_falha_por_saldo_insuficiente(auth_client, app):
    """
    Testa se o estorno de um recebimento falha se o saldo da conta for insuficiente.
    """
    with app.app_context():
        # 1. Setup: Conta com saldo baixo e um recebimento já registrado
        conta = Conta(
            usuario_id=1,
            nome_banco="BANCO ESTORNO REC",
            agencia="2222",
            conta="2222",
            tipo="Corrente",
            saldo_inicial=50,
            saldo_atual=50,
        )
        receita = DespRec(
            usuario_id=1, nome="RECEITA PARA ESTORNO", natureza="Receita", tipo="Fixa"
        )
        db.session.add_all([conta, receita])
        db.session.commit()

        form_recebimento = SimpleNamespace(
            conta_id=SimpleNamespace(data=conta.id),
            valor_recebido=SimpleNamespace(data=Decimal("500.00")),
            data_recebimento=SimpleNamespace(data=date.today()),
            item_id=SimpleNamespace(data=1),  # Supondo que será o ID 1
            item_tipo=SimpleNamespace(data="Receita"),
            item_descricao=SimpleNamespace(data="Recebimento Teste"),
        )
        registrar_recebimento(
            form_recebimento
        )  # Assume que DespRecMovimento com id 1 existe

        # Saldo após recebimento: 50 + 500 = 550
        assert conta.saldo_atual == Decimal("550.00")

        # Gasta o dinheiro para que o saldo fique insuficiente para o estorno
        conta.saldo_atual = Decimal("100.00")
        db.session.commit()

    # 2. Ação: Tentar estornar o recebimento de 500 com apenas 100 em conta
    response = auth_client.post(
        "/recebimentos/estornar",
        data={"item_id": 1, "item_tipo": "Receita"},
        follow_redirects=True,
    )

    # 3. Asserts: Verificar a falha
    assert response.status_code == 200
    assert "Estorno não permitido. Saldo insuficiente" in response.data.decode("utf-8")

    with app.app_context():
        conta_final = db.session.get(Conta, conta.id)
        assert conta_final.saldo_atual == Decimal("100.00")  # Saldo não deve ter mudado
