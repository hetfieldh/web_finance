# tests\test_services.py

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app import create_app, db
from app.models.conta_model import Conta
from app.models.conta_transacao_model import ContaTransacao
from app.services import (
    conta_service,
    crediario_movimento_service,
    crediario_service,
    desp_rec_service,
    movimento_service,
    usuario_service,
)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
@patch("app.services.usuario_service.current_app")
@patch("app.services.usuario_service.current_user")
@patch("app.services.usuario_service.db")
def test_criar_novo_usuario(mock_db, mock_current_user, mock_current_app, test_app):
    mock_form = MagicMock()
    mock_form.nome.data = "New"
    mock_form.sobrenome.data = "User"
    mock_form.email.data = "new@example.com"
    mock_form.login.data = "newuser"
    mock_form.is_admin.data = False
    mock_form.senha.data = "newpassword"
    mock_current_user.login = "admin_test"
    with test_app.app_context():
        success, message, new_user = usuario_service.criar_novo_usuario(mock_form)
    assert success is True
    assert message == "Usuário adicionado com sucesso!"
    assert new_user is not None
    assert new_user.login == "newuser"
    assert mock_db.session.add.call_count == 14
    mock_db.session.flush.assert_called_once()
    mock_db.session.commit.assert_called_once()
    mock_current_app.logger.info.assert_called_once()


@patch("app.services.conta_service.current_user", new_callable=MagicMock)
@patch("app.services.conta_service.db")
def test_criar_conta(mock_db, mock_current_user, new_user):
    mock_form = MagicMock()
    mock_form.nome_banco.data = "Banco Teste"
    mock_form.agencia.data = "0001"
    mock_form.conta.data = "12345-6"
    mock_form.tipo.data = "Corrente"
    mock_form.saldo_inicial.data = 1000.50
    mock_form.limite.data = 500.0
    mock_current_user.id = new_user.id
    mock_current_user.login = new_user.login
    success, message = conta_service.criar_conta(mock_form)
    assert success is True
    assert message == "Conta bancária adicionada com sucesso!"
    mock_db.session.add.assert_called_once()
    added_conta = mock_db.session.add.call_args[0][0]
    assert added_conta.nome_banco == "BANCO TESTE"
    assert added_conta.tipo == "Corrente"
    assert added_conta.usuario_id == new_user.id
    mock_db.session.commit.assert_called_once()


@patch("app.services.desp_rec_service.current_user", new_callable=MagicMock)
@patch("app.services.desp_rec_service.db")
def test_criar_cadastro_despesa_receita(mock_db, mock_current_user, new_user):
    mock_form = MagicMock()
    mock_form.nome.data = "Conta de Luz"
    mock_form.natureza.data = "Despesa"
    mock_form.tipo.data = "Fixa"
    mock_form.dia_vencimento.data = 10
    mock_form.ativo.data = True
    mock_current_user.id = new_user.id
    mock_current_user.login = new_user.login
    success, message = desp_rec_service.criar_cadastro(mock_form)
    assert success is True
    assert message == "Cadastro adicionado com sucesso!"
    mock_db.session.add.assert_called_once()
    added_item = mock_db.session.add.call_args[0][0]
    assert added_item.nome == "CONTA DE LUZ"
    assert added_item.natureza == "Despesa"
    assert added_item.tipo == "Fixa"
    assert added_item.usuario_id == new_user.id
    mock_db.session.commit.assert_called_once()


@patch("app.services.desp_rec_service.current_user", new_callable=MagicMock)
@patch("app.services.desp_rec_service.db")
def test_excluir_cadastro_com_sucesso(
    mock_db, mock_current_user, new_user, new_desp_rec
):
    cadastro_id_para_excluir = new_desp_rec.id
    mock_current_user.id = new_user.id
    mock_current_user.login = new_user.login
    mock_db.session.query.return_value.filter_by.return_value.first_or_404.return_value = (
        new_desp_rec
    )
    type(new_desp_rec).movimentos = []
    success, message = desp_rec_service.excluir_cadastro_por_id(
        cadastro_id_para_excluir
    )
    assert success is True
    assert message == "Cadastro excluído com sucesso!"
    mock_db.session.delete.assert_called_once_with(new_desp_rec)
    mock_db.session.commit.assert_called_once()


@patch("app.services.desp_rec_service.current_user", new_callable=MagicMock)
@patch("app.services.desp_rec_service.db")
def test_gerar_previsoes_com_sucesso(
    mock_db, mock_current_user, new_user, new_desp_rec, test_app
):
    mock_form = MagicMock()
    mock_form.desp_rec_id.data = new_desp_rec.id
    mock_form.valor_previsto.data = 150.00
    mock_form.data_inicio.data = date(2025, 1, 1)
    mock_form.numero_meses.data = 3
    mock_form.descricao.data = "Previsão de Teste"
    mock_current_user.id = new_user.id
    mock_db.session.get.return_value = new_desp_rec
    with test_app.app_context():
        success, message = desp_rec_service.gerar_previsoes(mock_form)
    assert success is True
    assert message == "3 lançamentos previstos gerados com sucesso!"
    mock_db.session.bulk_save_objects.assert_called_once()
    mock_db.session.commit.assert_called_once()
    saved_objects = mock_db.session.bulk_save_objects.call_args[0][0]
    assert len(saved_objects) == 3


@patch("app.services.crediario_service.current_user", new_callable=MagicMock)
@patch("app.services.crediario_service.db")
def test_criar_crediario(mock_db, mock_current_user, new_user):
    mock_form = MagicMock()
    mock_form.nome_crediario.data = "Cartão Principal"
    mock_form.tipo_crediario.data = "Cartão de Crédito"
    mock_form.limite_total.data = 2500.00
    mock_form.identificador_final.data = "1234"
    mock_current_user.id = new_user.id
    mock_current_user.login = new_user.login
    success, message = crediario_service.criar_crediario(mock_form)
    assert success is True
    assert message == "Crediário adicionado com sucesso!"
    mock_db.session.add.assert_called_once()
    added_item = mock_db.session.add.call_args[0][0]
    assert added_item.nome_crediario == "CARTÃO PRINCIPAL"
    assert added_item.tipo_crediario == "Cartão de Crédito"
    assert added_item.limite_total == 2500.00
    assert added_item.usuario_id == new_user.id
    mock_db.session.commit.assert_called_once()


@patch("app.services.movimento_service.current_user", new_callable=MagicMock)
@patch("app.services.movimento_service.db")
def test_registrar_movimento_debito(mock_db, mock_current_user, new_user, new_conta):
    mock_form = MagicMock()
    mock_form.tipo_operacao.data = "simples"
    mock_form.conta_id.data = new_conta.id
    mock_form.conta_transacao_id.data = 1
    mock_form.valor.data = Decimal("150.25")
    mock_form.data_movimento.data = date(2025, 9, 1)
    mock_form.descricao.data = "PAGAMENTO BOLETO"

    saldo_inicial = new_conta.saldo_atual

    mock_current_user.id = new_user.id

    mock_transacao = MagicMock(spec=ContaTransacao)
    mock_transacao.tipo = "Débito"

    def get_side_effect(model, obj_id):
        if model is Conta and obj_id == new_conta.id:
            return new_conta
        if model is ContaTransacao and obj_id == mock_form.conta_transacao_id.data:
            return mock_transacao
        return None

    mock_db.session.get.side_effect = get_side_effect

    success, message = movimento_service.registrar_movimento(mock_form)

    assert success is True
    assert message == "Movimentação registrada com sucesso!"

    mock_db.session.add.assert_called_once()

    added_movimento = mock_db.session.add.call_args[0][0]
    assert added_movimento.valor == Decimal("150.25")
    assert added_movimento.descricao == "PAGAMENTO BOLETO"

    saldo_esperado = saldo_inicial - Decimal("150.25")
    assert new_conta.saldo_atual == saldo_esperado

    mock_db.session.commit.assert_called_once()


@patch("app.services.movimento_service.current_user", new_callable=MagicMock)
@patch("app.services.movimento_service.db.session")
@patch("app.services.movimento_service.DespRecMovimento")
@patch("app.services.movimento_service.FinanciamentoParcela")
@patch("app.services.movimento_service.SalarioMovimento")
def test_excluir_movimento_com_sucesso(
    mock_salario_mov,
    mock_fin_parc,
    mock_desp_rec,
    mock_session,
    mock_current_user,
    new_user,
    new_conta,
    new_movimento,
):
    movimento_id_para_excluir = new_movimento.id
    saldo_antes_da_exclusao = new_conta.saldo_atual

    mock_current_user.id = new_user.id

    new_movimento.usuario_id = new_user.id

    transacao_real = ContaTransacao(tipo="Débito")
    new_movimento.tipo_transacao = transacao_real

    new_movimento.valor = Decimal("150.25")

    mock_desp_rec.query.filter_by.return_value.first.return_value = None
    mock_fin_parc.query.filter_by.return_value.first.return_value = None
    mock_salario_mov.query.filter.return_value.first.return_value = None

    mock_mov_query = MagicMock()
    mock_mov_query.filter_by.return_value.first_or_404.return_value = new_movimento
    mock_mov_query.filter.return_value.count.return_value = 0

    with patch("app.services.movimento_service.ContaMovimento.query", mock_mov_query):
        mock_session.get.return_value = new_conta

        success, message = movimento_service.excluir_movimento(
            movimento_id_para_excluir
        )

    assert success is True
    assert message == "Movimentação excluída com sucesso!"

    mock_session.delete.assert_called_once_with(new_movimento)

    saldo_esperado = saldo_antes_da_exclusao + new_movimento.valor
    assert new_conta.saldo_atual == saldo_esperado

    mock_session.commit.assert_called_once()


@patch("app.services.desp_rec_service.current_user", new_callable=MagicMock)
@patch("app.services.desp_rec_service.db.session")
def test_excluir_cadastro_com_movimentos_falha(
    mock_session, mock_current_user, new_user, new_desp_rec_with_movimento
):
    desp_rec_com_movimento = new_desp_rec_with_movimento
    cadastro_id = desp_rec_com_movimento.id

    mock_current_user.id = new_user.id

    mock_query = mock_session.query.return_value
    mock_query.filter_by.return_value.first_or_404.return_value = desp_rec_com_movimento

    success, message = desp_rec_service.excluir_cadastro_por_id(cadastro_id)

    assert success is False
    assert "existem lançamentos associados a ele" in message

    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


@patch("app.services.movimento_service.current_user", new_callable=MagicMock)
def test_excluir_movimento_com_movimento_posterior_falha(
    mock_current_user,
    new_user,
    new_conta,
    new_movimento,
    new_movimento_posterior,
    test_app,
):
    movimento_id_para_excluir = new_movimento.id

    mock_current_user.id = new_user.id

    with test_app.app_context():
        success, message = movimento_service.excluir_movimento(
            movimento_id_para_excluir
        )

    assert success is False
    assert "existem lançamentos posteriores na mesma conta" in message


@patch("app.services.movimento_service.current_user", new_callable=MagicMock)
def test_excluir_movimento_com_vinculo_falha(
    mock_current_user, new_user, new_movimento_vinculado, test_app
):
    movimento_id_para_excluir = new_movimento_vinculado.id

    mock_current_user.id = new_user.id

    with test_app.app_context():
        success, message = movimento_service.excluir_movimento(
            movimento_id_para_excluir
        )

    assert success is False
    assert "está vinculada a um pagamento ou recebimento" in message
