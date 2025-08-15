# app/routes/crediario_movimento_routes.py

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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

getcontext().prec = 10

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from app import db
from app.forms.crediario_movimento_forms import (
    CadastroCrediarioMovimentoForm,
    EditarCrediarioMovimentoForm,
)
from app.models.crediario_fatura_model import CrediarioFatura
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
    form = CadastroCrediarioMovimentoForm()

    if form.validate_on_submit():
        crediario_id = form.crediario_id.data
        crediario_grupo_id = (
            form.crediario_grupo_id.data if form.crediario_grupo_id.data else None
        )
        data_compra = form.data_compra.data
        valor_total_compra = form.valor_total_compra.data
        descricao = form.descricao.data.strip()
        data_primeira_parcela_obj = form.data_primeira_parcela.data
        numero_parcelas = form.numero_parcelas.data

        mes_ano_referencia = data_primeira_parcela_obj.strftime("%Y-%m")
        fatura_existente = CrediarioFatura.query.filter_by(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            mes_referencia=mes_ano_referencia,
        ).first()

        if fatura_existente and fatura_existente.status in [
            "Paga",
            "Parcialmente Paga",
        ]:
            flash(
                f"Não é possível adicionar uma compra cuja primeira parcela vence em {mes_ano_referencia.split('-')[1]}/{mes_ano_referencia.split('-')[0]}, pois a fatura para este período já foi paga.",
                "danger",
            )
            return render_template("crediario_movimentos/add.html", form=form)

        valor_final_compra = valor_total_compra
        if crediario_grupo_id:
            grupo = CrediarioGrupo.query.get(crediario_grupo_id)
            if grupo and grupo.tipo_grupo_crediario == "Estorno":
                valor_final_compra = -valor_total_compra

        if numero_parcelas <= 0:
            flash("O número de parcelas deve ser no mínimo 1.", "danger")
            return render_template("crediario_movimentos/add.html", form=form)

        try:
            novo_movimento = CrediarioMovimento(
                usuario_id=current_user.id,
                crediario_id=crediario_id,
                crediario_grupo_id=crediario_grupo_id,
                data_compra=data_compra,
                valor_total_compra=valor_final_compra,
                descricao=descricao,
                data_primeira_parcela=data_primeira_parcela_obj,
                numero_parcelas=numero_parcelas,
            )
            db.session.add(novo_movimento)
            db.session.flush()

            valor_por_parcela = valor_final_compra / Decimal(str(numero_parcelas))

            for i in range(numero_parcelas):
                data_vencimento = data_primeira_parcela_obj + relativedelta(months=i)
                nova_parcela = CrediarioParcela(
                    crediario_movimento_id=novo_movimento.id,
                    numero_parcela=i + 1,
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
            return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))

        except Exception as e:
            db.session.rollback()
            flash("Ocorreu um erro inesperado. Tente novamente.", "danger")

    return render_template("crediario_movimentos/add.html", form=form)


@crediario_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimento_crediario(id):
    movimento = CrediarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarCrediarioMovimentoForm(obj=movimento)

    if form.validate_on_submit():
        nova_data_primeira_parcela = form.data_primeira_parcela.data
        mes_ano_referencia = nova_data_primeira_parcela.strftime("%Y-%m")

        if nova_data_primeira_parcela != movimento.data_primeira_parcela:
            fatura_existente = CrediarioFatura.query.filter_by(
                usuario_id=current_user.id,
                crediario_id=movimento.crediario_id,
                mes_referencia=mes_ano_referencia,
            ).first()

            if fatura_existente and fatura_existente.status in [
                "Paga",
                "Parcialmente Paga",
            ]:
                flash(
                    f"Não é possível mover a primeira parcela para {mes_ano_referencia.split('-')[1]}/{mes_ano_referencia.split('-')[0]}, pois a fatura para este período já foi paga.",
                    "danger",
                )
                return render_template(
                    "crediario_movimentos/edit.html", form=form, movimento=movimento
                )

        valor_total_compra = form.valor_total_compra.data
        if (
            movimento.crediario_grupo
            and movimento.crediario_grupo.tipo_grupo_crediario == "Estorno"
        ):
            valor_total_compra = -abs(valor_total_compra)

        if any(p.pago for p in movimento.parcelas):
            flash(
                "Não é possível editar esta compra, pois ela possui parcelas que já foram pagas.",
                "danger",
            )
            return render_template(
                "crediario_movimentos/edit.html", form=form, movimento=movimento
            )

        movimento.data_compra = form.data_compra.data
        movimento.valor_total_compra = valor_total_compra
        movimento.data_primeira_parcela = form.data_primeira_parcela.data
        movimento.numero_parcelas = form.numero_parcelas.data
        movimento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )

        for parcela in movimento.parcelas:
            db.session.delete(parcela)
        db.session.flush()

        valor_por_parcela = valor_total_compra / Decimal(str(form.numero_parcelas.data))
        for i in range(form.numero_parcelas.data):
            data_vencimento = form.data_primeira_parcela.data + relativedelta(months=i)
            nova_parcela = CrediarioParcela(
                crediario_movimento_id=movimento.id,
                numero_parcela=i + 1,
                data_vencimento=data_vencimento,
                valor_parcela=valor_por_parcela,
                pago=False,
            )
            db.session.add(nova_parcela)

        try:
            db.session.commit()
            flash("Movimento de crediário atualizado com sucesso!", "success")
            return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))
        except Exception as e:
            db.session.rollback()
            flash("Ocorreu um erro ao atualizar a compra. Tente novamente.", "danger")
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
    movimento = CrediarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    for parcela in movimento.parcelas:
        mes_referencia = parcela.data_vencimento.strftime("%Y-%m")
        fatura = CrediarioFatura.query.filter_by(
            crediario_id=movimento.crediario_id,
            usuario_id=current_user.id,
            mes_referencia=mes_referencia,
        ).first()
        if fatura:
            flash(
                f"Não é possível excluir esta compra. A fatura do mês {mes_referencia} já foi gerada para o crediário.",
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
        f"Movimentação {movimento.id} excluída por {current_user.login}."
    )
    return redirect(url_for("crediario_movimento.listar_movimentos_crediario"))
