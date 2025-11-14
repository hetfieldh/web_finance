# app/routes/pagamentos_routes.py

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

from app.forms.pagamentos_forms import PagamentoForm, PainelPagamentosForm
from app.models.conta_model import Conta
from app.services import conta_service, pagamento_service
from app.services.pagamento_service import (
    estornar_pagamento as estornar_pagamento_service,
)

pagamentos_bp = Blueprint("pagamentos", __name__, url_prefix="/pagamentos")


@pagamentos_bp.route("/painel", methods=["GET"])
@login_required
def painel():
    form = PainelPagamentosForm(request.args)
    pagamento_form = PagamentoForm()
    contas_ativas = Conta.query.filter_by(usuario_id=current_user.id, ativa=True).all()
    contas_json = [
        {
            "id": conta.id,
            "nome": conta.nome_banco,
            "tipo": conta.tipo,
            "saldo_atual": float(conta.saldo_atual),
            "limite": float(conta.limite or 0),
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

    contas_a_pagar = pagamento_service.get_contas_a_pagar_por_mes(ano, mes)

    totais = {
        "previsto": sum(
            c.get("valor_display", Decimal("0.00")) for c in contas_a_pagar
        ),
        "pago": sum(c.get("valor_pago", Decimal("0.00")) for c in contas_a_pagar),
    }
    totais["pendente"] = totais["previsto"] - totais["pago"]

    return render_template(
        "pagamentos/painel.html",
        form=form,
        pagamento_form=pagamento_form,
        contas=contas_a_pagar,
        totais=totais,
        contas_json=contas_json,
        title="Painel de Pagamentos",
        today=date.today(),
    )


@pagamentos_bp.route("/registrar", methods=["POST"])
@login_required
def registrar_pagamento():
    account_choices = conta_service.get_active_accounts_for_user_choices()
    form = PagamentoForm(request.form, account_choices=account_choices)

    form.item_id.data = request.form.get("item_id", type=int)
    form.item_tipo.data = request.form.get("item_tipo")
    form.item_descricao.data = request.form.get("item_descricao")
    form.data_pagamento.data = request.form.get(
        "data_pagamento", type=lambda x: date.fromisoformat(x) if x else None
    )
    form.valor_pago.data = request.form.get("valor_pago", type=Decimal)
    form.conta_id.data = request.form.get("conta_id", type=int)

    if (
        not form.data_pagamento.data
        or not form.valor_pago.data
        or not form.conta_id.data
        or not form.item_id.data
    ):
        flash(
            "Erro de validação: Campos obrigatórios (data, valor, conta, item) não foram preenchidos.",
            "danger",
        )
        return redirect(request.referrer or url_for("main.dashboard"))

    try:
        success, message = pagamento_service.registrar_pagamento(form)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
    except Exception as e:
        current_app.logger.error(
            f"Erro ao registrar pagamento (rota): {e}", exc_info=True
        )
        flash(f"Erro ao registrar pagamento: {str(e)}", "danger")

    return redirect(request.referrer or url_for("main.dashboard"))


@pagamentos_bp.route("/estornar", methods=["POST"])
@login_required
def estornar_pagamento():
    item_id = request.form.get("item_id")
    item_tipo = request.form.get("item_tipo")
    mes_ano = request.form.get("mes_ano")

    success, message = estornar_pagamento_service(item_id, item_tipo)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(request.referrer or url_for("pagamentos.painel", mes_ano=mes_ano))
