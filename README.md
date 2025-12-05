# Web Finance - Sistema de Gestão Financeira Pessoal

![Badge de Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Badge de Linguagem](https://img.shields.io/badge/python-3.9%2B-blue)
![Badge de Framework](https://img.shields.io/badge/flask-2.x-orange)
![Badge de Banco de Dados](https://img.shields.io/badge/database-PostgreSQL%20%7C%20MySQL-purple)

Web Finance é um sistema web completo para gestão e análise de finanças pessoais, desenvolvido para centralizar todas as informações financeiras de um usuário em um único lugar, oferecendo clareza, controle e previsibilidade.

---

## 🚀 Funcionalidades Principais

O sistema foi construído de forma modular, com uma gama completa de funcionalidades para uma gestão financeira 360°:

- **📊 Dashboard Interativo:** Painel principal com KPIs (Indicadores Chave de Desempenho) como saldos totais, receitas e despesas do mês, balanço mensal, saldos devedores, além de gráficos dinâmicos sobre a saúde financeira e alertas de contas a vencer/vencidas.
- **👤 Gestão de Usuários:** Sistema de autenticação seguro (login/logout), com solicitação de acesso para novos usuários e painel de gerenciamento (aprovação/rejeição) para administradores. Edição de perfil de usuário.
- **🏦 Contas Bancárias:** Cadastro e controle de múltiplas contas (Corrente, Poupança, Digital, Investimento, etc.). Lançamentos de débitos e créditos (movimentação tradicional) e transferências entre contas. Cadastro de tipos de transação personalizados.
- **💳 Crediários:** Gestão completa de cartões de crédito, cartões de benefícios (VR/VT), boletos e outros tipos de crediário. Lançamento de compras, estornos e ajustes, com parcelamento automático. Cadastro de Grupos de Crediário para categorização (ex: Alimentação, Transporte). Geração e visualização automática de faturas mensais, com cálculo de saldo anterior, total de gastos, pagamentos e saldo final.
- **💸 Financiamentos:** Cadastro e acompanhamento de financiamentos (SAC, Price, Outro). Geração (ou importação via CSV) e visualização de parcelas, com controle de status (Pendente, Pago, Atrasado, Amortizado). Funcionalidade de amortização de saldo devedor.
- **🧾 Despesas e Receitas:** Cadastro base de despesas e receitas (Fixas ou Variáveis). Lançamento de movimentos únicos ou geração de previsões de lançamentos recorrentes (ex: aluguel, salário) para meses futuros.
- **💰 Salário:** Cadastro de Itens de Salário (Proventos, Descontos, Impostos, Benefícios, FGTS). Lançamento facilitado de holerites mensais a partir dos itens pré-cadastrados, com cálculo automático de totais.
- **📈 Consultas e Relatórios:**
  - **Extrato Bancário:** Consulta detalhada de movimentações por conta e período.
  - **Fluxo de Caixa:** Projeção de saldos futuros com base em lançamentos previstos e realizados.
  - **Fluxo Detalhado:** Visão consolidada de todas as entradas e saídas (salários, receitas, despesas, faturas, financiamentos) em um determinado mês.
  - **Resumo Mensal:** Balanço simplificado de receitas, despesas e saldo do mês.
  - **Resumo Anual da Folha:** Tabela detalhada com todos os itens do holerite (Proventos, Descontos, etc.) totalizados por mês e no ano.
  - **Gastos Anuais por Grupo de Crediário:** Relatório anual que totaliza os gastos (líquido de estornos) por Grupo de Crediário, ordenado do maior para o menor, com resumo por Destino (Próprio, Outros, Coletivo).
- **⚙️ Painéis de Ação:**
  - **Painel de Pagamentos:** Centraliza todas as contas a pagar (Despesas, Faturas, Parcelas de Financiamento) de um mês específico, permitindo registrar pagamentos.
  - **Painel de Recebimentos:** Centraliza todas as contas a receber (Receitas, Salário, Benefícios) de um mês específico, permitindo registrar recebimentos.
- **🎨 Gráficos:** Visualização de dados financeiros através de gráficos (requer configuração/implementação adicional).

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído utilizando as seguintes tecnologias e padrões:

- **Backend:**
  - **Linguagem:** Python 3
  - **Framework:** Flask
  - **ORM:** SQLAlchemy com Flask-SQLAlchemy
  - **Migrations:** Flask-Migrate (Alembic)
  - **Autenticação:** Flask-Login
  - **Formulários:** Flask-WTF
- **Frontend:**
  - **Template Engine:** Jinja2
  - **Framework CSS:** Bootstrap 5 (via CDN no `base.html`)
  - **Estilização:** CSS customizado (`style.css`)
  - **Ícones:** Font Awesome (via CDN no `base.html`)
  - **Interatividade:** JavaScript Vanilla (com AJAX para requisições assíncronas)
  - **Gráficos:** Chart.js (via CDN no `base.html`)
  - **Seletores de Data:** Flatpickr (via CDN no `base.html`)
- **Banco de Dados:**
  - PostgreSQL (configuração padrão)
  - MySQL (suportado via SQLAlchemy, requer ajuste na `DATABASE_URL`)
- **Arquitetura:**
  - Padrão próximo ao MVC (Model-View-Controller adaptado ao Flask com Blueprints)
  - Estrutura em Camadas (Rotas/Views, Serviços, Modelos/Dados)
  - Application Factory Pattern (`create_app` em `app/__init__.py`)

---

## ⚙️ Como Executar o Projeto Localmente

Siga os passos abaixo para configurar e executar o projeto em seu ambiente de desenvolvimento.

### Pré-requisitos

- [Python 3.9+](https://www.python.org/)
- [PostgreSQL](https://www.postgresql.org/download/) ou [MySQL](https://www.mysql.com/downloads/)
- [Git](https://git-scm.com/)

### Passos de Instalação

1.  **Clone o repositório:**

    ```bash
    git clone [https://github.com/hetfieldh/web_finance.git](https://github.com/hetfieldh/web_finance.git)
    cd web_finance
    ```

2.  **Crie e ative o ambiente virtual:**

    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    .\venv\Scripts\activate

    # Ativar no Linux/Mac
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o banco de dados e as variáveis de ambiente:**
    - Crie um banco de dados no seu PostgreSQL ou MySQL (ex: `web_finance_db`).
    - Crie um arquivo chamado `.env` na raiz do projeto.
    - Copie o conteúdo abaixo para o arquivo `.env` e substitua com suas credenciais:

      ```ini
      SECRET_KEY='sua_chave_secreta_aqui_bem_longa_e_segura'

      # Exemplo para PostgreSQL (recomendado):
      DATABASE_URL='postgresql://SEU_USUARIO:SUA_SENHA@localhost:5432/web_finance_db'

      # Exemplo para MySQL (alternativa):
      # DATABASE_URL='mysql+mysqlconnector://SEU_USUARIO:SUA_SENHA@localhost:3306/web_finance_db'
      ```

    - **Importante:** Garanta que o driver apropriado (`psycopg2-binary` para PostgreSQL ou `mysql-connector-python` para MySQL) esteja listado no `requirements.txt` e instalado.

5.  **Aplique as migrações do banco de dados:**

    ```bash
    flask db upgrade
    ```

    _Este comando criará todas as tabelas necessárias no seu banco de dados._

6.  **Execute a aplicação:**
    ```bash
    flask run
    ```

Pronto! A aplicação estará rodando em `http://127.0.0.1:5000`. Acesse a rota `/solicitar-acesso` para criar sua conta inicial. Se for a primeira execução, o primeiro usuário registrado será automaticamente definido como administrador.

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT.
