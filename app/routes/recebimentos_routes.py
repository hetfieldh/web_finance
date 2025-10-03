# app/routes/recebimentos_routes.py

import json
from datetime import date
from decimal import Decimal

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.forms.recebimentos_forms import PainelRecebimentosForm, RecebimentoForm
from app.models.conta_model import Conta
from app.services import conta_service, recebimento_service, salario_service
from app.services.recebimento_service import (
    estornar_recebimento as estornar_recebimento_service,
)
from app.services.recebimento_service import (
    registrar_recebimento as registrar_recebimento_service,
)

recebimentos_bp = Blueprint("recebimentos", __name__, url_prefix="/recebimentos")


@recebimentos_bp.route("/painel", methods=["GET"])
@login_required
def painel():
    form = PainelRecebimentosForm(request.args)

    account_choices = conta_service.get_active_accounts_for_user_choices()
    recebimento_form = RecebimentoForm(account_choices=account_choices)

    contas_ativas = Conta.query.filter_by(usuario_id=current_user.id, ativa=True).all()
    contas_para_js = [
        {
            "id": conta.id,
            "nome": conta.nome_banco,
            "tipo": conta.tipo,
            "saldo_atual": float(conta.saldo_atual),
        }
        for conta in contas_ativas
    ]

    mes_ano_str = form.mes_ano.data
    if not mes_ano_str:
        mes_ano_str = date.today().strftime("%m-%Y")
        form.mes_ano.data = mes_ano_str

    try:
        mes, ano = map(int, mes_ano_str.split("-"))
    except ValueError:
        flash("Formato de Mês/Ano inválido.", "danger")
        hoje = date.today()
        mes, ano = hoje.month, hoje.year
        mes_ano_str = hoje.strftime("%m-%Y")
        form.mes_ano.data = mes_ano_str

    contas_a_receber = recebimento_service.get_contas_a_receber_por_mes(ano, mes)

    totais = {
        "previsto": sum(
            c.get("valor_previsto", Decimal("0.00")) for c in contas_a_receber
        ),
        "recebido": sum(
            c.get("valor_recebido", Decimal("0.00")) for c in contas_a_receber
        ),
    }
    totais["pendente"] = totais["previsto"] - totais["recebido"]

    fgts_info = {
        "has_account": conta_service.has_fgts_account(),
        "has_item": salario_service.has_fgts_salario_item(),
    }

    return render_template(
        "recebimentos/painel.html",
        form=form,
        recebimento_form=recebimento_form,
        contas=contas_a_receber,
        totais=totais,
        contas_para_js=contas_para_js,
        title="Painel de Recebimentos",
        fgts_info_json=json.dumps(fgts_info),
    )


@recebimentos_bp.route("/registrar", methods=["POST"])
@login_required
def registrar_recebimento():
    account_choices = conta_service.get_active_accounts_for_user_choices()
    form = RecebimentoForm(request.form, account_choices=account_choices)

    if form.validate_on_submit():
        success, message = registrar_recebimento_service(form)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(
                    f"Erro no campo '{getattr(form, field).label.text}': {error}",
                    "danger",
                )

    return redirect(url_for("recebimentos.painel", mes_ano=request.form.get("mes_ano")))


@recebimentos_bp.route("/estornar", methods=["POST"])
@login_required
def estornar_recebimento():
    item_id = request.form.get("item_id")
    item_tipo = request.form.get("item_tipo")

    success, message = estornar_recebimento_service(item_id, item_tipo)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("recebimentos.painel", mes_ano=request.form.get("mes_ano")))
