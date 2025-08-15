# app/routes/conta_transacao_routes.py

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import asc

from app.forms.conta_transacao_forms import (
    CadastroContaTransacaoForm,
    EditarContaTransacaoForm,
)
from app.models.conta_transacao_model import ContaTransacao
from app.services.conta_transacao_service import (
    atualizar_tipo_transacao,
    criar_tipo_transacao,
)
from app.services.conta_transacao_service import (
    excluir_tipo_transacao_por_id as excluir_tipo_transacao_service,
)

conta_transacao_bp = Blueprint(
    "conta_transacao", __name__, url_prefix="/tipos_transacao"
)


@conta_transacao_bp.route("/")
@login_required
def listar_tipos_transacao():
    tipos_transacao = (
        ContaTransacao.query.filter_by(usuario_id=current_user.id)
        .order_by(ContaTransacao.transacao_tipo.asc(), ContaTransacao.tipo.asc())
        .all()
    )
    return render_template(
        "conta_transacoes/list.html", tipos_transacao=tipos_transacao
    )


@conta_transacao_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_tipo_transacao():
    form = CadastroContaTransacaoForm()
    if form.validate_on_submit():
        success, message = criar_tipo_transacao(form)
        if success:
            flash(message, "success")
            return redirect(url_for("conta_transacao.listar_tipos_transacao"))
        else:
            flash(message, "danger")
    return render_template("conta_transacoes/add.html", form=form)


@conta_transacao_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_tipo_transacao(id):
    tipo_transacao = ContaTransacao.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarContaTransacaoForm(
        obj=tipo_transacao,
        original_transacao_tipo=tipo_transacao.transacao_tipo,
        original_tipo=tipo_transacao.tipo,
    )

    if form.validate_on_submit():
        success, message = atualizar_tipo_transacao(tipo_transacao, form)
        if success:
            flash(message, "success")
            return redirect(url_for("conta_transacao.listar_tipos_transacao"))
        else:
            flash(message, "danger")

    return render_template(
        "conta_transacoes/edit.html", form=form, tipo_transacao=tipo_transacao
    )


@conta_transacao_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_tipo_transacao(id):
    success, message = excluir_tipo_transacao_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("conta_transacao.listar_tipos_transacao"))
