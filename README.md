Web Finance

Este projeto é uma aplicação web desenvolvida com Flask, Python e PostgreSQL, focada no gerenciamento de usuários. Ele incorpora diversas funcionalidades para garantir a segurança, robustez e usabilidade do sistema.
Funcionalidades Desenvolvidas

A seguir, um resumo das principais funcionalidades implementadas:
1. Estrutura e Configuração Base

    Ambiente de Desenvolvimento: Utiliza ambiente virtual (venv) para isolamento de dependências.

    Configuração Centralizada: Gerenciamento de configurações da aplicação (chaves secretas, conexão com DB, etc.) via config.py e variáveis de ambiente (.env).

    Inicialização da Aplicação: Ponto de entrada (run.py) para iniciar o servidor Flask.

2. Banco de Dados

    PostgreSQL: Utilizado como sistema de gerenciamento de banco de dados.

    Flask-SQLAlchemy: ORM para interação simplificada com o banco de dados.

    Flask-Migrate (Alembic): Gerenciamento de migrações de esquema do banco de dados, permitindo evoluir a estrutura das tabelas de forma controlada.

3. Autenticação e Autorização

    Flask-Login: Sistema de gerenciamento de sessões de usuário (Login e Logout).

    Controle de Acesso: Rotas protegidas que exigem autenticação para acesso.

    Permissões de Administrador: Implementação de um decorador @admin_required para restringir o acesso a funcionalidades específicas (e.g., gerenciamento de usuários) apenas para usuários com privilégios de administrador.

4. Gerenciamento de Usuários (CRUD)

    Modelo de Usuário (Usuario): Definição da estrutura de dados para usuários, incluindo nome, sobrenome, e-mail, login, senha (hashed), status de atividade e privilégios de administrador.

    Operações CRUD: Funcionalidades completas para:

        Listar Usuários: Visualização de todos os usuários cadastrados.

        Adicionar Usuários: Cadastro de novos usuários.

        Editar Usuários: Modificação de dados de usuários existentes.

        Excluir Usuários: Remoção de registros de usuários.

5. Validação de Formulários (Flask-WTF)

    Flask-WTF: Utilização da extensão para criação e validação de formulários de forma robusta e segura.

    Validações Abrangentes:

        Campos Obrigatórios: Nome, Sobrenome, E-mail, Login e Senha.

        Formato de E-mail: Validação estrita do formato de e-mail usando email_validator.

        Senha Forte: Requisitos de senha (mínimo 8 caracteres, pelo menos uma letra maiúscula e um caractere especial).

        Confirmação de Senha: Verificação de que a senha e a confirmação coincidem.

        Unicidade: E-mail e Login devem ser únicos no sistema.

        Login Restrito: Proibição de logins com palavras reservadas (e.g., "admin", "root").

        Tamanho de Campos: Restrições de comprimento mínimo e máximo para Nome, Sobrenome e Login.

        Caracteres Permitidos: Validação de caracteres específicos para Nome, Sobrenome e Login.

    Edição de Senha Opcional: Na edição de usuário, a senha só é validada se for fornecida, permitindo que outros dados sejam atualizados sem exigir a reentrada da senha.

6. Padronização e Consistência de Dados

    Nome e Sobrenome: Convertidos automaticamente para CAIXA ALTA ao serem salvos.

    Login: Convertido automaticamente para minúsculas ao ser salvo.

7. Auditoria e Logs

    Sistema de Logging: Configuração de logs para registrar eventos importantes da aplicação.

    Auditoria de Autenticação: Registro de logins bem-sucedidos e falhos, bem como logouts.

    Registro de Erros: Captura e log de erros de requisição (4xx) e erros internos do servidor (500) com informações detalhadas (usuário, IP, traceback).

    Rotação de Logs: Configuração para rotação de arquivos de log para evitar que cresçam indefinidamente.

8. Melhorias de Interface (UI/UX)

    Layout Responsivo: Utilização do Bootstrap 5 para um design adaptável a diferentes tamanhos de tela.

    Componentes Visuais: Cards, tabelas listradas, badges para status.

    Sidebar: Menu lateral com logotipo e informações do usuário logado no rodapé.

    Favicon: Ícone personalizado na aba do navegador.

    Tipografia Otimizada: Ajustes de tamanhos de fonte para diferentes elementos (cabeçalhos, tabelas, formulários, alertas) para melhor legibilidade e aproveitamento do espaço.

    Espaçamento Otimizado: Redução de margens e preenchimentos em formulários para um layout mais compacto.

    Botões de Ação: Estilização de botões de adicionar e botões de ação em tabelas para melhor visibilidade e usabilidade, com ícones Font Awesome.

Este documento serve como um guia rápido das capacidades atuais do seu projeto Web Finance