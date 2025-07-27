# app/routes/conta_transacao_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required, current_user
from app import db
from app.models.conta_transacao_model import ContaTransacao
from app.forms.conta_transacao_forms import (
    CadastroContaTransacaoForm,
    EditarContaTransacaoForm,
)

conta_transacao_bp = Blueprint(
    "conta_transacao", __name__, url_prefix="/tipos_transacao"
)


@conta_transacao_bp.route("/")
@login_required
def listar_tipos_transacao():
    tipos_transacao = ContaTransacao.query.filter_by(usuario_id=current_user.id).all()
    return render_template(
        "conta_transacoes/list.html", tipos_transacao=tipos_transacao
    )


@conta_transacao_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_tipo_transacao():
    form = CadastroContaTransacaoForm()

    if form.validate_on_submit():
        transacao_tipo = form.transacao_tipo.data.strip().upper()
        tipo_movimento = form.tipo.data

        novo_tipo_transacao = ContaTransacao(
            usuario_id=current_user.id,
            transacao_tipo=transacao_tipo,
            tipo=tipo_movimento,
        )
        db.session.add(novo_tipo_transacao)
        db.session.commit()
        flash("Tipo de transação adicionado com sucesso!", "success")
        current_app.logger.info(
            f'Tipo de transação "{transacao_tipo}" ({tipo_movimento}) adicionado por {current_user.login} (ID: {current_user.id})'
        )
        return redirect(url_for("conta_transacao.listar_tipos_transacao"))

    return render_template("conta_transacoes/add.html", form=form)


@conta_transacao_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_tipo_transacao(id):
    tipo_transacao = ContaTransacao.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarContaTransacaoForm(
        original_transacao_tipo=tipo_transacao.transacao_tipo,
        original_tipo=tipo_transacao.tipo,
    )

    if form.validate_on_submit():
        tipo_transacao.transacao_tipo = form.transacao_tipo.data.strip().upper()

        tipo_transacao.tipo = tipo_transacao.tipo

        db.session.commit()
        flash("Tipo de transação atualizado com sucesso!", "success")
        current_app.logger.info(
            f'Tipo de transação "{tipo_transacao.transacao_tipo}" (ID: {tipo_transacao.id}) atualizado por {current_user.login} (ID: {current_user.id})'
        )
        return redirect(url_for("conta_transacao.listar_tipos_transacao"))

    elif request.method == "GET":
        form.transacao_tipo.data = tipo_transacao.transacao_tipo
        form.tipo.data = tipo_transacao.tipo

    return render_template(
        "conta_transacoes/edit.html", form=form, tipo_transacao=tipo_transacao
    )


@conta_transacao_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_tipo_transacao(id):
    tipo_transacao = ContaTransacao.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    db.session.delete(tipo_transacao)
    db.session.commit()
    flash("Tipo de transação excluído com sucesso!", "success")
    current_app.logger.info(
        f'Tipo de transação "{tipo_transacao.transacao_tipo}" (ID: {tipo_transacao.id}) excluído por {current_user.login} (ID: {current_user.id})'
    )
    return redirect(url_for("conta_transacao.listar_tipos_transacao"))
