# app/routes/recebimentos_routes.py

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
from sqlalchemy.orm import joinedload, subqueryload

from app import db
from app.forms.recebimentos_forms import PainelRecebimentosForm, RecebimentoForm
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.services.recebimento_service import (
    estornar_recebimento as estornar_recebimento_service,
)
from app.services.recebimento_service import (
    registrar_recebimento as registrar_recebimento_service,
)

recebimentos_bp = Blueprint("recebimentos", __name__, url_prefix="/recebimentos")


@recebimentos_bp.route("/painel", methods=["GET", "POST"])
@login_required
def painel():
    form = PainelRecebimentosForm(request.form)
    recebimento_form = RecebimentoForm()

    if request.method == "GET" and not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%Y-%m")

    mes_ano_str = form.mes_ano.data
    contas_a_receber = []
    totais = {
        "previsto": Decimal("0.00"),
        "recebido": Decimal("0.00"),
        "pendente": Decimal("0.00"),
    }

    if mes_ano_str:
        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = date(ano, mes, 1)
        if mes == 12:
            data_fim_mes = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim_mes = date(ano, mes + 1, 1) - timedelta(days=1)

        salario_movimentos = (
            SalarioMovimento.query.filter(
                SalarioMovimento.usuario_id == current_user.id,
                SalarioMovimento.data_recebimento >= data_inicio_mes,
                SalarioMovimento.data_recebimento <= data_fim_mes,
            )
            .options(
                subqueryload(SalarioMovimento.itens).joinedload(
                    SalarioMovimentoItem.salario_item
                ),
                joinedload(SalarioMovimento.movimento_bancario_salario),
                joinedload(SalarioMovimento.movimento_bancario_beneficio),
            )
            .all()
        )

        for movimento in salario_movimentos:
            salario_liquido = sum(
                i.valor for i in movimento.itens if i.salario_item.tipo == "Provento"
            ) - sum(
                i.valor
                for i in movimento.itens
                if i.salario_item.tipo in ["Imposto", "Desconto"]
            )
            total_beneficios = sum(
                i.valor for i in movimento.itens if i.salario_item.tipo == "Benefício"
            )

            if salario_liquido > 0:
                status_salario = (
                    "Recebido"
                    if movimento.movimento_bancario_salario_id
                    else "Pendente"
                )
                data_pag_salario = (
                    movimento.movimento_bancario_salario.data_movimento
                    if movimento.movimento_bancario_salario
                    else None
                )
                contas_a_receber.append(
                    {
                        "vencimento": movimento.data_recebimento,
                        "origem": f"Salário Líquido (Ref: {movimento.mes_referencia})",
                        "valor": salario_liquido,
                        "status": status_salario,
                        "data_pagamento": data_pag_salario,
                        "tipo": "Salário",
                        "id_original": movimento.id,
                    }
                )
                totais["previsto"] += salario_liquido
                if status_salario == "Recebido":
                    totais["recebido"] += salario_liquido

            if total_beneficios > 0:
                status_beneficio = (
                    "Recebido"
                    if movimento.movimento_bancario_beneficio_id
                    else "Pendente"
                )
                data_pag_beneficio = (
                    movimento.movimento_bancario_beneficio.data_movimento
                    if movimento.movimento_bancario_beneficio
                    else None
                )
                contas_a_receber.append(
                    {
                        "vencimento": movimento.data_recebimento,
                        "origem": f"Benefícios (Ref: {movimento.mes_referencia})",
                        "valor": total_beneficios,
                        "status": status_beneficio,
                        "data_pagamento": data_pag_beneficio,
                        "tipo": "Benefício",
                        "id_original": movimento.id,
                    }
                )
                totais["previsto"] += total_beneficios
                if status_beneficio == "Recebido":
                    totais["recebido"] += total_beneficios

        outras_receitas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.data_vencimento >= data_inicio_mes,
                DespRecMovimento.data_vencimento <= data_fim_mes,
                DespRecMovimento.despesa_receita.has(natureza="Receita"),
            )
            .options(joinedload(DespRecMovimento.despesa_receita))
            .all()
        )
        for receita in outras_receitas:
            valor_previsto = receita.valor_previsto
            valor_recebido = receita.valor_realizado or Decimal("0.00")
            contas_a_receber.append(
                {
                    "vencimento": receita.data_vencimento,
                    "origem": receita.despesa_receita.nome,
                    "valor": valor_previsto,
                    "status": receita.status,
                    "data_pagamento": receita.data_pagamento,
                    "tipo": "Receita",
                    "id_original": receita.id,
                }
            )
            totais["previsto"] += valor_previsto
            totais["recebido"] += valor_recebido

        contas_a_receber.sort(key=lambda x: x["vencimento"])
        totais["pendente"] = totais["previsto"] - totais["recebido"]

    return render_template(
        "recebimentos/painel.html",
        form=form,
        recebimento_form=recebimento_form,
        contas=contas_a_receber,
        totais=totais,
        title="Painel de Recebimentos",
    )


@recebimentos_bp.route("/registrar", methods=["POST"])
@login_required
def registrar_recebimento():
    form = RecebimentoForm()
    if form.validate_on_submit():
        success, message = registrar_recebimento_service(form)
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
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
