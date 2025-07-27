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

# As importações de Conta e ContaMovimento não são necessárias aqui se não forem usadas em outras partes
# from app.models.conta_model import Conta
# from app.models.conta_movimento_model import ContaMovimento
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
import functools
import re
from app.forms.usuario_forms import CadastroUsuarioForm, EditarUsuarioForm

# A importação de Decimal não é necessária aqui se não for usada em outras partes
# from decimal import Decimal

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")


def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Você não tem permissão para acessar esta página.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


def validar_senha_forte(senha):
    if len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r"[A-Z]", senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",<.>/?`~]', senha):
        return False, "A senha deve conter pelo menos um caractere especial."
    return True, ""


@usuario_bp.route("/")
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template("usuarios/list.html", usuarios=usuarios)


@usuario_bp.route("/adicionar", methods=["GET", "POST"])
@admin_required
def adicionar_usuario():
    form = CadastroUsuarioForm()

    if form.validate_on_submit():
        nome = form.nome.data.strip().upper()
        sobrenome = form.sobrenome.data.strip().upper()
        email = form.email.data.strip()
        login = form.login.data.strip().lower()
        senha = form.senha.data

        novo_usuario = Usuario(
            nome=nome,
            sobrenome=sobrenome,
            email=email,
            login=login,
            senha_hash=generate_password_hash(senha),
            is_admin=form.is_admin.data,
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Usuário adicionado com sucesso!", "success")
        current_app.logger.info(
            f"Usuário {login} adicionado por {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
        )
        return redirect(url_for("usuario.listar_usuarios"))

    return render_template("usuarios/add.html", form=form)


@usuario_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    form = EditarUsuarioForm(original_email=usuario.email, original_login=usuario.login)

    if form.validate_on_submit():
        # REMOVIDO: Lógica de validação de saldo e ativação de conta, pois não pertence a Usuario
        # if not form.ativa.data and Decimal(str(usuario.saldo_atual)) != Decimal('0.00'):
        #     flash('Não é possível inativar a conta. O saldo atual deve ser zero para inativação.', 'danger')
        #     form.nome.data = usuario.nome
        #     form.sobrenome.data = usuario.sobrenome
        #     form.email.data = usuario.email
        #     form.login.data = usuario.login
        #     form.is_active.data = usuario.is_active
        #     form.is_admin.data = usuario.is_admin
        #     return render_template('usuarios/edit.html', form=form, usuario=usuario)

        usuario.nome = form.nome.data.strip().upper()
        usuario.sobrenome = form.sobrenome.data.strip().upper()
        usuario.email = form.email.data.strip()
        usuario.login = form.login.data.strip().lower()

        if form.senha.data:
            usuario.set_password(form.senha.data)

        usuario.is_active = form.is_active.data
        if current_user.is_admin:
            usuario.is_admin = form.is_admin.data

        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        current_app.logger.info(
            f"Usuário {usuario.login} (ID: {usuario.id}) atualizado por {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
        )
        return redirect(url_for("usuario.listar_usuarios"))

    elif request.method == "GET":
        form.nome.data = usuario.nome
        form.sobrenome.data = usuario.sobrenome
        form.email.data = usuario.email
        form.login.data = usuario.login
        form.is_active.data = usuario.is_active
        form.is_admin.data = usuario.is_admin

    return render_template("usuarios/edit.html", form=form, usuario=usuario)


@usuario_bp.route("/excluir/<int:id>", methods=["POST"])
@admin_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if current_user.id == usuario.id:
        flash("Você não pode excluir seu próprio usuário.", "danger")
        current_app.logger.warning(
            f"Tentativa de auto-exclusão bloqueada para {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
        )
        return redirect(url_for("usuario.listar_usuarios"))

    # NOVO: Verificar se o usuário possui contas bancárias associadas
    if len(usuario.contas) > 0:
        flash(
            "Não é possível excluir o usuário. Existem contas bancárias associadas a ele.",
            "danger",
        )
        return redirect(url_for("usuario.listar_usuarios"))

    # NOVO: Verificar se o usuário possui movimentações associadas
    # (Embora as contas já cubram isso, é bom ter uma verificação direta se a regra for mais estrita)
    if (
        len(usuario.movimentos) > 0
    ):  # 'movimentos' é o backref de ContaMovimento para Usuario
        flash(
            "Não é possível excluir o usuário. Existem movimentações associadas a ele.",
            "danger",
        )
        return redirect(url_for("usuario.listar_usuarios"))

    # NOVO: Verificar se o usuário possui tipos de transação associados
    if (
        len(usuario.tipos_transacao) > 0
    ):  # 'tipos_transacao' é o backref de ContaTransacao para Usuario
        flash(
            "Não é possível excluir o usuário. Existem tipos de transação associados a ele.",
            "danger",
        )
        return redirect(url_for("usuario.listar_usuarios"))

    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído com sucesso!", "success")
    current_app.logger.info(
        f"Usuário {usuario.login} (ID: {usuario.id}) excluído por {current_user.login} (ID: {current_user.id}, IP: {request.remote_addr})"
    )
    return redirect(url_for("usuario.listar_usuarios"))
