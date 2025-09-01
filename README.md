# Web Finance - Sistema de Gestão Financeira Pessoal

![Badge de Status](https://img.shields.io/badge/status-conclu%C3%ADdo-green)
![Badge de Linguagem](https://img.shields.io/badge/python-3.9%2B-blue)
![Badge de Framework](https://img.shields.io/badge/flask-2.x-orange)

Web Finance é um sistema web completo para gestão e análise de finanças pessoais, desenvolvido para centralizar todas as informações financeiras de um usuário em um único lugar, oferecendo clareza, controle e previsibilidade.

---

## 🚀 Funcionalidades Principais

O sistema foi construído de forma modular, com uma gama completa de funcionalidades para uma gestão financeira 360°:

* **📊 Dashboard Interativo:** Painel principal com KPIs e gráficos dinâmicos sobre a saúde financeira.
* **👤 Gestão de Usuários:** Sistema de autenticação seguro, com solicitação de acesso e painel de gerenciamento para administradores.
* **🏦 Contas Bancárias:** Cadastro e controle de múltiplas contas, com lançamentos de débitos, créditos e transferências.
* **💳 Crediários:** Gestão completa de cartões de crédito e crediários, com geração automática de faturas.
* **💸 Financiamentos:** Acompanhamento de financiamentos, com controle de parcelas e amortizações.
* **🧾 Despesas e Receitas:** Cadastro de despesas e receitas recorrentes para automação e previsão de lançamentos.
* **💰 Salário:** Lançamento facilitado de holerites a partir de itens pré-cadastrados.
* **📈 Relatórios e Painéis:**
    * **Fluxo de Caixa:** Projeção de saldos futuros com base em lançamentos previstos.
    * **Painel de Pagamentos e Recebimentos:** Visão centralizada de contas a pagar e a receber.
    * **Extratos:** Geração de extrato bancário detalhado e extrato consolidado.

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído utilizando as seguintes tecnologias e padrões:

* **Backend:**
    * **Linguagem:** Python 3
    * **Framework:** Flask
    * **ORM:** SQLAlchemy com Flask-SQLAlchemy
    * **Migrations:** Flask-Migrate (Alembic)
    * **Autenticação:** Flask-Login
    * **Formulários:** Flask-WTF
* **Frontend:**
    * **Template Engine:** Jinja2
    * **Estilização:** CSS customizado
    * **Interatividade:** JavaScript (com AJAX para requisições assíncronas)
    * **Gráficos:** Chart.js
* **Banco de Dados:**
    * PostgreSQL
* **Arquitetura:**
    * Padrão MVC (Model-View-Controller)
    * Estrutura em Camadas (Apresentação, Aplicação, Serviços, Dados)
    * Application Factory Pattern

---

## ⚙️ Como Executar o Projeto Localmente

Siga os passos abaixo para configurar e executar o projeto em seu ambiente de desenvolvimento.

### Pré-requisitos

* [Python 3.8+](https://www.python.org/)
* [PostgreSQL](https://www.postgresql.org/download/)
* [Git](https://git-scm.com/)

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
    * Crie um banco de dados no seu PostgreSQL (ex: `web_finance_db`).
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Copie o conteúdo abaixo para o arquivo `.env` e substitua com suas credenciais:
        ```ini
        SECRET_KEY='sua_chave_secreta_aqui'
        DATABASE_URL='postgresql://USUARIO:SENHA@localhost:5432/NOME_DO_BANCO'
        ```

5.  **Aplique as migrações do banco de dados:**
    ```bash
    flask db upgrade
    ```
    *Este comando criará todas as tabelas necessárias no seu banco de dados.*

6.  **Execute a aplicação:**
    ```bash
    flask run
    ```

Pronto! A aplicação estará rodando em `http://127.0.0.1:5000`.

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT.
