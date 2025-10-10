# app/utils.py

from datetime import date
from enum import Enum

from dateutil.relativedelta import relativedelta
from wtforms.validators import ValidationError


# Funções de validações
def date_is_not_future(form, field):
    if field.data and field.data > date.today():
        raise ValidationError("A data não pode ser no futuro.")


# Constantes STATUS
STATUS_PAGO = "Pago"
STATUS_RECEBIDO = "Recebido"
STATUS_PENDENTE = "Pendente"
STATUS_ATRASADO = "Atrasado"
STATUS_PARCIAL_PAGO = "Parcialmente Pago"
STATUS_PARCIAL_RECEBIDO = "Parcialmente Recebido"
STATUS_APROVADO = "Aprovado"
STATUS_REJEITADO = "Rejeitado"
STATUS_AMORTIZADO = "Amortizado"
STATUS_PREVISTO = "Previsto"

# Constantes NATUREZA
NATUREZA_RECEITA = "Receita"
NATUREZA_DESPESA = "Despesa"

# Constantes TIPO
TIPO_ENTRADA = "Entrada"
TIPO_SAIDA = "Saída"
TIPO_DEBITO = "Débito"
TIPO_CREDITO = "Crédito"
TIPO_FIXA = "Fixa"
TIPO_VARIAVEL = "Variável"
TIPO_PROVENTO = "Provento"
TIPO_DESCONTO = "Desconto"
TIPO_IMPOSTO = "Imposto"
TIPO_BENEFICIO = "Benefício"
TIPO_COMPRA = "Compra"
TIPO_ESTORNO = "Estorno"
TIPO_AJUSTE = "Ajuste"
TIPO_CORRENTE = "Corrente"
TIPO_DIGITAL = "Digital"
TIPO_POUPANCA = "Poupança"
TIPO_INVESTIMENTO = "Investimento"
TIPO_CAIXINHA = "Caixinha"
TIPO_DINHEIRO = "Dinheiro"
TIPO_FGTS = "FGTS"
TIPO_CARTAO_FISICO = "Cartão Físico"
TIPO_CARTAO_VR = "Cartão VR"
TIPO_CARTAO_VT = "Cartão VT"
TIPO_BOLETO = "Boleto"
TIPO_CHEQUE = "Cheque"
TIPO_OUTRO = "Outro"
TIPO_SAC = "SAC"
TIPO_PRICE = "Price"
TIPO_MOVIMENTACAO_SIMPLES = "simples"
TIPO_MOVIMENTACAO_TRANSFERENCIA = "transferencia"


# OPÇÕES PARA FORMULÁRIOS (SELECT CHOICES) USANDO ENUM
class FormChoices:
    class TipoConta(Enum):
        CORRENTE = TIPO_CORRENTE
        POUPANCA = TIPO_POUPANCA
        DIGITAL = TIPO_DIGITAL
        INVESTIMENTO = TIPO_INVESTIMENTO
        CAIXINHA = TIPO_CAIXINHA
        DINHEIRO = TIPO_DINHEIRO
        BENEFICIO = TIPO_BENEFICIO
        FGTS = TIPO_FGTS

    class TipoCrediario(Enum):
        CARTAO_FISICO = TIPO_CARTAO_FISICO
        CARTAO_VR = TIPO_CARTAO_VR
        CARTAO_VT = TIPO_CARTAO_VT
        BOLETO = TIPO_BOLETO
        CHEQUE = TIPO_CHEQUE
        OUTRO = TIPO_OUTRO

    class TipoAmortizacao(Enum):
        SAC = TIPO_SAC
        PRICE = TIPO_PRICE
        OUTRO = TIPO_OUTRO

    class NaturezaDespRec(Enum):
        RECEITA = NATUREZA_RECEITA
        DESPESA = NATUREZA_DESPESA

    class TipoCadastroDespRec(Enum):
        VARIAVEL = TIPO_VARIAVEL
        FIXA = TIPO_FIXA

    class TipoTransacao(Enum):
        CREDITO = TIPO_CREDITO
        DEBITO = TIPO_DEBITO

    class TipoSalarioItem(Enum):
        PROVENTO = TIPO_PROVENTO
        DESCONTO = TIPO_DESCONTO
        IMPOSTO = TIPO_IMPOSTO
        BENEFICIO = TIPO_BENEFICIO
        FGTS = TIPO_FGTS

    class StatusFatura(Enum):
        PENDENTE = STATUS_PENDENTE
        PAGO = STATUS_PAGO
        ATRASADO = STATUS_ATRASADO
        PARCIAL_PAGA = STATUS_PARCIAL_PAGO

    class StatusFinanciamento(Enum):
        PENDENTE = STATUS_PENDENTE
        PAGO = STATUS_PAGO
        ATRASADO = STATUS_ATRASADO
        AMORTIZADO = STATUS_AMORTIZADO

    class StatusDespesaReceita(Enum):
        PENDENTE = STATUS_PENDENTE
        PAGO = STATUS_PAGO
        RECEBIDO = STATUS_RECEBIDO
        ATRASADO = STATUS_ATRASADO

    class SalarioMovimento(Enum):
        PENDENTE = STATUS_PENDENTE
        PARCIAL_RECEBIDO = STATUS_PARCIAL_RECEBIDO
        RECEBIDO = STATUS_RECEBIDO

    class StatusSolicitacao(Enum):
        PENDENTE = STATUS_PENDENTE
        APROVADO = STATUS_APROVADO
        REJEITADO = STATUS_REJEITADO

    class TiposCrediarioGrupo(Enum):
        COMPRA = TIPO_COMPRA
        ESTORNO = TIPO_ESTORNO
        AJUSTE = TIPO_AJUSTE

    class TiposMovimentacaoBancaria(Enum):
        SIMPLES = TIPO_MOVIMENTACAO_SIMPLES
        TRANSFERENCIA = TIPO_MOVIMENTACAO_TRANSFERENCIA

    class DestinoCrediario(Enum):
        PROPRIO = "Próprio"
        OUTROS = "Outros"
        COLETIVO = "Coletivo"

    @classmethod
    def get_choices(cls, enum_class):
        return [("", "Selecione...")] + [
            (item.value, item.value) for item in enum_class
        ]


# CONFIGURAÇÃO DE TÍTULOS E CABEÇALHOS DAS PÁGINAS
PAGE_CONFIG = {
    # Main e Auth
    "main.dashboard": {"title": "Dashboard", "header": "Dashboard"},
    "auth.login": {"title": "Login", "header": "Acesso ao Sistema"},
    # Usuários
    "usuario.listar_usuarios": {"title": "Usuários", "header": "Usuários"},
    "usuario.adicionar_usuario": {
        "title": "Usuários",
        "header": "Usuário",
    },
    "usuario.editar_usuario": {"title": "Usuários", "header": "Usuário"},
    "usuario.perfil": {"title": "Usuários", "header": "Editar Perfil"},
    # Contas
    "conta.listar_contas": {"title": "Contas Bancárias", "header": "Contas Bancárias"},
    "conta.adicionar_conta": {
        "title": "Contas Bancárias",
        "header": "Contas Bancárias",
    },
    "conta.editar_conta": {"title": "Contas Bancárias", "header": "Editar Conta"},
    # Transações da Conta
    "conta_transacao.listar_tipos_transacao": {
        "title": "Contas Bancárias",
        "header": "Contas Bancárias",
    },
    "conta_transacao.adicionar_tipo_transacao": {
        "title": "Contas Bancárias",
        "header": "Contas Bancárias",
    },
    "conta_transacao.editar_tipo_transacao": {
        "title": "Contas Bancárias",
        "header": "Contas Bancárias",
    },
    # Movimentos da Conta
    "conta_movimento.listar_movimentacoes": {
        "title": "TR Bancárias",
        "header": "Contas Bancárias",
    },
    "conta_movimento.adicionar_movimentacao": {
        "title": "TR Bancárias",
        "header": "Contas Bancárias",
    },
    "conta_movimento.editar_movimentacao": {
        "title": "TR Bancárias",
        "header": "Contas Bancárias",
    },
    # Crediários
    "crediario.listar_crediarios": {
        "title": "Crediários",
        "header": "Crediários",
    },
    "crediario.adicionar_crediario": {
        "title": "Crediários",
        "header": "Crediários",
    },
    "crediario.editar_crediario": {"title": "Crediários", "header": "Crediários"},
    # Grupos de Crediário
    "crediario_grupo.listar_grupos_crediario": {
        "title": "Crediários",
        "header": "Crediários",
    },
    "crediario_grupo.adicionar_grupo_crediario": {
        "title": "Crediários",
        "header": "Crediários",
    },
    "crediario_grupo.editar_grupo_crediario": {
        "title": "Crediários",
        "header": "Crediários",
    },
    # Movimentos de Crediário
    "crediario_movimento.listar_movimentos_crediario": {
        "title": "TR Crediários",
        "header": "Crediários",
    },
    "crediario_movimento.adicionar_movimento_crediario": {
        "title": "TR Crediários",
        "header": "Crediários",
    },
    "crediario_movimento.editar_movimento_crediario": {
        "title": "TR Crediários",
        "header": "Crediários",
    },
    "crediario_movimento.detalhes_movimento": {
        "title": "TR Crediários",
        "header": "Crediários",
    },
    # Faturas de Crediário
    "crediario_fatura.listar_faturas": {
        "title": "Fatura Crediário",
        "header": "Crediários",
    },
    "crediario_fatura.visualizar_fatura": {
        "title": "Fatura Crediário",
        "header": "Crediários",
    },
    # Financiamentos
    "financiamento.listar_financiamentos": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    "financiamento.adicionar_financiamento": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    "financiamento.editar_financiamento": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    "financiamento.importar_parcelas": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    "financiamento.visualizar_parcelas": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    "financiamento.amortizar_financiamento": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    # Despesas e Receitas (Cadastros)
    "desp_rec.listar_cadastros": {
        "title": "Despesas e Receitas",
        "header": "Despesas e Receitas",
    },
    "desp_rec.adicionar_cadastro": {
        "title": "Despesas e Receitas",
        "header": "Despesas e Receitas",
    },
    "desp_rec.editar_cadastro": {
        "title": "Despesas e Receitas",
        "header": "Despesas e Receitas",
    },
    # Despesas e Receitas (Movimentos)
    "desp_rec_movimento.listar_movimentos": {
        "title": "TR Desp/Rec",
        "header": "Despesas e Receitas",
    },
    "desp_rec_movimento.gerar_previsao": {
        "title": "TR Desp/Rec",
        "header": "Despesas e Receitas",
    },
    "desp_rec_movimento.adicionar_lancamento_unico": {
        "title": "TR Desp/Rec",
        "header": "Despesas e Receitas",
    },
    "desp_rec_movimento.editar_movimento": {
        "title": "TR Desp/Rec",
        "header": "Despesas e Receitas",
    },
    # Salário
    "salario.listar_itens": {
        "title": "Salários",
        "header": "Salários",
    },
    "salario.adicionar_item": {
        "title": "Salários",
        "header": "Salários",
    },
    "salario.editar_item": {
        "title": "Salários",
        "header": "Salários",
    },
    "salario.listar_movimentos": {
        "title": "Salários",
        "header": "Salários",
    },
    "salario.novo_lancamento_folha": {
        "title": "Salários",
        "header": "Salários",
    },
    "salario.gerenciar_itens_folha": {
        "title": "Salários",
        "header": "Salários",
    },
    # Relatórios
    "extrato.extrato_bancario": {
        "title": "Extrato Bancário",
        "header": "Contas Bancárias",
    },
    "extrato_consolidado.extrato_consolidado": {
        "title": "Fluxo de Caixa Detalhado por Parcelas",
        "header": "Fluxo de Caixa Detalhado por Parcelas",
    },
    "fluxo_caixa.painel": {
        "title": "Fluxo de Caixa",
        "header": "Fluxo de Caixa",
    },
    # Painéis
    "pagamentos.painel": {
        "title": "Pagamentos",
        "header": "Painel de Pagamentos",
    },
    "recebimentos.painel": {
        "title": "Recebimentos",
        "header": "Painel de Recebimentos",
    },
    # Gráficos
    "graphics.view_graphics": {"title": "Gráficos", "header": "Resumo do Mês"},
    "graphics.resumo_financiamentos": {
        "title": "Gráficos",
        "header": "Resumo do Financiamento",
    },
    # Solicitações de Acesso
    "solicitacao.solicitar_acesso": {
        "title": "Solicitar Acesso",
        "header": "Solicitar Acesso ao Sistema",
    },
    "solicitacao.verificar_status": {
        "title": "Status Solicitação",
        "header": "Verificar Status da Solicitação",
    },
    "solicitacao.gerenciar_solicitacoes": {
        "title": "Usuários",
        "header": "Gerenciar Solicitações de Acesso",
    },
}
