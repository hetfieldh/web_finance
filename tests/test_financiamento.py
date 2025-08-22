# tests/test_financiamento.py

import io
from datetime import date

from app import db
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela


def test_create_financiamento_and_redirect_to_import(auth_client, app):
    """Testa a criação do financiamento principal e o redirecionamento para a importação."""
    with app.app_context():
        from app.models.conta_model import Conta

        conta = Conta(
            usuario_id=1,
            nome_banco="BANCO FINANC",
            agencia="1234",
            conta="5678",
            tipo="Corrente",
            saldo_inicial=0,
            saldo_atual=0,
        )
        db.session.add(conta)
        db.session.commit()

    form_data = {
        "nome_financiamento": "FINANCIAMENTO CASA",
        "conta_id": 1,
        "valor_total_financiado": 200000.00,
        "taxa_juros_anual": 9.5,
        "data_inicio": "2025-01-01",
        "prazo_meses": 360,
        "tipo_amortizacao": "SAC",
    }
    response = auth_client.post(
        "/financiamentos/adicionar", data=form_data, follow_redirects=True
    )

    assert response.status_code == 200
    assert "Financiamento principal criado com sucesso!" in response.data.decode(
        "utf-8"
    )
    assert "Importar Parcelas do Financiamento" in response.data.decode("utf-8")


def test_import_parcelas_successfully(auth_client, app):
    """Testa o upload bem-sucedido de um CSV de parcelas."""
    with app.app_context():
        from app.models.conta_model import Conta

        conta = Conta(
            usuario_id=1,
            nome_banco="BANCO FINANC",
            agencia="1234",
            conta="5678",
            tipo="Corrente",
            saldo_inicial=0,
            saldo_atual=0,
        )
        financiamento = Financiamento(
            usuario_id=1,
            conta=conta,
            nome_financiamento="FINANC TESTE CSV",
            valor_total_financiado=1000,
            saldo_devedor_atual=1000,
            taxa_juros_anual=10,
            data_inicio=date(2025, 1, 1),
            prazo_meses=2,
            tipo_amortizacao="SAC",
        )
        db.session.add_all([conta, financiamento])
        db.session.commit()
        financiamento_id = financiamento.id

    # CORREÇÃO: CSV atualizado para o formato de 15 colunas
    csv_content = (
        "numero_parcela,data_vencimento,valor_principal,valor_juros,valor_seguro,valor_seguro_2,valor_seguro_3,valor_taxas,multa,mora,ajustes,valor_total_previsto,saldo_devedor,data_pagamento,valor_pago,observacoes\n"
        "1,2025-02-01,500.00,8.33,10,0,0,5,0,0,0,523.33,500.00,2025-02-01,523.33,\n"
        "2,2025-03-01,500.00,4.17,10,0,0,5,0,0,0,519.17,0.00,,,Parcela Pendente"
    )
    csv_file = io.BytesIO(csv_content.encode("utf-8"))

    response = auth_client.post(
        f"/financiamentos/{financiamento_id}/importar",
        data={"csv_file": (csv_file, "parcelas.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "2 parcelas importadas com sucesso!" in response.data.decode("utf-8")
    with app.app_context():
        assert FinanciamentoParcela.query.count() == 2
