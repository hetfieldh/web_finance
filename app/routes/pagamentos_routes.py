# app/routes/pagamentos_routes.py

from datetime import date, timedelta
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
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.forms.pagamentos_forms import PagamentoForm, PainelPagamentosForm
from app.models.conta_movimento_model import ContaMovimento
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.services import conta_service
from app.services.pagamento_service import (
    estornar_pagamento as estornar_pagamento_service,
)
from app.services.pagamento_service import registrar_pagamento
from app.utils import STATUS_PAGO, STATUS_PENDENTE, STATUS_PREVISTO

pagamentos_bp = Blueprint("pagamentos", __name__, url_prefix="/pagamentos")


@pagamentos_bp.route("/painel", methods=["GET", "POST"])
@login_required
def painel():
    form = PainelPagamentosForm(request.args)
    account_choices = conta_service.get_active_accounts_for_user_choices()
    pagamento_form = PagamentoForm(account_choices=account_choices)

    mes_ano_str = form.mes_ano.data
    if not mes_ano_str:
        mes_ano_str = date.today().strftime("%m-%Y")
        form.mes_ano.data = mes_ano_str

    contas_a_pagar = []
    totais = {
        "Previsto": Decimal("0.00"),
        "Pago": Decimal("0.00"),
        "Pendente": Decimal("0.00"),
    }

    if mes_ano_str:
        try:
            mes, ano = map(int, mes_ano_str.split("-"))
            data_inicio_mes = date(ano, mes, 1)
            data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
                day=1
            ) - timedelta(days=1)
        except ValueError:
            flash("Formato de data inválido.", "danger")
            return redirect(url_for("pagamentos.painel"))

        faturas = (
            CrediarioFatura.query.filter(
                CrediarioFatura.usuario_id == current_user.id,
                CrediarioFatura.data_vencimento_fatura.between(
                    data_inicio_mes, data_fim_mes
                ),
            )
            .options(
                joinedload(CrediarioFatura.crediario),
                joinedload(CrediarioFatura.movimento_bancario).joinedload(
                    ContaMovimento.conta
                ),
            )
            .all()
        )

        parcelas = (
            FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
            .filter(
                FinanciamentoParcela.data_vencimento.between(
                    data_inicio_mes, data_fim_mes
                ),
                FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            )
            .options(
                joinedload(FinanciamentoParcela.financiamento),
                joinedload(FinanciamentoParcela.movimento_bancario).joinedload(
                    ContaMovimento.conta
                ),
            )
            .all()
        )

        despesas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
                DespRecMovimento.despesa_receita.has(natureza="Despesa"),
            )
            .options(
                joinedload(DespRecMovimento.despesa_receita),
                joinedload(DespRecMovimento.movimento_bancario).joinedload(
                    ContaMovimento.conta
                ),
            )
            .all()
        )

        def adicionar_conta_a_pagar(item, tipo):
            pago_com = ""
            if item.movimento_bancario and item.movimento_bancario.conta:
                conta = item.movimento_bancario.conta
                pago_com = f"{conta.nome_banco} ({conta.tipo})"

            item_dict = {}
            if tipo == "Crediário":
                item_dict.update(
                    {
                        "vencimento": item.data_vencimento_fatura,
                        "origem": f"FATURA {item.crediario.nome_crediario}",
                        "valor_display": item.valor_total_fatura,
                        "valor_pago": item.valor_pago_fatura or Decimal("0.00"),
                        "status": item.status,
                        "data_pagamento": item.data_pagamento,
                        "id_original": item.id,
                    }
                )
            elif tipo == "Financiamento":
                item_dict.update(
                    {
                        "vencimento": item.data_vencimento,
                        "origem": f"{item.financiamento.nome_financiamento} ({item.numero_parcela}/{item.financiamento.prazo_meses})",
                        "valor_display": item.valor_total_previsto,
                        "valor_pago": item.valor_pago or Decimal("0.00"),
                        "status": item.status,
                        "data_pagamento": item.data_pagamento,
                        "id_original": item.id,
                    }
                )
            elif tipo == "Despesa":
                item_dict.update(
                    {
                        "vencimento": item.data_vencimento,
                        "origem": item.despesa_receita.nome,
                        "valor_display": item.valor_previsto,
                        "valor_pago": item.valor_realizado or Decimal("0.00"),
                        "status": item.status,
                        "data_pagamento": item.data_pagamento,
                        "id_original": item.id,
                    }
                )

            item_dict.update(
                {
                    "tipo": tipo,
                    "pago_com": pago_com,
                    "valor_pendente": item_dict["valor_display"]
                    - item_dict["valor_pago"],
                }
            )

            contas_a_pagar.append(item_dict)
            totais[STATUS_PREVISTO] += item_dict["valor_display"]
            totais[STATUS_PAGO] += item_dict["valor_pago"]

        for fatura in faturas:
            adicionar_conta_a_pagar(fatura, "Crediário")
        for parcela in parcelas:
            adicionar_conta_a_pagar(parcela, "Financiamento")
        for despesa in despesas:
            adicionar_conta_a_pagar(despesa, "Despesa")

        contas_a_pagar.sort(key=lambda x: x["vencimento"])
        totais[STATUS_PENDENTE] = totais[STATUS_PREVISTO] - totais[STATUS_PAGO]

    return render_template(
        "pagamentos/painel.html",
        form=form,
        pagamento_form=pagamento_form,
        contas=contas_a_pagar,
        totais=totais,
        title="Painel de Pagamentos",
    )


@pagamentos_bp.route("/pagar", methods=["POST"])
@login_required
def pagar_conta():
    account_choices = conta_service.get_active_accounts_for_user_choices()
    form = PagamentoForm(request.form, account_choices=account_choices)

    if form.validate_on_submit():
        success, message = registrar_pagamento(form)
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

    return redirect(url_for("pagamentos.painel", mes_ano=request.form.get("mes_ano")))


@pagamentos_bp.route("/estornar", methods=["POST"])
@login_required
def estornar_pagamento():
    item_id = request.form.get("item_id")
    item_tipo = request.form.get("item_tipo")

    success, message = estornar_pagamento_service(item_id, item_tipo)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("pagamentos.painel", mes_ano=request.form.get("mes_ano")))
