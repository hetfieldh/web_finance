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
from app.models.conta_transacao_model import ContaTransacao
from app.forms.conta_movimento_forms import (
    CadastroContaMovimentoForm,
    EditarContaMovimentoForm,
)
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

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
        is_transferencia = form.is_transferencia.data
        conta_destino_id = form.conta_destino_id.data if is_transferencia else None

        conta_origem = Conta.query.get(conta_origem_id)
        tipo_transacao = ContaTransacao.query.get(tipo_transacao_id)
        conta_destino = Conta.query.get(conta_destino_id) if is_transferencia else None

        if not conta_origem or not tipo_transacao:
            flash("Erro: Conta ou Tipo de Transação inválidos.", "danger")
            return render_template("conta_movimentos/add.html", form=form)

        if tipo_transacao.tipo == "Débito":
            tipos_com_limite = ["Corrente", "Digital"]

            saldo_atual_decimal = Decimal(str(conta_origem.saldo_atual))
            valor_decimal = Decimal(str(valor))

            if saldo_atual_decimal >= valor_decimal:
                pass
            elif (
                conta_origem.tipo in tipos_com_limite
                and conta_origem.limite is not None
            ):
                limite_decimal = Decimal(str(conta_origem.limite))
                if (saldo_atual_decimal + limite_decimal) >= valor_decimal:
                    flash(
                        f"Atenção: Saldo insuficiente. Esta movimentação utilizará R$ {(valor_decimal - saldo_atual_decimal):.2f} do seu limite.",
                        "warning",
                    )
                else:
                    flash(
                        "Saldo insuficiente e/ou limite não disponível para esta movimentação.",
                        "danger",
                    )
                    return render_template("conta_movimentos/add.html", form=form)
            else:
                flash(
                    "Saldo insuficiente e/ou limite não disponível para esta movimentação.",
                    "danger",
                )
                return render_template("conta_movimentos/add.html", form=form)

        if is_transferencia:
            if not conta_destino:
                flash("Erro: Conta de destino inválida para transferência.", "danger")
                return render_template("conta_movimentos/add.html", form=form)
            if conta_origem.id == conta_destino.id:
                flash(
                    "A conta de origem e a conta de destino não podem ser a mesma.",
                    "danger",
                )
                return render_template("conta_movimentos/add.html", form=form)
            if tipo_transacao.tipo != "Débito":
                flash(
                    'Para transferências, o tipo de movimento da transação de origem deve ser "Débito".',
                    "danger",
                )
                return render_template("conta_movimentos/add.html", form=form)

            tipo_transacao_credito = ContaTransacao.query.filter_by(
                usuario_id=current_user.id,
                transacao_tipo=tipo_transacao.transacao_tipo,
                tipo="Crédito",
            ).first()

            if not tipo_transacao_credito:
                flash(
                    f'Erro: Não foi encontrado um tipo de transação "{tipo_transacao.transacao_tipo}" do tipo "Crédito" para a conta de destino.',
                    "danger",
                )
                db.session.rollback()
                return render_template("conta_movimentos/add.html", form=form)

        try:
            movimento_origem = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_origem_id,
                conta_transacao_id=tipo_transacao_id,
                data_movimento=data_movimento,
                valor=valor,
                descricao=descricao,
            )
            db.session.add(movimento_origem)
            db.session.flush()

            if tipo_transacao.tipo == "Débito":
                conta_origem.saldo_atual = Decimal(
                    str(conta_origem.saldo_atual)
                ) - Decimal(str(valor))
            elif tipo_transacao.tipo == "Crédito":
                conta_origem.saldo_atual = Decimal(
                    str(conta_origem.saldo_atual)
                ) + Decimal(str(valor))

            if is_transferencia:
                movimento_destino = ContaMovimento(
                    usuario_id=current_user.id,
                    conta_id=conta_destino_id,
                    conta_transacao_id=tipo_transacao_credito.id,
                    data_movimento=data_movimento,
                    valor=valor,
                    descricao=f"Transferência recebida de {conta_origem.nome_banco} - {conta_origem.conta}",
                )
                db.session.add(movimento_destino)
                db.session.flush()

                conta_destino.saldo_atual = Decimal(
                    str(conta_destino.saldo_atual)
                ) + Decimal(str(valor))

                movimento_origem.id_movimento_relacionado = movimento_destino.id
                movimento_destino.id_movimento_relacionado = movimento_origem.id

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

    conta_afetada = Conta.query.get(movimento.conta_id)
    tipo_transacao = ContaTransacao.query.get(movimento.conta_transacao_id)

    if conta_afetada and tipo_transacao:
        conta_afetada.saldo_atual = Decimal(str(conta_afetada.saldo_atual))
        movimento.valor = Decimal(str(movimento.valor))

        if tipo_transacao.tipo == "Débito":
            conta_afetada.saldo_atual += movimento.valor
        else:
            conta_afetada.saldo_atual -= movimento.valor

    if movimento.id_movimento_relacionado:
        movimento_relacionado = ContaMovimento.query.get(
            movimento.id_movimento_relacionado
        )
        if movimento_relacionado:
            conta_destino_afetada = Conta.query.get(movimento_relacionado.conta_id)
            tipo_transacao_destino = ContaTransacao.query.get(
                movimento_relacionado.conta_transacao_id
            )
            if conta_destino_afetada and tipo_transacao_destino:
                conta_destino_afetada.saldo_atual = Decimal(
                    str(conta_destino_afetada.saldo_atual)
                )
                movimento_relacionado.valor = Decimal(str(movimento_relacionado.valor))

                if tipo_transacao_destino.tipo == "Crédito":
                    conta_destino_afetada.saldo_atual -= movimento_relacionado.valor
                else:
                    conta_destino_afetada.saldo_atual += movimento_relacionado.valor

            db.session.delete(movimento_relacionado)

    db.session.delete(movimento)
    db.session.commit()
    flash("Movimentação excluída com sucesso!", "success")
    current_app.logger.info(
        f"Movimentação {movimento.id} excluída por {current_user.login} (ID: {current_user.id})"
    )
    return redirect(url_for("conta_movimento.listar_movimentacoes"))
