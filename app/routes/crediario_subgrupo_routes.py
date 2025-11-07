# app/routes/crediario_subgrupo_routes.py

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.crediario_subgrupo_forms import (
    CadastroCrediarioSubgrupoForm,
    EditarCrediarioSubgrupoForm,
)
from app.models.crediario_subgrupo_model import CrediarioSubgrupo
from app.services import crediario_grupo_service, crediario_subgrupo_service

crediario_subgrupo_bp = Blueprint(
    "crediario_subgrupo", __name__, url_prefix="/subgrupos_crediario"
)


@crediario_subgrupo_bp.route("/")
@login_required
def listar_subgrupos():
    subgrupos = crediario_subgrupo_service.get_all_subgrupos_for_user()
    return render_template("crediario_subgrupos/list.html", subgrupos=subgrupos)


@crediario_subgrupo_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_subgrupo():
    grupo_choices = crediario_grupo_service.get_all_crediario_grupos_for_user_choices()
    form = CadastroCrediarioSubgrupoForm(grupo_choices=grupo_choices)

    if form.validate_on_submit():
        success, message = crediario_subgrupo_service.criar_subgrupo(form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario_subgrupo.listar_subgrupos"))
        else:
            flash(message, "danger")

    return render_template("crediario_subgrupos/add.html", form=form)


@crediario_subgrupo_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_subgrupo(id):
    subgrupo = CrediarioSubgrupo.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    grupo_choices = crediario_grupo_service.get_all_crediario_grupos_for_user_choices()
    form = EditarCrediarioSubgrupoForm(obj=subgrupo, grupo_choices=grupo_choices)

    if form.validate_on_submit():
        success, message = crediario_subgrupo_service.atualizar_subgrupo(subgrupo, form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario_subgrupo.listar_subgrupos"))
        else:
            flash(message, "danger")
            return render_template(
                "crediario_subgrupos/edit.html", form=form, subgrupo=subgrupo
            )

    return render_template(
        "crediario_subgrupos/edit.html", form=form, subgrupo=subgrupo
    )


@crediario_subgrupo_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_subgrupo(id):
    success, message = crediario_subgrupo_service.excluir_subgrupo_por_id(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("crediario_subgrupo.listar_subgrupos"))


@crediario_subgrupo_bp.route("/json/<int:grupo_id>")
@login_required
def get_subgrupos_json(grupo_id):
    return crediario_subgrupo_service.get_subgrupos_by_grupo_id_json(grupo_id)
