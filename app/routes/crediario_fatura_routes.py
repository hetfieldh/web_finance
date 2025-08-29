# app/routes/crediario_fatura_routes.py

from datetime import date, timedelta
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
from flask_wtf import FlaskForm
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.services import fatura_service
from app.utils import STATUS_ATRASADO, STATUS_PAGO, STATUS_PARCIAL_PAGO, STATUS_PENDENTE

crediario_fatura_bp = Blueprint(
    "crediario_fatura", __name__, url_prefix="/faturas_crediario"
)


@crediario_fatura_bp.route("/")
@login_required
def listar_faturas():
    form = FlaskForm()

    faturas = (
        CrediarioFatura.query.filter_by(usuario_id=current_user.id)
        .options(joinedload(CrediarioFatura.crediario))
        .order_by(CrediarioFatura.data_vencimento_fatura.asc())
        .all()
    )

    faturas_com_status = []
    hoje = date.today()

    for fatura in faturas:
        ano = int(fatura.mes_referencia.split("-")[0])
        mes = int(fatura.mes_referencia.split("-")[1])
        data_inicio_mes = date(ano, mes, 1)
        if mes == 12:
            data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)
        soma_real_parcelas = (
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
        desatualizada = fatura.valor_total_fatura != soma_real_parcelas

        destaque_status = ""
        if fatura.status in [STATUS_PENDENTE, STATUS_ATRASADO, STATUS_PARCIAL_PAGO]:
            if fatura.data_vencimento_fatura < hoje:
                destaque_status = STATUS_ATRASADO
            elif (
                fatura.data_vencimento_fatura.year == hoje.year
                and fatura.data_vencimento_fatura.month == hoje.month
            ):
                destaque_status = "vence_este_mes"

        faturas_com_status.append(
            {
                "fatura": fatura,
                "desatualizada": desatualizada,
                "destaque_status": destaque_status,
            }
        )

    return render_template(
        "crediario_faturas/list.html",
        faturas=faturas_com_status,
        form=form,
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
        .options(joinedload(CrediarioParcela.movimento_pai))
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


@crediario_fatura_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_fatura(id):
    fatura = CrediarioFatura.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if fatura.status in [STATUS_PAGO, STATUS_PARCIAL_PAGO]:
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


@crediario_fatura_bp.route("/automatizar", methods=["POST"])
@login_required
def automatizar_faturas():
    success, message = fatura_service.automatizar_geracao_e_atualizacao_faturas(
        current_user.id
    )
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("crediario_fatura.listar_faturas"))
