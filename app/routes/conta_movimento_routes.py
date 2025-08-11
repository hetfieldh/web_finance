# app/routes/conta_movimento_routes.py

from decimal import Decimal, getcontext

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
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

getcontext().prec = 10

from datetime import datetime

from app import db
from app.forms.conta_movimento_forms import (
    CadastroContaMovimentoForm,
    EditarContaMovimentoForm,
)
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento

conta_movimento_bp = Blueprint("conta_movimento", __name__, url_prefix="/movimentacoes")


@conta_movimento_bp.route("/")
@login_required
def listar_movimentacoes():
    movimentacoes = (
        ContaMovimento.query.filter_by(usuario_id=current_user.id)
        .order_by(ContaMovimento.data_movimento.desc(), ContaMovimento.id.desc())
        .all()
    )
    return render_template("conta_movimentos/list.html", movimentacoes=movimentacoes)


@conta_movimento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_movimentacao():
    form = CadastroContaMovimentoForm()

    if form.validate_on_submit():
        tipo_operacao = form.tipo_operacao.data
        conta_origem_id = form.conta_id.data
        data_movimento = form.data_movimento.data
        valor = form.valor.data
        descricao_manual = form.descricao.data.strip() if form.descricao.data else None

        conta_origem = db.session.query(Conta).get(conta_origem_id)

        if valor <= 0:
            flash("O valor da movimentação deve ser maior que zero.", "danger")
            return render_template("conta_movimentos/add.html", form=form)

        try:
            if tipo_operacao == "simples":
                tipo_transacao_id = form.conta_transacao_id.data
                tipo_transacao = ContaTransacao.query.get(tipo_transacao_id)

                movimento = ContaMovimento(
                    usuario_id=current_user.id,
                    conta_id=conta_origem_id,
                    conta_transacao_id=tipo_transacao_id,
                    data_movimento=data_movimento,
                    valor=valor,
                    descricao=descricao_manual,
                )
                db.session.add(movimento)

                if tipo_transacao.tipo == "Débito":
                    conta_origem.saldo_atual -= valor
                else:  # Crédito
                    conta_origem.saldo_atual += valor

            elif tipo_operacao == "transferencia":
                conta_destino_id = form.conta_destino_id.data
                transferencia_tipo_id = form.transferencia_tipo_id.data

                conta_destino = Conta.query.get(conta_destino_id)
                tipo_transacao_debito = ContaTransacao.query.get(transferencia_tipo_id)
                tipo_transacao_credito = ContaTransacao.query.filter_by(
                    usuario_id=current_user.id,
                    transacao_tipo=tipo_transacao_debito.transacao_tipo,
                    tipo="Crédito",
                ).first()

                if not tipo_transacao_credito:
                    flash(
                        f'Tipo de transação de Crédito correspondente a "{tipo_transacao_debito.transacao_tipo}" não encontrado.',
                        "danger",
                    )
                    return render_template("conta_movimentos/add.html", form=form)

                nome_origem = f"{conta_origem.nome_banco} - {conta_origem.conta}"
                nome_destino = f"{conta_destino.nome_banco} - {conta_destino.conta}"
                desc_origem = (
                    f"{tipo_transacao_debito.transacao_tipo} para {nome_destino}"
                )
                desc_destino = (
                    f"{tipo_transacao_debito.transacao_tipo} de {nome_origem}"
                )
                if descricao_manual:
                    desc_origem += f" ({descricao_manual})"
                    desc_destino += f" ({descricao_manual})"

                movimento_origem = ContaMovimento(
                    usuario_id=current_user.id,
                    conta_id=conta_origem_id,
                    conta_transacao_id=tipo_transacao_debito.id,
                    data_movimento=data_movimento,
                    valor=valor,
                    descricao=desc_origem,
                )
                db.session.add(movimento_origem)
                conta_origem.saldo_atual -= valor
                db.session.flush()

                movimento_destino = ContaMovimento(
                    usuario_id=current_user.id,
                    conta_id=conta_destino_id,
                    conta_transacao_id=tipo_transacao_credito.id,
                    data_movimento=data_movimento,
                    valor=valor,
                    descricao=desc_destino,
                )
                db.session.add(movimento_destino)
                conta_destino.saldo_atual += valor
                db.session.flush()

                movimento_origem.id_movimento_relacionado = movimento_destino.id
                movimento_destino.id_movimento_relacionado = movimento_origem.id

            db.session.commit()
            flash("Movimentação registrada com sucesso!", "success")
            return redirect(url_for("conta_movimento.listar_movimentacoes"))

        except Exception as e:
            db.session.rollback()
            flash("Ocorreu um erro inesperado. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao adicionar movimentação: {e}", exc_info=True
            )

    return render_template("conta_movimentos/add.html", form=form)


@conta_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimentacao(id):
    movimento = ContaMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarContaMovimentoForm()
    if form.validate_on_submit():
        movimento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )
        db.session.commit()
        flash("Movimentação atualizada com sucesso!", "success")
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

    is_linked = (
        DespRecMovimento.query.filter_by(movimento_bancario_id=id).first()
        or FinanciamentoParcela.query.filter_by(movimento_bancario_id=id).first()
        or SalarioMovimento.query.filter_by(movimento_bancario_id=id).first()
    )
    if is_linked:
        flash(
            "Esta movimentação não pode ser excluída diretamente, pois está vinculada a um pagamento ou recebimento. "
            "Por favor, realize o estorno a partir do painel de origem.",
            "danger",
        )
        return redirect(url_for("conta_movimento.listar_movimentacoes"))

    movimentos_posteriores = ContaMovimento.query.filter(
        ContaMovimento.usuario_id == current_user.id,
        or_(
            ContaMovimento.data_movimento > movimento.data_movimento,
            db.and_(
                ContaMovimento.data_movimento == movimento.data_movimento,
                ContaMovimento.id > movimento.id,
            ),
        ),
    ).count()

    if movimentos_posteriores > 0:
        flash(
            "Não é possível excluir esta movimentação, pois existem lançamentos posteriores em suas contas. "
            "Exclua as movimentações da mais recente para a mais antiga para manter a integridade dos saldos.",
            "danger",
        )
        return redirect(url_for("conta_movimento.listar_movimentacoes"))

    conta_afetada = Conta.query.get(movimento.conta_id)
    tipo_transacao = ContaTransacao.query.get(movimento.conta_transacao_id)

    if conta_afetada and tipo_transacao:
        valor_decimal = Decimal(str(movimento.valor))
        if tipo_transacao.tipo == "Débito":
            conta_afetada.saldo_atual += valor_decimal
        else:
            conta_afetada.saldo_atual -= valor_decimal

    if movimento.id_movimento_relacionado:
        movimento_relacionado = ContaMovimento.query.get(
            movimento.id_movimento_relacionado
        )
        if movimento_relacionado:
            conta_destino = Conta.query.get(movimento_relacionado.conta_id)
            if conta_destino:
                conta_destino.saldo_atual -= movimento_relacionado.valor

            movimento_relacionado.id_movimento_relacionado = None
            movimento.id_movimento_relacionado = None
            db.session.flush()

            db.session.delete(movimento_relacionado)

    db.session.delete(movimento)
    db.session.commit()
    flash("Movimentação excluída com sucesso!", "success")
    current_app.logger.info(
        f"Movimentação {movimento.id} excluída por {current_user.login}."
    )
    return redirect(url_for("conta_movimento.listar_movimentacoes"))
