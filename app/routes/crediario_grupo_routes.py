# app/routes/crediario_grupo_routes.py

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.forms.crediario_grupo_forms import (
    CadastroCrediarioGrupoForm,
    EditarCrediarioGrupoForm,
)
from app.models.crediario_grupo_model import CrediarioGrupo
from app.services.crediario_grupo_service import (
    atualizar_grupo,
    criar_grupo,
)
from app.services.crediario_grupo_service import (
    excluir_grupo_por_id as excluir_grupo_service,
)

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
        success, message = criar_grupo(form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario_grupo.listar_grupos_crediario"))
        else:
            flash(message, "danger")
    return render_template("crediario_grupos/add.html", form=form)


@crediario_grupo_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_grupo_crediario(id):
    grupo_crediario_obj = CrediarioGrupo.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarCrediarioGrupoForm(
        obj=grupo_crediario_obj,
        original_grupo_crediario=grupo_crediario_obj.grupo_crediario,
        original_tipo_grupo_crediario=grupo_crediario_obj.tipo_grupo_crediario,
    )

    if form.validate_on_submit():
        success, message = atualizar_grupo(grupo_crediario_obj, form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario_grupo.listar_grupos_crediario"))
        else:
            flash(message, "danger")

    return render_template(
        "crediario_grupos/edit.html", form=form, grupo_crediario_obj=grupo_crediario_obj
    )


@crediario_grupo_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_grupo_crediario(id):
    success, message = excluir_grupo_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("crediario_grupo.listar_grupos_crediario"))
