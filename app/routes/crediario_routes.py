# app/routes/crediario_routes.py

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
from app.forms.crediario_forms import CadastroCrediarioForm, EditarCrediarioForm
from app.models.crediario_model import Crediario

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
        nome_crediario = form.nome_crediario.data.strip().upper()
        tipo_crediario = form.tipo_crediario.data
        identificador_final = (
            form.identificador_final.data.strip().upper()
            if form.identificador_final.data
            else None
        )
        limite_total = form.limite_total.data
        ativa = form.ativa.data

        novo_crediario = Crediario(
            usuario_id=current_user.id,
            nome_crediario=nome_crediario,
            tipo_crediario=tipo_crediario,
            identificador_final=identificador_final,
            limite_total=limite_total,
            ativa=ativa,
        )
        db.session.add(novo_crediario)
        db.session.commit()
        flash("Crediário adicionado com sucesso!", "success")
        current_app.logger.info(
            f'Crediário "{nome_crediario}" ({tipo_crediario}) adicionado por {current_user.login} (ID: {current_user.id})'
        )
        return redirect(url_for("crediario.listar_crediarios"))

    return render_template("crediarios/add.html", form=form)


@crediario_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_crediario(id):
    crediario = Crediario.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarCrediarioForm(
        original_nome_crediario=crediario.nome_crediario,
        original_tipo_crediario=crediario.tipo_crediario,
        original_identificador_final=crediario.identificador_final,
    )

    if form.validate_on_submit():
        crediario.nome_crediario = form.nome_crediario.data.strip().upper()
        crediario.identificador_final = (
            form.identificador_final.data.strip().upper()
            if form.identificador_final.data
            else None
        )

        crediario.limite_total = form.limite_total.data
        crediario.ativa = form.ativa.data

        db.session.commit()
        flash("Crediário atualizado com sucesso!", "success")
        current_app.logger.info(
            f'Crediário "{crediario.nome_crediario}" (ID: {crediario.id}) atualizado por {current_user.login} (ID: {current_user.id})'
        )
        return redirect(url_for("crediario.listar_crediarios"))

    elif request.method == "GET":
        form.nome_crediario.data = crediario.nome_crediario
        form.tipo_crediario.data = crediario.tipo_crediario
        form.identificador_final.data = crediario.identificador_final
        form.limite_total.data = crediario.limite_total
        form.ativa.data = crediario.ativa

    return render_template("crediarios/edit.html", form=form, crediario=crediario)


@crediario_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_crediario(id):
    crediario = Crediario.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if len(crediario.movimentos) > 0:
        flash(
            "Não é possível excluir este crediário. Existem movimentos de crediário associados a ele.",
            "danger",
        )
        return redirect(url_for("crediario.listar_crediarios"))

    db.session.delete(crediario)
    db.session.commit()
    flash("Crediário excluído com sucesso!", "success")
    current_app.logger.info(
        f'Crediário "{crediario.nome_crediario}" (ID: {crediario.id}) excluído por {current_user.login} (ID: {current_user.id})'
    )
    return redirect(url_for("crediario.listar_crediarios"))
