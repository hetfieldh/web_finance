# app\routes\usuario_routes.py

import functools
import re

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import asc, desc
from werkzeug.security import generate_password_hash

from app import db
from app.forms.usuario_forms import (
    CadastroUsuarioForm,
    EditarUsuarioForm,
    PerfilUsuarioForm,
)
from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.models.usuario_model import Usuario
from app.services.usuario_service import atualizar_perfil_usuario, criar_novo_usuario
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
    form = CadastroUsuarioForm(
        request.form if request.method == "POST" else request.args
    )

    if (
        request.method == "GET"
        and form.nome.data
        and form.sobrenome.data
        and not form.login.data
    ):
        from app.routes.solicitacao_routes import sanitizar_login

        nome_sugerido = sanitizar_login(form.nome.data.split(" ")[0])
        sobrenome_sugerido = sanitizar_login(form.sobrenome.data.split(" ")[0])
        form.login.data = f"{nome_sugerido}.{sobrenome_sugerido}"

    if form.validate_on_submit():
        if not form.senha.data:
            solicitacao_original = SolicitacaoAcesso.query.filter_by(
                email=form.email.data
            ).first()

            if solicitacao_original and solicitacao_original.senha_provisoria:
                form.senha.data = solicitacao_original.senha_provisoria
            else:
                form.senha.errors.append(
                    "A senha é obrigatória para criação manual de usuário."
                )
                return render_template("usuarios/add.html", form=form)

        success, message, new_user = criar_novo_usuario(form)
        if success:
            solicitacao_original = SolicitacaoAcesso.query.filter_by(
                email=new_user.email
            ).first()
            if solicitacao_original and solicitacao_original.status == "Aprovada":
                solicitacao_original.login_criado = new_user.login

                senha_para_mensagem = solicitacao_original.senha_provisoria
                mensagem_final = (
                    f"Seja bem-vindo(a)! Seu acesso foi aprovado. Você pode entrar no sistema usando seu e-mail ou o login '{new_user.login}'. "
                    f"Sua senha provisória é '{senha_para_mensagem}'. Recomendamos que você a altere no primeiro acesso através do seu perfil."
                )
                solicitacao_original.motivo_decisao = mensagem_final
                db.session.commit()

            flash(message, "success")
            return redirect(url_for("usuario.listar_usuarios"))
        else:
            if isinstance(message, dict):
                for field, errors in message.items():
                    if hasattr(form, field):
                        getattr(form, field).errors.extend(errors)
                    else:
                        flash(errors[0], "danger")
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

        if current_user.id != usuario.id:
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
        form.process(obj=usuario)

    return render_template(
        "usuarios/edit.html",
        form=form,
        usuario=usuario,
        is_self_edit=(current_user.id == usuario.id),
    )


@usuario_bp.route("/excluir/<int:id>", methods=["POST"])
@admin_required
def excluir_usuario(id):
    success, message = excluir_usuario_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("usuario.listar_usuarios"))


@usuario_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    form = PerfilUsuarioForm(original_email=current_user.email)

    if form.validate_on_submit():
        success, result = atualizar_perfil_usuario(current_user, form)
        if success:
            flash(result, "success")
            return redirect(url_for("main.dashboard"))
        else:
            if isinstance(result, dict):
                for field, errors in result.items():
                    if hasattr(form, field):
                        getattr(form, field).errors.extend(errors)
                    else:
                        flash(errors[0], "danger")
            else:
                flash(result, "danger")

    elif request.method == "GET":
        form.process(obj=current_user)

    return render_template("usuarios/perfil.html", form=form)


@usuario_bp.route("/check-field")
@login_required
def check_field():
    field_name = request.args.get("field_name")
    value = request.args.get("value")
    user_id_to_exclude = request.args.get("user_id", type=int)

    if not field_name or not value:
        return jsonify({"available": False, "message": "Requisição inválida"}), 400

    query = Usuario.query
    if field_name == "login":
        query = query.filter_by(login=value.strip().lower())
    elif field_name == "email":
        query = query.filter_by(email=value.strip())
    else:
        return jsonify({"available": False, "message": "Campo inválido"}), 400

    if user_id_to_exclude:
        query = query.filter(Usuario.id != user_id_to_exclude)

    existing = query.first()

    if existing:
        return jsonify(
            {
                "available": False,
                "message": f"{field_name.capitalize()} já está em uso.",
            }
        )
    else:
        return jsonify(
            {
                "available": True,
                "message": f"{field_name.capitalize()} está disponível.",
            }
        )
