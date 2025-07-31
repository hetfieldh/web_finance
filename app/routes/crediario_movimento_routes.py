# app/routes/crediario_movimento_routes.py

from datetime import date, datetime, timedelta
from decimal import Decimal

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
from app.forms.crediario_movimento_forms import (
    CadastroCrediarioMovimentoForm,
    EditarCrediarioMovimentoForm,
)
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela

crediario_movimento_bp = Blueprint(
    "crediario_movimento", __name__, url_prefix="/movimentos_crediario"
)


@crediario_movimento_bp.route("/")
@login_required
def listar_movimentos_crediario():
    movimentos_crediario = (
        CrediarioMovimento.query.filter_by(usuario_id=current_user.id)
        .order_by(CrediarioMovimento.data_compra.desc())
        .all()
    )
    return render_template(
        "crediario_movimentos/list.html", movimentos_crediario=movimentos_crediario
    )


@crediario_movimento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_movimento_crediario():
    form = CadastroCrediarioMovimentoForm()

    if form.validate_on_submit():
        crediario_id = form.crediario_id.data
        crediario_grupo_id = (
            form.crediario_grupo_id.data if form.crediario_grupo_id.data else None
        )
        data_compra = form.data_compra.data
        valor_total_compra = form.valor_total_compra.data
        descricao = form.descricao.data.strip()
        numero_parcelas = form.numero_parcelas.data

        if valor_total_compra <= 0:
            flash("O valor total da compra deve ser maior que zero.", "danger")
            return render_template("crediario_movimentos/add.html", form=form)

        if numero_parcelas <= 0:
            flash("O número de parcelas deve ser no mínimo 1.", "danger")
            return render_template("crediario_movimentos/add.html", form=form)

        try:
            novo_movimento = CrediarioMovimento(
                usuario_id=current_user.id,
                crediario_id=crediario_id,
                crediario_grupo_id=crediario_grupo_id,
                data_compra=data_compra,
                valor_total_compra=valor_total_compra,
                descricao=descricao,
                numero_parcelas=numero_parcelas,
            )
            db.session.add(novo_movimento)
            db.session.flush()

            valor_por_parcela = valor_total_compra / Decimal(str(numero_parcelas))

            for i in range(1, numero_parcelas + 1):
                mes_vencimento = data_compra.month + i
                ano_vencimento = data_compra.year
                while mes_vencimento > 12:
                    mes_vencimento -= 12
                    ano_vencimento += 1

                dia_vencimento = min(
                    data_compra.day,
                    (
                        (
                            datetime(ano_vencimento, mes_vencimento + 1, 1)
                            - timedelta(days=1)
                        ).day
                        if mes_vencimento < 12
                        else (
                            datetime(ano_vencimento + 1, 1, 1) - timedelta(days=1)
                        ).day
                    ),
                )

                data_vencimento = date(ano_vencimento, mes_vencimento, dia_vencimento)

                nova_parcela = CrediarioParcela(
                    crediario_movimento_id=novo_movimento.id,
                    numero_parcela=i,
                    data_vencimento=data_vencimento,
                    valor_parcela=valor_por_parcela,
                    pago=False,
                )
                db.session.add(nova_parcela)

            db.session.commit()
            flash(
                "Compra no crediário registrada e parcelas geradas com sucesso!",
                "success",
            )
            current_app.logger.info(
                f"Movimento de crediário (ID: {novo_movimento.id}) de R$ {valor_total_compra} em {numero_parcelas}x registrado por {current_user.login}."
            )
            return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro de integridade ao adicionar movimento de crediário: {e}",
                exc_info=True,
            )
            flash(
                "Erro ao registrar movimento de crediário. Verifique os dados e tente novamente.",
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro inesperado ao adicionar movimento de crediário: {e}",
                exc_info=True,
            )
            flash("Ocorreu um erro inesperado. Tente novamente.", "danger")

    return render_template("crediario_movimentos/add.html", form=form)


@crediario_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimento_crediario(id):
    movimento = CrediarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarCrediarioMovimentoForm()

    if form.validate_on_submit():
        movimento.descricao = form.descricao.data.strip()

        db.session.commit()
        flash("Movimento de crediário atualizado com sucesso!", "success")
        current_app.logger.info(
            f"Movimento de crediário (ID: {movimento.id}) atualizado por {current_user.login}."
        )
        return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))

    elif request.method == "GET":
        form.crediario_id.data = movimento.crediario_id
        form.crediario_grupo_id.data = movimento.crediario_grupo_id
        form.data_compra.data = movimento.data_compra
        form.valor_total_compra.data = movimento.valor_total_compra
        form.descricao.data = movimento.descricao
        form.numero_parcelas.data = movimento.numero_parcelas

    return render_template(
        "crediario_movimentos/edit.html", form=form, movimento=movimento
    )


@crediario_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimento_crediario(id):
    movimento = CrediarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    ultima_movimentacao = (
        CrediarioMovimento.query.filter_by(
            crediario_id=movimento.crediario_id, usuario_id=current_user.id
        )
        .order_by(CrediarioMovimento.data_compra.desc(), CrediarioMovimento.id.desc())
        .first()
    )

    if ultima_movimentacao and ultima_movimentacao.id != movimento.id:
        flash(
            "Não é possível excluir esta compra. Apenas a última compra (mais recente) do crediário pode ser excluída.",
            "danger",
        )
        return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))

    if any(parcela.pago for parcela in movimento.parcelas):
        flash(
            "Não é possível excluir esta compra. Existem parcelas associadas que já foram pagas.",
            "danger",
        )
        return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))

    db.session.delete(movimento)
    db.session.commit()
    flash("Compra no crediário excluída com sucesso!", "success")
    current_app.logger.info(
        f"Movimento de crediário (ID: {movimento.id}) excluído por {current_user.login}."
    )
    return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))
