Estrutura do Projeto Atualizada
07-08-2025


web_finance/
├── .env                     # Configuração das variáveis de ambiente (senhas, chaves)
├── .vscode/                 # Configurações do VSCode
│   ├── extensions.json
│   └── settings.json
├── app/                     # Pasta principal
│   ├── __init__.py          # Inicializador da aplicação
│   ├── forms/               # Contém todos os formulários
│   │   ├── conta_forms.py
│   │   ├── conta_movimento_forms.py
│   │   ├── conta_transacao_forms.py
│   │   ├── crediario_fatura_forms.py
│   │   ├── crediario_forms.py
│   │   ├── crediario_grupo_forms.py
│   │   ├── crediario_movimento_forms.py
│   │   ├── desp_rec_forms.py
│   │   ├── extrato_desp_rec_forms.py
│   │   ├── extrato_forms.py
│   │   ├── financiamento_forms.py
│   │   ├── pagamentos_forms.py
│   │   ├── recebimentos_forms.py
│   │   └── usuario_forms.py
│   ├── models/              # Modelso que definem a estrutura das tabelas do banco de dados (SQLAlchemy)
│   │   ├── conta_model.py
│   │   ├── conta_movimento_model.py
│   │   ├── conta_transacao_model.py
│   │   ├── crediario_fatura_model.py
│   │   ├── crediario_grupo_model.py
│   │   ├── crediario_model.py
│   │   ├── crediario_movimento_model.py
│   │   ├── crediario_parcela_model.py
│   │   ├── desp_rec_model.py
│   │   ├── desp_rec_movimento_model.py
│   │   ├── financiamento_model.py
│   │   ├── financiamento_parcela_model.py
│   │   ├── salario_item_model.py
│   │   ├── salario_movimento_item_model.py
│   │   ├── salario_movimento_model.py
│   │   └── usuario_model.py
│   ├── routes/              # Contém a lógica das rotas e visualizações (Blueprints)
│   │   ├── auth_routes.py
│   │   ├── conta_movimento_routes.py
│   │   ├── conta_routes.py
│   │   ├── conta_transacao_routes.py
│   │   ├── crediario_fatura_routes.py
│   │   ├── crediario_grupo_routes.py
│   │   ├── crediario_movimento_routes.py
│   │   ├── crediario_routes.py
│   │   ├── desp_rec_movimento_routes.py
│   │   ├── desp_rec_routes.py
│   │   ├── extrato_desp_rec_routes.py
│   │   ├── extrato_routes.py
│   │   ├── financiamento_routes.py
│   │   ├── main_routes.py
│   │   ├── pagamentos_routes.py
│   │   ├── recebimentos_routes.py
│   │   ├── salario_routes.py
│   │   └── usuario_routes.py
│   ├── static/              # Arquivos estáticos (CSS, JavaScript, Imagens)
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   └── templates/           # Arquivos HTML (Jinja2)
│       ├── base.html
│       ├── dashboard.html
│       ├── login.html
│       ├── conta_movimentos/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── conta_transacoes/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── contas/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── crediario_faturas/
│       │   ├── gerar.html
│       │   ├── list.html
│       │   └── view.html
│       ├── crediario_grupos/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── crediario_movimentos/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── crediarios/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── desp_rec/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── desp_rec_movimento/
│       │   ├── add_unico.html
│       │   ├── edit.html
│       │   ├── gerar_previsao.html
│       │   └── list.html
│       ├── errors/
│       │   ├── 404.html
│       │   └── 500.html
│       ├── extratos/
│       │   ├── bancario.html
│       │   └── desp_rec.html
│       ├── financiamentos/
│       │   ├── add.html
│       │   ├── edit.html
│       │   ├── importar_parcelas.html
│       │   ├── list.html
│       │   └── parcelas.html
│       ├── includes/
│       │   └── _sidebar.html
│       ├── pagamentos/
│       │   └── painel.html
│       ├── recebimentos/
│       │   └── painel.html
│       ├── salario_item/
│       │   ├── add.html
│       │   ├── edit.html
│       │   └── list.html
│       ├── salario_movimento/
│       │   ├── add.html
│       │   ├── gerenciar_itens.html
│       │   └── list.html
│       └── usuarios/
│           ├── add.html
│           ├── edit.html
│           └── list.html
├── config.py                # Configurações gerais da aplicação
├── requirements.txt         # Bibliotecas Python
└── run.py                   # Ponto de entrada para iniciar a aplicação
