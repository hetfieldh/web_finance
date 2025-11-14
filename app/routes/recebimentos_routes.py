# app/routes/recebimentos_routes.py

import json
from datetime import date
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

from app import db
from app.forms.recebimentos_forms import PainelRecebimentosForm, RecebimentoForm
from app.models.conta_model import Conta
from app.services import conta_service, recebimento_service, salario_service
from app.services.recebimento_service import (
    estornar_recebimento as estornar_recebimento_service,
)

recebimentos_bp = Blueprint("recebimentos", __name__, url_prefix="/recebimentos")


@recebimentos_bp.route("/painel", methods=["GET"])
@login_required
def painel():
    form = PainelRecebimentosForm(request.args)
    recebimento_form = RecebimentoForm()
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

    fgts_info = {"has_account": conta_service.has_fgts_account()}

    return render_template(
        "recebimentos/painel.html",
        form=form,
        recebimento_form=recebimento_form,
        contas=contas_a_receber,
        totais=totais,
        contas_para_js=contas_para_js,
        title="Painel de Recebimentos",
        fgts_info_json=json.dumps(fgts_info),
        today=date.today(),
    )


@recebimentos_bp.route("/registrar", methods=["POST"])
@login_required
def registrar_recebimento():
    account_choices = conta_service.get_active_accounts_for_user_choices()
    form = RecebimentoForm(request.form, account_choices=account_choices)

    form.item_id.data = request.form.get("item_id", type=int)
    form.item_tipo.data = request.form.get("item_tipo")
    form.item_descricao.data = request.form.get("item_descricao")
    form.data_recebimento.data = request.form.get(
        "data_recebimento", type=lambda x: date.fromisoformat(x) if x else None
    )
    form.valor_recebido.data = request.form.get("valor_recebido", type=Decimal)
    form.conta_id.data = request.form.get("conta_id", type=int)

    if (
        not form.data_recebimento.data
        or not form.valor_recebido.data
        or not form.conta_id.data
        or not form.item_id.data
    ):
        flash(
            "Erro de validação: Campos obrigatórios (data, valor, conta, item) não foram preenchidos.",
            "danger",
        )
        return redirect(request.referrer or url_for("main.dashboard"))

    try:
        success, message = recebimento_service.registrar_recebimento(form)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
    except Exception as e:
        current_app.logger.error(
            f"Erro ao registrar recebimento (rota): {e}", exc_info=True
        )
        flash(f"Erro ao registrar recebimento: {str(e)}", "danger")

    return redirect(request.referrer or url_for("main.dashboard"))


@recebimentos_bp.route("/estornar", methods=["POST"])
@login_required
def estornar_recebimento():
    item_id = request.form.get("item_id")
    item_tipo = request.form.get("item_tipo")
    mes_ano = request.form.get("mes_ano")

    success, message = estornar_recebimento_service(item_id, item_tipo)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(request.referrer or url_for("recebimentos.painel", mes_ano=mes_ano))
