# app/routes/desp_rec_routes.py

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.forms.desp_rec_forms import CadastroDespRecForm, EditarDespRecForm
from app.models.desp_rec_model import DespRec
from app.services.desp_rec_service import atualizar_cadastro, criar_cadastro
from app.services.desp_rec_service import (
    excluir_cadastro_por_id as excluir_cadastro_service,
)

desp_rec_bp = Blueprint("desp_rec", __name__, url_prefix="/despesas_receitas")


@desp_rec_bp.route("/")
@login_required
def listar_cadastros():
    cadastros = (
        DespRec.query.filter_by(usuario_id=current_user.id)
        .order_by(DespRec.ativo.desc(), DespRec.nome.asc(), DespRec.natureza.asc())
        .all()
    )
    return render_template("desp_rec/list.html", cadastros=cadastros)


@desp_rec_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_cadastro():
    form = CadastroDespRecForm()
    if form.validate_on_submit():
        success, message = criar_cadastro(form)
        if success:
            flash(message, "success")
            return redirect(url_for("desp_rec.listar_cadastros"))
        else:
            flash(message, "danger")
    return render_template("desp_rec/add.html", form=form, title="Adicionar Cadastro")


@desp_rec_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cadastro(id):
    cadastro = DespRec.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    form = EditarDespRecForm(obj=cadastro)

    if form.validate_on_submit():
        success, message = atualizar_cadastro(cadastro, form)
        if success:
            flash(message, "success")
            return redirect(url_for("desp_rec.listar_cadastros"))
        else:
            flash(message, "danger")

    return render_template(
        "desp_rec/edit.html", form=form, title="Editar Cadastro", cadastro=cadastro
    )


@desp_rec_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_cadastro(id):
    success, message = excluir_cadastro_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("desp_rec.listar_cadastros"))
