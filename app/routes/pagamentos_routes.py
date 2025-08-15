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
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_movimento_model import CrediarioMovimento
from app.models.crediario_parcela_model import CrediarioParcela
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.services.pagamento_service import (
    estornar_pagamento as estornar_pagamento_service,
)
from app.services.pagamento_service import registrar_pagamento

pagamentos_bp = Blueprint("pagamentos", __name__, url_prefix="/pagamentos")


@pagamentos_bp.route("/painel", methods=["GET", "POST"])
@login_required
def painel():
    form = PainelPagamentosForm(request.form)
    pagamento_form = PagamentoForm()

    if request.method == "GET" and not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%Y-%m")

    mes_ano_str = form.mes_ano.data
    contas_a_pagar = []
    totais = {
        "previsto": Decimal("0.00"),
        "pago": Decimal("0.00"),
        "pendente": Decimal("0.00"),
    }

    if mes_ano_str:
        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = date(ano, mes, 1)
        if mes == 12:
            data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

        faturas = (
            CrediarioFatura.query.filter(
                CrediarioFatura.usuario_id == current_user.id,
                CrediarioFatura.data_vencimento_fatura >= data_inicio_mes,
                CrediarioFatura.data_vencimento_fatura <= data_fim_mes,
            )
            .options(joinedload(CrediarioFatura.crediario))
            .all()
        )

        for fatura in faturas:
            soma_real_parcelas = (
                db.session.query(
                    func.coalesce(
                        func.sum(CrediarioParcela.valor_parcela), Decimal("0.00")
                    )
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
            valor_original = fatura.valor_total_fatura
            valor_pago = fatura.valor_pago_fatura
            contas_a_pagar.append(
                {
                    "vencimento": fatura.data_vencimento_fatura,
                    "origem": f"Fatura {fatura.crediario.nome_crediario}",
                    "valor_display": valor_original,
                    "valor_pendente": valor_original - valor_pago,
                    "status": fatura.status,
                    "data_pagamento": fatura.data_pagamento,
                    "tipo": "Crediário",
                    "id_original": fatura.id,
                    "desatualizada": desatualizada,
                }
            )
            totais["previsto"] += valor_original
            totais["pago"] += valor_pago

        parcelas = (
            FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
            .filter(
                FinanciamentoParcela.data_vencimento >= data_inicio_mes,
                FinanciamentoParcela.data_vencimento <= data_fim_mes,
                FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            )
            .options(joinedload(FinanciamentoParcela.financiamento))
            .all()
        )
        for parcela in parcelas:
            valor_original = parcela.valor_total_previsto
            valor_pago = (
                valor_original
                if parcela.status in ["Paga", "Pago"]
                else Decimal("0.00")
            )
            contas_a_pagar.append(
                {
                    "vencimento": parcela.data_vencimento,
                    "origem": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                    "valor_display": valor_original,
                    "valor_pendente": valor_original - valor_pago,
                    "status": parcela.status,
                    "data_pagamento": parcela.data_pagamento,
                    "tipo": "Financiamento",
                    "id_original": parcela.id,
                    "desatualizada": False,
                }
            )
            totais["previsto"] += valor_original
            totais["pago"] += valor_pago

        despesas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.data_vencimento >= data_inicio_mes,
                DespRecMovimento.data_vencimento <= data_fim_mes,
                DespRecMovimento.despesa_receita.has(natureza="Despesa"),
            )
            .options(joinedload(DespRecMovimento.despesa_receita))
            .all()
        )
        for despesa in despesas:
            valor_original = despesa.valor_previsto
            valor_pago = despesa.valor_realizado or Decimal("0.00")
            contas_a_pagar.append(
                {
                    "vencimento": despesa.data_vencimento,
                    "origem": despesa.despesa_receita.nome,
                    "valor_display": valor_original,
                    "valor_pendente": valor_original - valor_pago,
                    "status": despesa.status,
                    "data_pagamento": despesa.data_pagamento,
                    "tipo": "Despesa",
                    "id_original": despesa.id,
                    "desatualizada": False,
                }
            )
            totais["previsto"] += valor_original
            totais["pago"] += valor_pago

        contas_a_pagar.sort(key=lambda x: x["vencimento"])
        totais["pendente"] = totais["previsto"] - totais["pago"]

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
    form = PagamentoForm()
    if form.validate_on_submit():
        success, message = registrar_pagamento(form)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")

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
