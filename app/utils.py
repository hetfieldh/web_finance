# app/utils.py

from datetime import date

from dateutil.relativedelta import relativedelta

# Títulos das páginas e cabeçalho
PAGE_CONFIG = {
    # Main e Auth
    "main.dashboard": {"title": "Dashboard", "header": "Dashboard Principal"},
    "auth.login": {"title": "Login", "header": "Acesso ao Sistema"},
    # Usuários
    "usuario.listar_usuarios": {"title": "Usuários", "header": "Gerenciar Usuários"},
    "usuario.adicionar_usuario": {
        "title": "Usuários",
        "header": "Adicionar Usuário",
    },
    "usuario.editar_usuario": {"title": "Usuários", "header": "Editar Usuário"},
    "usuario.perfil": {"title": "Usuários", "header": "Editar Perfil"},
    # Contas
    "conta.listar_contas": {"title": "Contas Bancárias", "header": "Contas Bancárias"},
    "conta.adicionar_conta": {
        "title": "Contas Bancárias",
        "header": "Adicionar Conta",
    },
    "conta.editar_conta": {"title": "Contas Bancárias", "header": "Editar Conta"},
    # Transações da Conta
    "conta_transacao.listar_transacoes": {
        "title": "Contas Bancárias",
        "header": "Tipos de Transação",
    },
    "conta_transacao.adicionar_transacao": {
        "title": "Contas Bancárias",
        "header": "Adicionar Tipo de Transação",
    },
    "conta_transacao.editar_transacao": {
        "title": "Contas Bancárias",
        "header": "Editar Tipo de Transação",
    },
    # Movimentos da Conta
    "conta_movimento.listar_movimentos": {
        "title": "TR Bancárias",
        "header": "Movimentos da Conta",
    },
    "conta_movimento.adicionar_movimento": {
        "title": "TR Bancárias",
        "header": "Adicionar Movimento",
    },
    "conta_movimento.editar_movimento": {
        "title": "TR Bancárias",
        "header": "Editar Movimento",
    },
    # Crediários
    "crediario.listar_crediarios": {
        "title": "Crediários",
        "header": "Crediários",
    },
    "crediario.adicionar_crediario": {
        "title": "Crediários",
        "header": "Adicionar Crediário",
    },
    "crediario.editar_crediario": {"title": "Crediários", "header": "Editar Crediário"},
    # Grupos de Crediário
    "crediario_grupo.listar_grupos": {
        "title": "Crediários",
        "header": "Grupos de Compra",
    },
    "crediario_grupo.adicionar_grupo": {
        "title": "Crediários",
        "header": "Adicionar Grupo de Compra",
    },
    "crediario_grupo.editar_grupo": {
        "title": "Crediários",
        "header": "Editar Grupo de Compra",
    },
    # Movimentos de Crediário
    "crediario_movimento.listar_movimentos": {
        "title": "TR Crediários",
        "header": "Lançamentos de Crediário",
    },
    "crediario_movimento.adicionar_movimento": {
        "title": "TR Crediários",
        "header": "Adicionar Lançamento",
    },
    "crediario_movimento.editar_movimento": {
        "title": "TR Crediários",
        "header": "Editar Lançamento",
    },
    "crediario_movimento.detalhes_movimento": {
        "title": "TR Crediários",
        "header": "Detalhes do Lançamento",
    },
    # Faturas de Crediário
    "crediario_fatura.listar_faturas": {
        "title": "Fatura Crediário",
        "header": "Faturas",
    },
    "crediario_fatura.visualizar_fatura": {
        "title": "Fatura Crediário",
        "header": "Detalhes da Fatura",
    },
    # Financiamentos
    "financiamento.listar_financiamentos": {
        "title": "Financiamentos",
        "header": "Financiamentos",
    },
    "financiamento.adicionar_financiamento": {
        "title": "Financiamentos",
        "header": "Adicionar Financiamento",
    },
    "financiamento.editar_financiamento": {
        "title": "Financiamentos",
        "header": "Editar Financiamento",
    },
    "financiamento.importar_parcelas": {
        "title": "Financiamentos",
        "header": "Importar Parcelas",
    },
    "financiamento.visualizar_parcelas": {
        "title": "Financiamentos",
        "header": "Detalhes do Financiamento",
    },
    "financiamento.amortizar_financiamento": {
        "title": "Financiamentos",
        "header": "Amortizar Financiamento",
    },
    # Despesas e Receitas (Cadastros)
    "desp_rec.listar_cadastros": {
        "title": "Despesas e Receitas",
        "header": "Cadastros de Despesas e Receitas",
    },
    "desp_rec.adicionar_cadastro": {
        "title": "Despesas e Receitas",
        "header": "Adicionar Despesa/Receita",
    },
    "desp_rec.editar_cadastro": {
        "title": "Despesas e Receitas",
        "header": "Editar Despesa/Receita",
    },
    # Despesas e Receitas (Movimentos)
    "desp_rec_movimento.listar_movimentos": {
        "title": "TR Despesas e Receitas",
        "header": "Lançamentos Previstos",
    },
    "desp_rec_movimento.gerar_previsao": {
        "title": "TR Despesas e Receitas",
        "header": "Gerar Previsão de Lançamentos",
    },
    "desp_rec_movimento.adicionar_lancamento_unico": {
        "title": "TR Despesas e Receitas",
        "header": "Adicionar Lançamento Único",
    },
    "desp_rec_movimento.editar_lancamento": {
        "title": "TR Despesas e Receitas",
        "header": "Editar Lançamento",
    },
    # Salário
    "salario.listar_itens_salario": {
        "title": "Salários",
        "header": "Itens de Salário",
    },
    "salario.adicionar_item_salario": {
        "title": "Salários",
        "header": "Adicionar Item ao Salário",
    },
    "salario.editar_item_salario": {
        "title": "Salários",
        "header": "Editar Item do Salário",
    },
    "salario.listar_movimentos_salario": {
        "title": "Salários",
        "header": "Recebimentos de Salário",
    },
    "salario.adicionar_movimento_salario": {
        "title": "Salários",
        "header": "Adicionar Recebimento de Salário",
    },
    "salario.gerenciar_itens_movimento": {
        "title": "Salários",
        "header": "Gerenciar Itens do Recebimento",
    },
    # Relatórios e Painéis
    "extrato.extrato_bancario": {
        "title": "Extrato Bancário",
        "header": "Extrato Bancário",
    },
    "extrato_consolidado.extrato_consolidado": {
        "title": "Extrato Movimentos Detalhado",
        "header": "Extrato Consolidado de Movimentos",
    },
    "pagamentos.painel_pagamentos": {
        "title": "Pagamentos",
        "header": "Painel de Pagamentos",
    },
    "recebimentos.painel_recebimentos": {
        "title": "Recebimentos",
        "header": "Painel de Recebimentos",
    },
    "fluxo_caixa.painel_fluxo_caixa": {
        "title": "Fluxo de Caixa",
        "header": "Fluxo de Caixa",
    },
    "graphics.view_graphics": {"title": "Gráficos", "header": "Gráficos"},
    "graphics.resumo_financiamentos": {"title": "Gráficos", "header": "Gráficos"},
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


def gerar_opcoes_mes_ano(meses_passados=12, meses_futuros=12, incluir_selecione=True):
    hoje = date.today()
    nomes_meses_ptbr = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    opcoes = []
    # Gera meses desde o passado até o futuro
    for i in range(-meses_passados, meses_futuros + 1):
        data_ref = hoje + relativedelta(months=i)
        value = data_ref.strftime("%Y-%m")
        label = f"{nomes_meses_ptbr[data_ref.month]}/{data_ref.year}"
        opcoes.append((value, label))

    # Ordena as opções em ordem decrescente (mais recente primeiro)
    opcoes_ordenadas = sorted(opcoes, key=lambda x: x[0], reverse=True)

    if incluir_selecione:
        return [("", "Selecione um período...")] + opcoes_ordenadas

    return opcoes_ordenadas
