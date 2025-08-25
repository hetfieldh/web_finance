Estrutura do Projeto Atualizada
25-08-2025


.
├── app
│   ├── forms
│   │   ├── conta_forms.py
│   │   ├── conta_movimento_forms.py
│   │   ├── conta_transacao_forms.py
│   │   ├── crediario_fatura_forms.py
│   │   ├── crediario_forms.py
│   │   ├── crediario_grupo_forms.py
│   │   ├── crediario_movimento_forms.py
│   │   ├── desp_rec_forms.py
│   │   ├── extrato_forms.py
│   │   ├── financiamento_forms.py
│   │   ├── fluxo_caixa_forms.py
│   │   ├── pagamentos_forms.py
│   │   ├── recebimentos_forms.py
│   │   ├── salario_forms.py
│   │   ├── solicitacao_forms.py
│   │   └── usuario_forms.py
│   ├── __init__.py
│   ├── models
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
│   │   ├── solicitacao_acesso_model.py
│   │   └── usuario_model.py
│   ├── routes
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
│   │   ├── extrato_consolidado_routes.py
│   │   ├── extrato_routes.py
│   │   ├── financiamento_routes.py
│   │   ├── fluxo_caixa_routes.py
│   │   ├── graphics_routes.py
│   │   ├── main_routes.py
│   │   ├── pagamentos_routes.py
│   │   ├── recebimentos_routes.py
│   │   ├── salario_routes.py
│   │   ├── solicitacao_routes.py
│   │   └── usuario_routes.py
│   ├── services
│   │   ├── conta_service.py
│   │   ├── conta_transacao_service.py
│   │   ├── crediario_grupo_service.py
│   │   ├── crediario_movimento_service.py
│   │   ├── crediario_service.py
│   │   ├── desp_rec_service.py
│   │   ├── fatura_service.py
│   │   ├── financiamento_service.py
│   │   ├── graphics_service.py
│   │   ├── __init.__.py
│   │   ├── movimento_service.py
│   │   ├── pagamento_service.py
│   │   ├── recebimento_service.py
│   │   ├── relatorios_service.py
│   │   ├── salario_service.py
│   │   └── usuario_service.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   ├── images
│   │   │   ├── error-icon.png
│   │   │   ├── favicon.png
│   │   │   ├── logo2.png
│   │   │   ├── logo-black.png
│   │   │   └── logo-white.png
│   │   └── js
│   │       ├── ajax-forms.js
│   │       ├── financiamento.js
│   │       ├── forms.js
│   │       ├── form-spinner.js
│   │       ├── global.js
│   │       ├── graphics.js
│   │       ├── modals.js
│   │       └── salario_form.js
│   ├── templates
│   │   ├── base.html
│   │   ├── conta_movimentos
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── contas
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── conta_transacoes
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── crediarios
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── crediario_faturas
│   │   │   ├── list.html
│   │   │   └── view.html
│   │   ├── crediario_grupos
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── crediario_movimentos
│   │   │   ├── add.html
│   │   │   ├── detalhes.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── dashboard.html
│   │   ├── desp_rec
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── desp_rec_movimento
│   │   │   ├── add_unico.html
│   │   │   ├── edit.html
│   │   │   ├── gerar_previsao.html
│   │   │   └── list.html
│   │   ├── errors
│   │   │   ├── 404.html
│   │   │   └── 500.html
│   │   ├── extratos
│   │   │   ├── bancario.html
│   │   │   └── consolidado.html
│   │   ├── financiamentos
│   │   │   ├── add.html
│   │   │   ├── amortizar.html
│   │   │   ├── edit.html
│   │   │   ├── importar_parcelas.html
│   │   │   ├── list.html
│   │   │   └── parcelas.html
│   │   ├── fluxo_caixa
│   │   │   └── painel.html
│   │   ├── graphics.html
│   │   ├── graphics_2.html
│   │   ├── includes
│   │   │   ├── _macros.html
│   │   │   └── _sidebar.html
│   │   ├── login.html
│   │   ├── pagamentos
│   │   │   └── painel.html
│   │   ├── recebimentos
│   │   │   └── painel.html
│   │   ├── salario_item
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── salario_movimento
│   │   │   ├── add.html
│   │   │   ├── gerenciar_itens.html
│   │   │   └── list.html
│   │   ├── solicitacoes
│   │   │   ├── gerenciar.html
│   │   │   ├── solicitar_acesso.html
│   │   │   └── verificar_status.html
│   │   └── usuarios
│   │       ├── add.html
│   │       ├── edit.html
│   │       ├── list.html
│   │       └── perfil.html
│   ├── template_filters.py
│   └── utils.py
├── config.py
├── .gitignore
├── migrations
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       └── 6c2aa3907e61_versão_final_do_bd.py
├── node_modules
│   ├── .bin
│   │   ├── prettier
│   │   ├── prettier.cmd
│   │   └── prettier.ps1
│   ├── .package-lock.json
│   ├── prettier
│   │   ├── bin
│   │   │   └── prettier.cjs
│   │   ├── doc.d.ts
│   │   ├── doc.js
│   │   ├── doc.mjs
│   │   ├── index.cjs
│   │   ├── index.d.ts
│   │   ├── index.mjs
│   │   ├── internal
│   │   │   ├── experimental-cli.mjs
│   │   │   ├── experimental-cli-worker.mjs
│   │   │   └── legacy-cli.mjs
│   │   ├── LICENSE
│   │   ├── package.json
│   │   ├── plugins
│   │   │   ├── acorn.d.ts
│   │   │   ├── acorn.js
│   │   │   ├── acorn.mjs
│   │   │   ├── angular.d.ts
│   │   │   ├── angular.js
│   │   │   ├── angular.mjs
│   │   │   ├── babel.d.ts
│   │   │   ├── babel.js
│   │   │   ├── babel.mjs
│   │   │   ├── estree.d.ts
│   │   │   ├── estree.js
│   │   │   ├── estree.mjs
│   │   │   ├── flow.d.ts
│   │   │   ├── flow.js
│   │   │   ├── flow.mjs
│   │   │   ├── glimmer.d.ts
│   │   │   ├── glimmer.js
│   │   │   ├── glimmer.mjs
│   │   │   ├── graphql.d.ts
│   │   │   ├── graphql.js
│   │   │   ├── graphql.mjs
│   │   │   ├── html.d.ts
│   │   │   ├── html.js
│   │   │   ├── html.mjs
│   │   │   ├── markdown.d.ts
│   │   │   ├── markdown.js
│   │   │   ├── markdown.mjs
│   │   │   ├── meriyah.d.ts
│   │   │   ├── meriyah.js
│   │   │   ├── meriyah.mjs
│   │   │   ├── postcss.d.ts
│   │   │   ├── postcss.js
│   │   │   ├── postcss.mjs
│   │   │   ├── typescript.d.ts
│   │   │   ├── typescript.js
│   │   │   ├── typescript.mjs
│   │   │   ├── yaml.d.ts
│   │   │   ├── yaml.js
│   │   │   └── yaml.mjs
│   │   ├── README.md
│   │   ├── standalone.d.ts
│   │   ├── standalone.js
│   │   ├── standalone.mjs
│   │   └── THIRD-PARTY-NOTICES.md
│   └── prettier-plugin-jinja-template
│       ├── .github
│       │   └── workflows
│       │       └── node.js.yml
│       ├── .prettierignore
│       ├── .prettierrc
│       ├── babel.config.js
│       ├── jest.config.js
│       ├── LICENSE
│       ├── package.json
│       ├── README.md
│       ├── src
│       │   ├── index.ts
│       │   ├── jinja.ts
│       │   ├── parser.ts
│       │   ├── printer.ts
│       │   ├── regex.ts
│       │   └── regex_editable.ts
│       ├── test
│       │   ├── cases
│       │   │   ├── collition
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── comment
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_2
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_as_attr
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_empty
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_escaped
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_long
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_multi
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_multiline
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── expression_whitespace
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── ignore
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── ignore_jinja
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── issue_25
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── newline_between
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_after_script
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_broken
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_broken_2
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_broken_3
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_empty_block
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_for_else
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_if_else
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_if_else_2
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_inline
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_long
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_multiple
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_multiple_else
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_non_closing
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_set
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_underscore_end
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_unknown
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   ├── statement_whitespace
│       │   │   │   ├── expected.html
│       │   │   │   └── input.html
│       │   │   └── statement_with
│       │   │       ├── expected.html
│       │   │       └── input.html
│       │   ├── parser.test.ts
│       │   ├── plugin.test.ts
│       │   └── printer.test.ts
│       └── tsconfig.json
├── package.json
├── package-lock.json
├── pytest.ini
├── README.md
├── requirements.txt
├── run.py
└── tests
    ├── conftest.py
    ├── test_auth.py
    ├── test_conta.py
    ├── test_crediario.py
    ├── test_desp_rec.py
    ├── test_financiamento.py
    ├── test_salario.py
    └── test_usuario_crud.py
