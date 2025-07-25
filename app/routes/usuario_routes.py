from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db
from app.models.usuario_model import Usuario
from werkzeug.security import (
    generate_password_hash,
)
from flask_login import login_required, current_user
import functools

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


@usuario_bp.route("/")
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template("usuarios/list.html", usuarios=usuarios)


@usuario_bp.route("/adicionar", methods=["GET", "POST"])
@admin_required
def adicionar_usuario():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        login = request.form.get("login")
        senha = request.form.get("senha")
        is_admin = request.form.get("is_admin") == "on"

        if not all([nome, email, login, senha]):
            flash("Todos os campos obrigatórios devem ser preenchidos.", "danger")
            return redirect(url_for("usuario.adicionar_usuario"))

        if Usuario.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.", "danger")
            return redirect(url_for("usuario.adicionar_usuario"))

        if Usuario.query.filter_by(login=login).first():
            flash("Login já cadastrado.", "danger")
            return redirect(url_for("usuario.adicionar_usuario"))

        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            login=login,
            senha_hash=senha_hash,
            is_admin=is_admin,
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash("Usuário adicionado com sucesso!", "success")
        return redirect(url_for("usuario.listar_usuarios"))
    return render_template("usuarios/add.html")


@usuario_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if request.method == "POST":
        usuario.nome = request.form.get("nome")
        usuario.email = request.form.get("email")
        usuario.login = request.form.get("login")
        nova_senha = request.form.get("senha")
        if nova_senha:
            usuario.set_password(nova_senha)

        usuario.is_active = request.form.get("is_active") == "on"

        usuario.is_admin = request.form.get("is_admin") == "on"

        if Usuario.query.filter(
            Usuario.email == usuario.email, Usuario.id != id
        ).first():
            flash("E-mail já cadastrado por outro usuário.", "danger")
            return redirect(url_for("usuario.editar_usuario", id=id))
        if Usuario.query.filter(
            Usuario.login == usuario.login, Usuario.id != id
        ).first():
            flash("Login já cadastrado por outro usuário.", "danger")
            return redirect(url_for("usuario.editar_usuario", id=id))

        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("usuario.listar_usuarios"))
    return render_template("usuarios/edit.html", usuario=usuario)


@usuario_bp.route("/excluir/<int:id>", methods=["POST"])
@admin_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)

    if current_user.id == usuario.id:
        flash("Você não pode excluir seu próprio usuário.", "danger")
        return redirect(url_for("usuario.listar_usuarios"))

    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for("usuario.listar_usuarios"))
