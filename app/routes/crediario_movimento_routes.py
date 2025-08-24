# app/routes/crediario_movimento_routes.py

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.forms.crediario_movimento_forms import (
    CadastroCrediarioMovimentoForm,
    EditarCrediarioMovimentoForm,
)
from app.models.crediario_movimento_model import CrediarioMovimento
from app.services import crediario_grupo_service, crediario_service
from app.services.crediario_movimento_service import (
    adicionar_movimento,
)
from app.services.crediario_movimento_service import (
    editar_movimento as editar_movimento_service,
)
from app.services.crediario_movimento_service import (
    excluir_movimento as excluir_movimento_service,
)

crediario_movimento_bp = Blueprint(
    "crediario_movimento", __name__, url_prefix="/movimentos_crediario"
)


@crediario_movimento_bp.route("/")
@login_required
def listar_movimentos_crediario():
    movimentos_crediario = (
        CrediarioMovimento.query.filter_by(usuario_id=current_user.id)
        .options(
            joinedload(CrediarioMovimento.crediario),
            joinedload(CrediarioMovimento.crediario_grupo),
        )
        .order_by(
            CrediarioMovimento.data_compra.desc(),
            CrediarioMovimento.data_criacao.desc(),
        )
        .all()
    )
    return render_template(
        "crediario_movimentos/list.html", movimentos_crediario=movimentos_crediario
    )


@crediario_movimento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_movimento_crediario():
    crediario_choices = crediario_service.get_active_crediarios_for_user_choices()
    grupo_choices = crediario_grupo_service.get_all_crediario_grupos_for_user_choices()
    form = CadastroCrediarioMovimentoForm(
        crediario_choices=crediario_choices, grupo_choices=grupo_choices
    )
    if form.validate_on_submit():
        success, message = adicionar_movimento(form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))
        else:
            flash(message, "danger")

    return render_template("crediario_movimentos/add.html", form=form)


@crediario_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimento_crediario(id):
    movimento = CrediarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    crediario_choices = crediario_service.get_active_crediarios_for_user_choices()
    grupo_choices = crediario_grupo_service.get_all_crediario_grupos_for_user_choices()
    form = EditarCrediarioMovimentoForm(
        obj=movimento, crediario_choices=crediario_choices, grupo_choices=grupo_choices
    )

    if form.validate_on_submit():
        success, message = editar_movimento_service(movimento, form)
        if success:
            flash(message, "success")
            return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))
        else:
            flash(message, "danger")
            return render_template(
                "crediario_movimentos/edit.html", form=form, movimento=movimento
            )

    if movimento.valor_total_compra < 0:
        form.valor_total_compra.data = abs(movimento.valor_total_compra)

    return render_template(
        "crediario_movimentos/edit.html", form=form, movimento=movimento
    )


@crediario_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimento_crediario(id):
    success, message = excluir_movimento_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))


@crediario_movimento_bp.route("/detalhes/<int:id>")
@login_required
def detalhes_movimento(id):
    """
    Exibe os detalhes de um movimento de crediário e todas as suas parcelas.
    """
    movimento = (
        CrediarioMovimento.query.options(
            joinedload(CrediarioMovimento.parcelas),
            joinedload(CrediarioMovimento.crediario),
            joinedload(CrediarioMovimento.crediario_grupo),
        )
        .filter_by(id=id, usuario_id=current_user.id)
        .first_or_404()
    )

    return render_template("crediario_movimentos/detalhes.html", movimento=movimento)
