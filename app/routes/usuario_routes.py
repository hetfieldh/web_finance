# app/routes/usuario_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    current_app,
)
from app import db
from app.models.usuario_model import Usuario
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
import functools
import re
from app.forms.usuario_forms import CadastroUsuarioForm, EditarUsuarioForm

# Cria um Blueprint para as rotas relacionadas a usuários
usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")


# Decorador customizado para exigir que o usuário seja administrador
def admin_required(f):
    @functools.wraps(f)
    @login_required  # Garante que o usuário esteja logado
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:  # Verifica se o usuário é admin
            flash("Você não tem permissão para acessar esta página.", "danger")
            return redirect(url_for("main.dashboard"))  # Redireciona se não for admin
        return f(*args, **kwargs)

    return decorated_function


# Função para validar a força da senha (reutilizada do formulário)
def validar_senha_forte(senha):
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Z]", senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",<.>/?`~]', senha):
        return False, "A senha deve conter pelo menos um caractere especial."
    return True, ""


@usuario_bp.route("/")
@admin_required  # Rota protegida por admin_required
def listar_usuarios():
    # Busca todos os usuários do banco de dados
    usuarios = Usuario.query.all()
    # Renderiza o template de listagem de usuários
    return render_template("usuarios/list.html", usuarios=usuarios)


@usuario_bp.route("/adicionar", methods=["GET", "POST"])
@admin_required  # Rota protegida por admin_required
def adicionar_usuario():
    # Cria uma instância do formulário de cadastro de usuário
    form = CadastroUsuarioForm()

    if form.validate_on_submit():  # Processa o formulário se for POST e válido
        # Padroniza e limpa os dados do formulário
        nome = form.nome.data.strip().upper()
        sobrenome = form.sobrenome.data.strip().upper()
        email = form.email.data.strip()
        login = form.login.data.strip().lower()
        senha = form.senha.data

        # Cria uma nova instância de Usuário
        novo_usuario = Usuario(
            nome=nome,
            sobrenome=sobrenome,
            email=email,
            login=login,
            senha_hash=generate_password_hash(senha),  # Gera o hash da senha
            is_admin=form.is_admin.data,
        )
        # Adiciona o novo usuário ao banco de dados
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Usuário adicionado com sucesso!", "success")
        # Registra o evento de adição de usuário no log
        current_app.logger.info(
            f"Usuário {login} adicionado por {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
        )
        # Redireciona para a lista de usuários
        return redirect(url_for("usuario.listar_usuarios"))

    # Renderiza o template do formulário de adição (para GET ou validação falha)
    return render_template("usuarios/add.html", form=form)


@usuario_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@admin_required  # Rota protegida por admin_required
def editar_usuario(id):
    # Busca o usuário pelo ID, ou retorna 404 se não encontrado
    usuario = Usuario.query.get_or_404(id)
    # Cria uma instância do formulário de edição, preenchendo com dados originais para validação
    form = EditarUsuarioForm(original_email=usuario.email, original_login=usuario.login)

    if form.validate_on_submit():  # Processa o formulário se for POST e válido
        # Padroniza e atualiza os dados do usuário
        usuario.nome = form.nome.data.strip().upper()
        usuario.sobrenome = form.sobrenome.data.strip().upper()
        usuario.email = form.email.data.strip()
        usuario.login = form.login.data.strip().lower()

        if form.senha.data:  # Atualiza a senha apenas se um novo valor for fornecido
            usuario.set_password(form.senha.data)

        usuario.is_active = form.is_active.data
        if current_user.is_admin:  # Apenas admins podem alterar o status de admin
            usuario.is_admin = form.is_admin.data

        # Salva as alterações no banco de dados
        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        # Registra o evento de atualização de usuário no log
        current_app.logger.info(
            f"Usuário {usuario.login} (ID: {usuario.id}) atualizado por {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
        )
        # Redireciona para a lista de usuários
        return redirect(url_for("usuario.listar_usuarios"))
    elif (
        request.method == "GET"
    ):  # No método GET, preenche o formulário com os dados atuais do usuário
        form.nome.data = usuario.nome
        form.sobrenome.data = usuario.sobrenome
        form.email.data = usuario.email
        form.login.data = usuario.login
        form.is_active.data = usuario.is_active
        form.is_admin.data = usuario.is_admin

    # Renderiza o template do formulário de edição
    return render_template("usuarios/edit.html", form=form, usuario=usuario)


@usuario_bp.route("/excluir/<int:id>", methods=["POST"])
@admin_required  # Rota protegida por admin_required
def excluir_usuario(id):
    # Busca o usuário pelo ID, ou retorna 404 se não encontrado
    usuario = Usuario.query.get_or_404(id)

    if current_user.id == usuario.id:  # Impede que um admin exclua a si mesmo
        flash("Você não pode excluir seu próprio usuário.", "danger")
        # Registra a tentativa de auto-exclusão no log
        current_app.logger.warning(
            f"Tentativa de auto-exclusão bloqueada para {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
        )
        return redirect(url_for("usuario.listar_usuarios"))

    # Deleta o usuário do banco de dados
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído com sucesso!", "success")
    # Registra o evento de exclusão de usuário no log
    current_app.logger.info(
        f"Usuário {usuario.login} (ID: {usuario.id}) excluído por {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
    )
    # Redireciona para a lista de usuários
    return redirect(url_for("usuario.listar_usuarios"))
