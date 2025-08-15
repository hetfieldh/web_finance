# app/routes/usuario_routes.py

import functools

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.forms.usuario_forms import CadastroUsuarioForm, EditarUsuarioForm
from app.models.usuario_model import Usuario
from app.services.usuario_service import (
    criar_novo_usuario,
)
from app.services.usuario_service import (
    excluir_usuario_por_id as excluir_usuario_service,
)

usuario_bp = Blueprint("usuario", __name__, url_prefix="/usuarios")


def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Você não tem permissão para acessar esta página", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@usuario_bp.route("/")
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.order_by(
        Usuario.is_admin.asc(), Usuario.is_active.desc(), Usuario.nome.asc()
    ).all()
    return render_template("usuarios/list.html", usuarios=usuarios)


@usuario_bp.route("/adicionar", methods=["GET", "POST"])
@admin_required
def adicionar_usuario():
    form = CadastroUsuarioForm()
    if form.validate_on_submit():
        success, message, new_user = criar_novo_usuario(form)
        if success:
            flash(message, "success")
            return redirect(url_for("usuario.listar_usuarios"))
        else:
            flash(message, "danger")

    return render_template("usuarios/add.html", form=form)


@usuario_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    form = EditarUsuarioForm(original_email=usuario.email, original_login=usuario.login)

    if form.validate_on_submit():
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
    success, message = excluir_usuario_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("usuario.listar_usuarios"))
