# app/routes/conta_movimento_routes.py

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

from app import db
from app.forms.conta_movimento_forms import (
    CadastroContaMovimentoForm,
    EditarContaMovimentoForm,
)
from app.models.conta_movimento_model import ContaMovimento
from app.services import conta_service, conta_transacao_service
from app.services.movimento_service import (
    excluir_movimento as excluir_movimento_service,
)
from app.services.movimento_service import registrar_movimento

conta_movimento_bp = Blueprint("conta_movimento", __name__, url_prefix="/movimentacoes")


@conta_movimento_bp.route("/")
@login_required
def listar_movimentacoes():
    movimentacoes = (
        ContaMovimento.query.filter_by(usuario_id=current_user.id)
        .options(
            joinedload(ContaMovimento.conta), joinedload(ContaMovimento.tipo_transacao)
        )
        .order_by(ContaMovimento.data_movimento.desc(), ContaMovimento.id.desc())
        .all()
    )
    return render_template("conta_movimentos/list.html", movimentacoes=movimentacoes)


@conta_movimento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_movimentacao():
    account_choices = conta_service.get_active_accounts_for_user_choices()
    transaction_choices = (
        conta_transacao_service.get_all_transaction_types_for_user_choices()
    )
    transfer_choices = (
        conta_transacao_service.get_debit_transaction_types_for_user_choices()
    )

    form = CadastroContaMovimentoForm(
        account_choices=account_choices,
        transaction_choices=transaction_choices,
        transfer_choices=transfer_choices,
    )

    if form.validate_on_submit():
        success, message = registrar_movimento(form)
        if success:
            flash(message, "success")
            return redirect(url_for("conta_movimento.listar_movimentacoes"))
        else:
            flash(message, "danger")

    return render_template("conta_movimentos/add.html", form=form)


@conta_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimentacao(id):
    movimento = ContaMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarContaMovimentoForm(obj=movimento)

    if form.validate_on_submit():
        movimento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )
        db.session.commit()
        flash("Movimentação atualizada com sucesso!", "success")
        return redirect(url_for("conta_movimento.listar_movimentacoes"))

    return render_template("conta_movimentos/edit.html", form=form, movimento=movimento)


@conta_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimentacao(id):
    success, message = excluir_movimento_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("conta_movimento.listar_movimentacoes"))
