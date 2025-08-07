Estrutura do Projeto Atualizada
07-08-2025


web_finance/
├── .env
├── .vscode/
│   ├── extensions.json
│   └── settings.json
├── app/
│   ├── __init__.py
│   ├── forms/
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
│   │   ├── salario_forms.py
│   │   └── usuario_forms.py
│   ├── models/
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
│   ├── routes/
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
│   │   ├── salario_routes.py
│   │   └── usuario_routes.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   └── templates/
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
├── config.py
├── requirements.txt
└── run.py
