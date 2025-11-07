# app/routes/fornecedor_routes.py

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.fornecedor_forms import (
    CadastroFornecedorForm,
    EditarFornecedorForm,
)
from app.models.fornecedor_model import Fornecedor
from app.services import fornecedor_service

fornecedor_bp = Blueprint("fornecedor", __name__, url_prefix="/fornecedores")


@fornecedor_bp.route("/")
@login_required
def listar_fornecedores():
    fornecedores = (
        Fornecedor.query.filter_by(usuario_id=current_user.id)
        .order_by(Fornecedor.nome.asc())
        .all()
    )
    return render_template("fornecedores/list.html", fornecedores=fornecedores)


@fornecedor_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_fornecedor():
    form = CadastroFornecedorForm()
    if form.validate_on_submit():
        success, message = fornecedor_service.criar_fornecedor(form)
        if success:
            flash(message, "success")
            return redirect(url_for("fornecedor.listar_fornecedores"))
        else:
            flash(message, "danger")

    return render_template("fornecedores/add.html", form=form)


@fornecedor_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_fornecedor(id):
    fornecedor = Fornecedor.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarFornecedorForm(obj=fornecedor)

    if form.validate_on_submit():
        success, message = fornecedor_service.atualizar_fornecedor(fornecedor, form)
        if success:
            flash(message, "success")
            return redirect(url_for("fornecedor.listar_fornecedores"))
        else:
            flash(message, "danger")
            return render_template(
                "fornecedores/edit.html", form=form, fornecedor=fornecedor
            )

    return render_template("fornecedores/edit.html", form=form, fornecedor=fornecedor)


@fornecedor_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_fornecedor(id):
    success, message = fornecedor_service.excluir_fornecedor_por_id(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("fornecedor.listar_fornecedores"))
