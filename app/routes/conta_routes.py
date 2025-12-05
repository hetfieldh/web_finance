# app/routes/conta_routes.py

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.forms.conta_forms import CadastroContaForm, EditarContaForm
from app.models.conta_model import Conta
from app.services.conta_service import (
    atualizar_conta,
    criar_conta,
)
from app.services.conta_service import (
    excluir_conta_por_id as excluir_conta_service,
)

conta_bp = Blueprint("conta", __name__, url_prefix="/contas")


@conta_bp.route("/")
@login_required
def listar_contas():
    contas = (
        Conta.query.filter_by(usuario_id=current_user.id)
        .order_by(Conta.ativa.desc(), Conta.nome_banco.asc(), Conta.tipo.asc())
        .all()
    )
    return render_template("contas/list.html", contas=contas)


@conta_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_conta():
    form = CadastroContaForm()
    if form.validate_on_submit():
        success, result = criar_conta(form)
        if success:
            flash(result, "success")
            return redirect(url_for("conta.listar_contas"))
        else:
            if isinstance(result, dict):
                for field, errors in result.items():
                    if field == "form" or not hasattr(form, field):
                        flash(errors[0], "danger")
                    else:
                        getattr(form, field).errors.extend(errors)
            else:
                flash(result, "danger")
    return render_template("contas/add.html", form=form)


@conta_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_conta(id):
    conta = Conta.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    form = EditarContaForm(
        obj=conta,
        original_nome_banco=conta.nome_banco,
        original_agencia=conta.agencia,
        original_conta=conta.conta,
        original_tipo=conta.tipo,
    )

    if request.method == "GET":
        form.process(obj=conta)

    if form.validate_on_submit():
        success, message = atualizar_conta(conta, form)
        if success:
            flash(message, "success")
            return redirect(url_for("conta.listar_contas"))
        else:
            flash(message, "danger")

    return render_template("contas/edit.html", form=form, conta=conta)


@conta_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_conta(id):
    success, message = excluir_conta_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("conta.listar_contas"))
