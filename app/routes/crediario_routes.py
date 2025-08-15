# app/routes/crediario_routes.py

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.forms.crediario_forms import CadastroCrediarioForm, EditarCrediarioForm
from app.models.crediario_model import Crediario
from app.services.crediario_service import (
    atualizar_crediario,
    criar_crediario,
)
from app.services.crediario_service import (
    excluir_crediario_por_id as excluir_crediario_service,
)

crediario_bp = Blueprint("crediario", __name__, url_prefix="/crediarios")


@crediario_bp.route("/")
@login_required
def listar_crediarios():
    crediarios = (
        Crediario.query.filter_by(usuario_id=current_user.id)
        .order_by(Crediario.ativa.desc())
        .order_by(Crediario.nome_crediario.asc())
        .order_by(Crediario.tipo_crediario.asc())
        .all()
    )
    return render_template("crediarios/list.html", crediarios=crediarios)


@crediario_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_crediario():
    form = CadastroCrediarioForm()
    if form.validate_on_submit():
        success, message = criar_crediario(form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario.listar_crediarios"))
        else:
            flash(message, "danger")
    return render_template("crediarios/add.html", form=form)


@crediario_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_crediario(id):
    crediario = Crediario.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarCrediarioForm(
        obj=crediario,
        original_nome_crediario=crediario.nome_crediario,
        original_tipo_crediario=crediario.tipo_crediario,
        original_identificador_final=crediario.identificador_final,
    )

    if form.validate_on_submit():
        success, message = atualizar_crediario(crediario, form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario.listar_crediarios"))
        else:
            flash(message, "danger")

    return render_template("crediarios/edit.html", form=form, crediario=crediario)


@crediario_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_crediario(id):
    success, message = excluir_crediario_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("crediario.listar_crediarios"))
