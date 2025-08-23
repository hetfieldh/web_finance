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
from app.forms.crediario_fatura_forms import GerarFaturaForm
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.services import (
    crediario_service,
    fatura_service,
)
from app.services.fatura_service import (
    gerar_fatura as gerar_fatura_service,
)
from app.services.fatura_service import (
    recalcular_fatura as recalcular_fatura_service,
)

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
        .order_by(CrediarioFatura.mes_referencia.desc())
        .all()
    )

    faturas_com_status = []
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
        faturas_com_status.append({"fatura": fatura, "desatualizada": desatualizada})

    return render_template(
        "crediario_faturas/list.html",
        faturas=faturas_com_status,
        form=form,
    )


@crediario_fatura_bp.route("/gerar", methods=["GET", "POST"])
@login_required
def gerar_fatura():
    crediario_choices = crediario_service.get_active_crediarios_for_user_choices()
    form = GerarFaturaForm(crediario_choices=crediario_choices)
    if form.validate_on_submit():
        crediario_id = form.crediario_id.data
        mes_ano_str = form.mes_ano.data

        success, message, fatura_obj = gerar_fatura_service(crediario_id, mes_ano_str)

        if success:
            flash(message, "success")
            return redirect(url_for("crediario_fatura.listar_faturas"))
        else:
            flash(message, "warning" if fatura_obj else "danger")
            if fatura_obj:
                return redirect(
                    url_for("crediario_fatura.visualizar_fatura", id=fatura_obj.id)
                )
            return redirect(url_for("crediario_fatura.gerar_fatura"))

    if request.method == "GET":
        if form.crediario_id.choices and len(form.crediario_id.choices) > 1:
            form.crediario_id.data = form.crediario_id.choices[1][0]

        hoje = date.today()
        mes_atual_str = f"{hoje.year}-{hoje.month:02d}"
        if any(choice[0] == mes_atual_str for choice in form.mes_ano.choices):
            form.mes_ano.data = mes_atual_str

    return render_template("crediario_faturas/gerar.html", form=form)


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


@crediario_fatura_bp.route("/recalcular/<int:id>", methods=["POST"])
@login_required
def recalcular_fatura(id):
    success, message = recalcular_fatura_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("crediario_fatura.listar_faturas"))


@crediario_fatura_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_fatura(id):
    fatura = CrediarioFatura.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if fatura.status in ["Paga", "Parcialmente Paga"]:
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
