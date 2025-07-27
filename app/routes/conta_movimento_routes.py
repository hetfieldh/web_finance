# app/routes/conta_movimento_routes.py

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
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_model import Conta
from app.models.conta_transacao_model import (
    ContaTransacao,
)
from app.forms.conta_movimento_forms import (
    CadastroContaMovimentoForm,
    EditarContaMovimentoForm,
)
from sqlalchemy.exc import IntegrityError

conta_movimento_bp = Blueprint("conta_movimento", __name__, url_prefix="/movimentacoes")


@conta_movimento_bp.route("/")
@login_required
def listar_movimentacoes():
    movimentacoes = (
        ContaMovimento.query.filter_by(usuario_id=current_user.id)
        .order_by(ContaMovimento.data_movimento.desc())
        .all()
    )
    return render_template("conta_movimentos/list.html", movimentacoes=movimentacoes)


@conta_movimento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_movimentacao():
    form = CadastroContaMovimentoForm()

    if form.validate_on_submit():
        conta_origem_id = form.conta_id.data
        tipo_transacao_id = form.conta_transacao_id.data
        data_movimento = form.data_movimento.data
        valor = form.valor.data
        descricao = form.descricao.data.strip() if form.descricao.data else None

        conta_origem = Conta.query.get(conta_origem_id)
        tipo_transacao = ContaTransacao.query.get(tipo_transacao_id)

        if not conta_origem or not tipo_transacao:
            flash("Erro: Conta ou Tipo de Transação inválidos.", "danger")
            return render_template("conta_movimentos/add.html", form=form)

        if tipo_transacao.tipo == "Débito" and conta_origem.saldo_inicial < valor:
            flash("Saldo insuficiente para esta movimentação.", "danger")
            return render_template("conta_movimentos/add.html", form=form)

        try:
            movimento_principal = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_origem_id,
                conta_transacao_id=tipo_transacao_id,
                data_movimento=data_movimento,
                valor=valor,
                descricao=descricao,
            )
            db.session.add(movimento_principal)
            db.session.flush()

            db.session.commit()
            flash("Movimentação registrada com sucesso!", "success")
            current_app.logger.info(
                f"Movimentação de {tipo_transacao.transacao_tipo} ({tipo_transacao.tipo}) de R$ {valor} na conta {conta_origem.conta} por {current_user.login} (ID: {current_user.id})"
            )
            return redirect(url_for("conta_movimento.listar_movimentacoes"))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro de integridade ao adicionar movimentação: {e}", exc_info=True
            )
            flash(
                "Erro ao registrar movimentação. Verifique os dados e tente novamente.",
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro inesperado ao adicionar movimentação: {e}", exc_info=True
            )
            flash("Ocorreu um erro inesperado. Tente novamente.", "danger")

    return render_template("conta_movimentos/add.html", form=form)


@conta_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimentacao(id):
    movimento = ContaMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarContaMovimentoForm()

    if form.validate_on_submit():
        movimento.conta_id = movimento.conta_id
        movimento.conta_transacao_id = movimento.conta_transacao_id
        movimento.data_movimento = movimento.data_movimento
        movimento.valor = movimento.valor

        movimento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )

        db.session.commit()
        flash("Movimentação atualizada com sucesso!", "success")
        current_app.logger.info(
            f"Movimentação {movimento.id} atualizada por {current_user.login} (ID: {current_user.id})"
        )
        return redirect(url_for("conta_movimento.listar_movimentacoes"))

    elif request.method == "GET":
        form.conta_id.data = movimento.conta_id
        form.conta_transacao_id.data = movimento.conta_transacao_id
        form.data_movimento.data = movimento.data_movimento
        form.valor.data = movimento.valor
        form.descricao.data = movimento.descricao

    return render_template("conta_movimentos/edit.html", form=form, movimento=movimento)


@conta_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimentacao(id):
    movimento = ContaMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if movimento.id_movimento_relacionado:
        movimento_relacionado = ContaMovimento.query.get(
            movimento.id_movimento_relacionado
        )
        if movimento_relacionado:
            movimento_relacionado.id_movimento_relacionado = None
            db.session.add(movimento_relacionado)

    db.session.delete(movimento)
    db.session.commit()
    flash("Movimentação excluída com sucesso!", "success")
    current_app.logger.info(
        f"Movimentação {movimento.id} excluída por {current_user.login} (ID: {current_user.id})"
    )
    return redirect(url_for("conta_movimento.listar_movimentacoes"))
