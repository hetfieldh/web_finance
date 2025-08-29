# app/utils.py

from datetime import date
from enum import Enum

from dateutil.relativedelta import relativedelta

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

    @classmethod
    def get_choices(cls, enum_class):
        return [("", "Selecione...")] + [
            (item.value, item.value) for item in enum_class
        ]


# CONFIGURAÇÃO DE TÍTULOS E CABEÇALHOS DAS PÁGINAS
PAGE_CONFIG = {
    # Main e Auth
    "main.dashboard": {"title": "Dashboard", "header": "Dashboard do Resumo Mensal"},
    "auth.login": {"title": "Login", "header": "Acesso ao Sistema"},
    # Usuários
    "usuario.listar_usuarios": {"title": "Usuários", "header": "Gerenciar Usuários"},
    "usuario.adicionar_usuario": {"title": "Usuários", "header": "Adicionar Usuário",},
    "usuario.editar_usuario": {"title": "Usuários", "header": "Editar Usuário"},
    "usuario.perfil": {"title": "Usuários", "header": "Editar Perfil"},
    # Contas
    "conta.listar_contas": {"title": "Contas Bancárias", "header": "Contas Bancárias"},
    "conta.adicionar_conta": {"title": "Contas Bancárias", "header": "Adicionar Conta",},
    "conta.editar_conta": {"title": "Contas Bancárias", "header": "Editar Conta"},
    # Transações da Conta
    "conta_transacao.listar_tipos_transacao": {"title": "Contas Bancárias", "header": "Tipos de Transação",},
    "conta_transacao.adicionar_tipo_transacao": {"title": "Contas Bancárias", "header": "Adicionar Tipo de Transação",},
    "conta_transacao.editar_tipo_transacao": {"title": "Contas Bancárias", "header": "Editar Tipo de Transação",},
    # Movimentos da Conta
    "conta_movimento.listar_movimentacoes": {"title": "TR Bancárias", "header": "Movimentos da Conta",},
    "conta_movimento.adicionar_movimentacao": {"title": "TR Bancárias", "header": "Adicionar Movimento",},
    "conta_movimento.editar_movimentacao": {"title": "TR Bancárias", "header": "Editar Movimento",},
    # Crediários
    "crediario.listar_crediarios": {"title": "Crediários", "header": "Crediários",},
    "crediario.adicionar_crediario": {"title": "Crediários", "header": "Adicionar Crediário",},
    "crediario.editar_crediario": {"title": "Crediários", "header": "Editar Crediário"},
    # Grupos de Crediário
    "crediario_grupo.listar_grupos_crediario": {"title": "Crediários", "header": "Grupos de Compra",},
    "crediario_grupo.adicionar_grupo_crediario": {"title": "Crediários", "header": "Adicionar Grupo de Compra",},
    "crediario_grupo.editar_grupo_crediario": {"title": "Crediários", "header": "Editar Grupo de Compra",},
    # Movimentos de Crediário
    "crediario_movimento.listar_movimentos_crediario": {"title": "TR Crediários", "header": "Lançamentos de Crediário",},
    "crediario_movimento.adicionar_movimento_crediario": {"title": "TR Crediários", "header": "Adicionar Lançamento",},
    "crediario_movimento.editar_movimento_crediario": {"title": "TR Crediários", "header": "Editar Lançamento",},
    "crediario_movimento.detalhes_movimento": {"title": "TR Crediários", "header": "Detalhes do Lançamento",},
    # Faturas de Crediário
    "crediario_fatura.listar_faturas": {"title": "Fatura Crediário", "header": "Faturas",},
    "crediario_fatura.visualizar_fatura": {"title": "Fatura Crediário", "header": "Detalhes da Fatura",},
    # Financiamentos
    "financiamento.listar_financiamentos": {"title": "Financiamentos", "header": "Financiamentos",},
    "financiamento.adicionar_financiamento": {"title": "Financiamentos", "header": "Adicionar Financiamento",},
    "financiamento.editar_financiamento": {"title": "Financiamentos", "header": "Editar Financiamento",},
    "financiamento.importar_parcelas": {"title": "Financiamentos", "header": "Importar Parcelas",},
    "financiamento.visualizar_parcelas": {"title": "Financiamentos", "header": "Detalhes do Financiamento",},
    "financiamento.amortizar_financiamento": {"title": "Financiamentos", "header": "Amortizar Financiamento",},
    # Despesas e Receitas (Cadastros)
    "desp_rec.listar_cadastros": {"title": "Despesas e Receitas", "header": "Cadastros de Despesas e Receitas",},
    "desp_rec.adicionar_cadastro": {"title": "Despesas e Receitas", "header": "Adicionar Despesa/Receita",},
    "desp_rec.editar_cadastro": {"title": "Despesas e Receitas", "header": "Editar Despesa/Receita",},
    # Despesas e Receitas (Movimentos)
    "desp_rec_movimento.listar_movimentos": {"title": "TR Desp/Rec", "header": "Lançamentos Previstos",},
    "desp_rec_movimento.gerar_previsao": {"title": "TR Desp/Rec", "header": "Gerar Previsão de Lançamentos",},
    "desp_rec_movimento.adicionar_lancamento_unico": {"title": "TR Desp/Rec", "header": "Adicionar Lançamento Único",},
    "desp_rec_movimento.editar_movimento": {"title": "TR Desp/Rec", "header": "Editar Lançamento",},
    # Salário
    "salario.listar_itens": {"title": "Salários", "header": "Itens de Salário",},
    "salario.adicionar_item": {"title": "Salários", "header": "Adicionar Item de Salário",},
    "salario.editar_item": {"title": "Salários", "header": "Editar Item de Salário",},
    "salario.listar_movimentos": {"title": "Salários", "header": "Recebimentos Cadastrados",},
    "salario.novo_lancamento_folha": {"title": "Salários", "header": "Adicionar Recebimento de Salário",},
    "salario.gerenciar_itens_folha": {"title": "Salários", "header": "Gerenciar Itens do Recebimento",},
    # Relatórios
    "extrato.extrato_bancario": {"title": "Extrato Bancário", "header": "Extrato Bancário",},
    "extrato_consolidado.extrato_consolidado": {"title": "Extrato Detalhado", "header": "Extrato Detalhado",},
    "fluxo_caixa.painel": {"title": "Fluxo de Caixa", "header": "Fluxo de Caixa",},
    # Painéis
    "pagamentos.painel": {"title": "Pagamentos", "header": "Painel de Pagamentos",},
    "recebimentos.painel": {"title": "Recebimentos", "header": "Painel de Recebimentos",},
    # Gráficos
    "graphics.view_graphics": {"title": "Gráficos", "header": "Resumo do Mês"},
    "graphics.resumo_financiamentos": {"title": "Gráficos", "header": "Resumo do Financiamento"},
    # Solicitações de Acesso
    "solicitacao.solicitar_acesso": {"title": "Solicitar Acesso", "header": "Solicitar Acesso ao Sistema",},
    "solicitacao.verificar_status": {"title": "Status Solicitação", "header": "Verificar Status da Solicitação",},
    "solicitacao.gerenciar_solicitacoes": {"title": "Usuários", "header": "Gerenciar Solicitações de Acesso",},
}

