# app/routes/crediario_fatura_routes.py

import calendar
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
from sqlalchemy import and_, func
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
    data_inicial_str = request.args.get("data_inicial")
    data_final_str = request.args.get("data_final")

    hoje = date.today()

    query = CrediarioFatura.query.filter_by(usuario_id=current_user.id).options(
        joinedload(CrediarioFatura.crediario)
    )

    try:
        if data_inicial_str:
            data_inicial = date.fromisoformat(data_inicial_str)
            query = query.filter(CrediarioFatura.data_vencimento_fatura >= data_inicial)
        if data_final_str:
            data_final = date.fromisoformat(data_final_str)
            query = query.filter(CrediarioFatura.data_vencimento_fatura <= data_final)
    except ValueError:
        flash("Formato de data inválido. Use DD-MM-AAAA.", "danger")
        return redirect(url_for("crediario_fatura.listar_faturas"))

    faturas = query.order_by(CrediarioFatura.data_vencimento_fatura.asc()).all()

    faturas_com_status = []

    for fatura in faturas:
        ano_ref = int(fatura.mes_referencia.split("-")[0])
        mes_ref = int(fatura.mes_referencia.split("-")[1])
        data_inicio_mes = date(ano_ref, mes_ref, 1)
        if mes_ref == 12:
            data_fim_mes = date(ano_ref + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim_mes = date(ano_ref, mes_ref + 1, 1) - timedelta(days=1)

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
        data_inicial=data_inicial_str,
        data_final=data_final_str,
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


# --- ADICIONE ESTA NOVA ROTA NO FINAL DO ARQUIVO ---
@crediario_fatura_bp.route("/excluir_em_massa", methods=["POST"])
@login_required
def excluir_em_massa():
    # Pega os IDs enviados pelos checkboxes (name="item_ids")
    ids = request.form.getlist("item_ids")

    if not ids:
        flash("Nenhuma fatura selecionada.", "warning")
        return redirect(url_for("crediario_fatura.listar_faturas"))

    # Busca as faturas no banco (garantindo que pertencem ao usuário logado)
    faturas = CrediarioFatura.query.filter(
        CrediarioFatura.id.in_(ids), CrediarioFatura.usuario_id == current_user.id
    ).all()

    count = 0
    ignoradas = 0

    for fatura in faturas:
        # Proteção: Não excluir faturas pagas ou parciais
        if fatura.status in [STATUS_PAGO, STATUS_PARCIAL_PAGO]:
            ignoradas += 1
        else:
            db.session.delete(fatura)
            count += 1

    db.session.commit()

    msg = f"{count} fatura(s) excluída(s) com sucesso."
    category = "success"

    if ignoradas > 0:
        msg += f" {ignoradas} fatura(s) pagas foram ignoradas."
        if count == 0:
            category = "warning"

    flash(msg, category)
    return redirect(url_for("crediario_fatura.listar_faturas"))
