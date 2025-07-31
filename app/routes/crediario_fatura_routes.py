# app/routes/crediario_fatura_routes.py

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
from sqlalchemy import extract, func
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.crediario_fatura_forms import GerarFaturaForm
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela

crediario_fatura_bp = Blueprint(
    "crediario_fatura", __name__, url_prefix="/faturas_crediario"
)


@crediario_fatura_bp.route("/")
@login_required
def listar_faturas():
    faturas = (
        CrediarioFatura.query.filter_by(usuario_id=current_user.id)
        .order_by(CrediarioFatura.mes_referencia.desc())
        .all()
    )
    return render_template("crediario_faturas/list.html", faturas=faturas)


@crediario_fatura_bp.route("/gerar", methods=["GET", "POST"])
@login_required
def gerar_fatura():
    form = GerarFaturaForm()
    fatura_existente = None
    parcelas_do_mes = []
    valor_total_calculado = Decimal("0.00")
    crediario_selecionado = None

    if form.validate_on_submit():
        crediario_id = form.crediario_id.data
        mes_ano_str = form.mes_ano.data

        crediario_selecionado = Crediario.query.filter_by(
            id=crediario_id, usuario_id=current_user.id
        ).first()
        if not crediario_selecionado:
            flash("Crediário inválido.", "danger")
            return render_template("crediario_faturas/gerar.html", form=form)

        ano = int(mes_ano_str.split("-")[0])
        mes = int(mes_ano_str.split("-")[1])

        fatura_existente = CrediarioFatura.query.filter_by(
            usuario_id=current_user.id,
            crediario_id=crediario_id,
            mes_referencia=mes_ano_str,
        ).first()

        data_inicio_mes = date(ano, mes, 1)
        if mes == 12:
            data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

        parcelas_do_mes = (
            CrediarioParcela.query.filter(
                CrediarioParcela.crediario_movimento_id.in_(
                    db.session.query(CrediarioMovimento.id).filter(
                        CrediarioMovimento.crediario_id == crediario_id,
                        CrediarioMovimento.usuario_id == current_user.id,
                    )
                ),
                CrediarioParcela.data_vencimento >= data_inicio_mes,
                CrediarioParcela.data_vencimento <= data_fim_mes,
            )
            .order_by(
                CrediarioParcela.data_vencimento.asc(),
                CrediarioParcela.numero_parcela.asc(),
            )
            .all()
        )

        for parcela in parcelas_do_mes:
            valor_total_calculado += parcela.valor_parcela

        if fatura_existente:
            flash(
                "Fatura para este período e crediário já existe. Visualizando...",
                "info",
            )
            return redirect(
                url_for("crediario_fatura.visualizar_fatura", id=fatura_existente.id)
            )
        else:
            if valor_total_calculado > 0:
                try:
                    data_vencimento_fatura = data_fim_mes

                    nova_fatura = CrediarioFatura(
                        usuario_id=current_user.id,
                        crediario_id=crediario_id,
                        mes_referencia=mes_ano_str,
                        valor_total_fatura=valor_total_calculado,
                        valor_pago_fatura=Decimal("0.00"),
                        data_fechamento=date.today(),
                        data_vencimento_fatura=data_vencimento_fatura,
                        status="Aberta",
                    )
                    db.session.add(nova_fatura)
                    db.session.commit()
                    flash("Fatura gerada com sucesso!", "success")
                    current_app.logger.info(
                        f"Fatura (ID: {nova_fatura.id}) para {crediario_selecionado.nome_crediario} ({mes_ano_str}) gerada por {current_user.login}."
                    )
                    return redirect(url_for("crediario_fatura.listar_faturas"))
                except IntegrityError as e:
                    db.session.rollback()
                    current_app.logger.error(
                        f"Erro de integridade ao gerar fatura: {e}", exc_info=True
                    )
                    flash(
                        "Erro ao gerar fatura. Verifique se já não existe uma fatura para este crediário e mês.",
                        "danger",
                    )
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(
                        f"Erro inesperado ao gerar fatura: {e}", exc_info=True
                    )
                    flash(
                        "Ocorreu um erro inesperado ao gerar fatura. Tente novamente.",
                        "danger",
                    )
            else:
                flash("Não há movimentações para gerar fatura neste período.", "warning")
                return redirect(url_for("crediario_fatura.listar_faturas"))

    elif request.method == "GET":
        if form.crediario_id.choices and len(form.crediario_id.choices) > 1:
            form.crediario_id.data = form.crediario_id.choices[1][0]

        hoje = date.today()
        mes_atual_str = f"{hoje.year}-{hoje.month:02d}"
        if any(choice[0] == mes_atual_str for choice in form.mes_ano.choices):
            form.mes_ano.data = mes_atual_str

    return render_template(
        "crediario_faturas/gerar.html",
        form=form,
        fatura_existente=fatura_existente,
        parcelas_do_mes=parcelas_do_mes,
        valor_total_calculado=valor_total_calculado,
        crediario_selecionado=crediario_selecionado,
    )


@crediario_fatura_bp.route("/<int:id>")
@login_required
def visualizar_fatura(id):
    fatura = CrediarioFatura.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    ano = int(fatura.mes_referencia.split("-")[0])
    mes = int(fatura.mes_referencia.split("-")[1])
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    parcelas_da_fatura = (
        CrediarioParcela.query.filter(
            CrediarioParcela.crediario_movimento_id.in_(
                db.session.query(CrediarioMovimento.id).filter(
                    CrediarioMovimento.crediario_id == fatura.crediario_id,
                    CrediarioMovimento.usuario_id == current_user.id,
                )
            ),
            CrediarioParcela.data_vencimento >= data_inicio_mes,
            CrediarioParcela.data_vencimento <= data_fim_mes,
        )
        .order_by(
            CrediarioParcela.data_vencimento.asc(),
            CrediarioParcela.numero_parcela.asc(),
        )
        .all()
    )

    return render_template(
        "crediario_faturas/view.html",
        fatura=fatura,
        parcelas_da_fatura=parcelas_da_fatura,
    )


@crediario_fatura_bp.route("/recalcular/<int:id>", methods=["POST"])
@login_required
def recalcular_fatura(id):
    fatura = CrediarioFatura.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if fatura.status == "Paga" or fatura.status == "Parcialmente Paga":
        flash(
            "Não é possível recalcular uma fatura que já está paga ou parcialmente paga.",
            "danger",
        )
        return redirect(url_for("crediario_fatura.listar_faturas"))

    ano = int(fatura.mes_referencia.split("-")[0])
    mes = int(fatura.mes_referencia.split("-")[1])
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

    valor_total_recalculado = (
        db.session.query(
            func.coalesce(func.sum(CrediarioParcela.valor_parcela), Decimal("0.00"))
        )
        .join(CrediarioMovimento)
        .filter(
            CrediarioMovimento.id == CrediarioParcela.crediario_movimento_id,
            CrediarioMovimento.crediario_id == fatura.crediario_id,
            CrediarioMovimento.usuario_id == current_user.id,
            CrediarioParcela.data_vencimento >= data_inicio_mes,
            CrediarioParcela.data_vencimento <= data_fim_mes,
        )
        .scalar()
    )

    try:
        fatura.valor_total_fatura = valor_total_recalculado
        db.session.commit()
        flash("Fatura atualizada com sucesso!", "success")
        current_app.logger.info(
            f"Fatura (ID: {fatura.id}) recalculada por {current_user.login}."
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Erro ao recalcular fatura (ID: {fatura.id}): {e}", exc_info=True
        )
        flash("Ocorreu um erro ao atualizar a fatura. Tente novamente.", "danger")

    return redirect(url_for("crediario_fatura.listar_faturas"))


@crediario_fatura_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_fatura(id):
    fatura = CrediarioFatura.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if fatura.status == "Paga" or fatura.status == "Parcialmente Paga":
        flash(
            "Não é possível excluir uma fatura que já está paga ou parcialmente paga.",
            "danger",
        )
        return redirect(url_for("crediario_fatura.listar_faturas"))

    db.session.delete(fatura)
    db.session.commit()
    flash("Fatura excluída com sucesso!", "success")
    current_app.logger.info(
        f"Fatura (ID: {fatura.id}) excluída por {current_user.login}."
    )
    return redirect(url_for("crediario_fatura.listar_faturas"))
