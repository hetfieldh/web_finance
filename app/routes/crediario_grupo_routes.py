# app/routes/crediario_grupo_routes.py

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.crediario_grupo_forms import (
    CadastroCrediarioGrupoForm,
    EditarCrediarioGrupoForm,
)
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_movimento_model import CrediarioMovimento

crediario_grupo_bp = Blueprint(
    "crediario_grupo", __name__, url_prefix="/grupos_crediario"
)


@crediario_grupo_bp.route("/")
@login_required
def listar_grupos_crediario():
    grupos_crediario = (
        CrediarioGrupo.query.filter_by(usuario_id=current_user.id)
        .order_by(
            CrediarioGrupo.grupo_crediario.asc(),
            CrediarioGrupo.tipo_grupo_crediario.asc(),
        )
        .all()
    )
    return render_template(
        "crediario_grupos/list.html", grupos_crediario=grupos_crediario
    )


@crediario_grupo_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_grupo_crediario():
    form = CadastroCrediarioGrupoForm()

    if form.validate_on_submit():
        grupo_crediario = form.grupo_crediario.data.strip().upper()
        tipo_grupo_crediario = form.tipo_grupo_crediario.data
        descricao = form.descricao.data.strip() if form.descricao.data else None

        novo_grupo = CrediarioGrupo(
            usuario_id=current_user.id,
            grupo_crediario=grupo_crediario,
            tipo_grupo_crediario=tipo_grupo_crediario,
            descricao=descricao,
        )
        db.session.add(novo_grupo)
        db.session.commit()
        flash("Grupo de crediário adicionado com sucesso!", "success")
        current_app.logger.info(
            f'Grupo de crediário "{grupo_crediario}" ({tipo_grupo_crediario}) adicionado por {current_user.login} (ID: {current_user.id})'
        )
        return redirect(url_for("crediario_grupo.listar_grupos_crediario"))

    return render_template("crediario_grupos/add.html", form=form)


@crediario_grupo_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_grupo_crediario(id):
    grupo_crediario_obj = CrediarioGrupo.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarCrediarioGrupoForm(
        original_grupo_crediario=grupo_crediario_obj.grupo_crediario,
        original_tipo_grupo_crediario=grupo_crediario_obj.tipo_grupo_crediario,
    )

    if form.validate_on_submit():
        grupo_crediario_obj.grupo_crediario = form.grupo_crediario.data.strip().upper()
        grupo_crediario_obj.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )

        db.session.commit()
        flash("Grupo de crediário atualizado com sucesso!", "success")
        current_app.logger.info(
            f'Grupo de crediário "{grupo_crediario_obj.grupo_crediario}" (ID: {grupo_crediario_obj.id}) atualizado por {current_user.login} (ID: {current_user.id})'
        )
        return redirect(url_for("crediario_grupo.listar_grupos_crediario"))

    elif request.method == "GET":
        form.grupo_crediario.data = grupo_crediario_obj.grupo_crediario
        form.tipo_grupo_crediario.data = grupo_crediario_obj.tipo_grupo_crediario
        form.descricao.data = grupo_crediario_obj.descricao

    return render_template(
        "crediario_grupos/edit.html", form=form, grupo_crediario_obj=grupo_crediario_obj
    )


@crediario_grupo_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_grupo_crediario(id):
    grupo_crediario_obj = CrediarioGrupo.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if len(grupo_crediario_obj.movimentos) > 0:
        flash(
            "Não é possível excluir este grupo de crediário. Existem movimentos de crediário associados a ele.",
            "danger",
        )
        return redirect(url_for("crediario_grupo.listar_grupos_crediario"))

    db.session.delete(grupo_crediario_obj)
    db.session.commit()
    flash("Grupo de crediário excluído com sucesso!", "success")
    current_app.logger.info(
        f'Grupo de crediário "{grupo_crediario_obj.grupo_crediario}" (ID: {grupo_crediario_obj.id}) excluído por {current_user.login} (ID: {current_user.id})'
    )
    return redirect(url_for("crediario_grupo.listar_grupos_crediario"))
