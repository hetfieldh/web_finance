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
from app.models.conta_movimento_model import ContaMovimento
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.services import conta_service
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
    account_choices = conta_service.get_active_accounts_for_user_choices()
    recebimento_form = RecebimentoForm(account_choices=account_choices)

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
        data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        salario_movimentos = (
            SalarioMovimento.query.filter(
                SalarioMovimento.usuario_id == current_user.id,
                SalarioMovimento.data_recebimento.between(
                    data_inicio_mes, data_fim_mes
                ),
            )
            .options(
                subqueryload(SalarioMovimento.itens).joinedload(
                    SalarioMovimentoItem.salario_item
                ),
                joinedload(SalarioMovimento.movimento_bancario_salario).joinedload(
                    ContaMovimento.conta
                ),
                joinedload(SalarioMovimento.movimento_bancario_beneficio).joinedload(
                    ContaMovimento.conta
                ),
            )
            .all()
        )

        outras_receitas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
                DespRecMovimento.despesa_receita.has(natureza="Receita"),
            )
            .options(
                joinedload(DespRecMovimento.despesa_receita),
                joinedload(DespRecMovimento.movimento_bancario).joinedload(
                    ContaMovimento.conta
                ),
            )
            .all()
        )

        for movimento in salario_movimentos:
            salario_liquido = movimento.salario_liquido
            total_beneficios = movimento.total_beneficios

            if salario_liquido > 0:
                recebido_em = ""
                is_recebido = movimento.movimento_bancario_salario_id is not None
                if is_recebido and movimento.movimento_bancario_salario.conta:
                    conta = movimento.movimento_bancario_salario.conta
                    recebido_em = f"{conta.nome_banco} ({conta.tipo})"

                contas_a_receber.append(
                    {
                        "vencimento": movimento.data_recebimento,
                        "origem": f"Salário Líquido (Ref: {movimento.mes_referencia})",
                        "valor_previsto": salario_liquido,
                        "valor_recebido": (
                            salario_liquido if is_recebido else Decimal("0.00")
                        ),
                        "status": "Recebido" if is_recebido else "Pendente",
                        "data_pagamento": (
                            movimento.movimento_bancario_salario.data_movimento
                            if is_recebido
                            else None
                        ),
                        "tipo": "Salário",
                        "id_original": movimento.id,
                        "recebido_em": recebido_em,
                    }
                )

            if total_beneficios > 0:
                recebido_em = ""
                is_recebido = movimento.movimento_bancario_beneficio_id is not None
                if is_recebido and movimento.movimento_bancario_beneficio.conta:
                    conta = movimento.movimento_bancario_beneficio.conta
                    recebido_em = f"{conta.nome_banco} ({conta.tipo})"

                contas_a_receber.append(
                    {
                        "vencimento": movimento.data_recebimento,
                        "origem": f"Benefícios (Ref: {movimento.mes_referencia})",
                        "valor_previsto": total_beneficios,
                        "valor_recebido": (
                            total_beneficios if is_recebido else Decimal("0.00")
                        ),
                        "status": "Recebido" if is_recebido else "Pendente",
                        "data_pagamento": (
                            movimento.movimento_bancario_beneficio.data_movimento
                            if is_recebido
                            else None
                        ),
                        "tipo": "Benefício",
                        "id_original": movimento.id,
                        "recebido_em": recebido_em,
                    }
                )

        for receita in outras_receitas:
            recebido_em = ""
            if receita.movimento_bancario and receita.movimento_bancario.conta:
                conta = receita.movimento_bancario.conta
                recebido_em = f"{conta.nome_banco} ({conta.tipo})"

            contas_a_receber.append(
                {
                    "vencimento": receita.data_vencimento,
                    "origem": receita.despesa_receita.nome,
                    "valor_previsto": receita.valor_previsto,
                    "valor_recebido": receita.valor_realizado or Decimal("0.00"),
                    "status": receita.status,
                    "data_pagamento": receita.data_pagamento,
                    "tipo": "Receita",
                    "id_original": receita.id,
                    "recebido_em": recebido_em,
                }
            )

        for conta in contas_a_receber:
            totais["previsto"] += conta["valor_previsto"]
            totais["recebido"] += conta["valor_recebido"]

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
