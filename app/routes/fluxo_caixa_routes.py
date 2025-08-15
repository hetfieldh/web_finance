# app/routes/fluxo_caixa_routes.py

from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload, subqueryload

from app.forms.fluxo_caixa_forms import FluxoCaixaForm
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento

fluxo_caixa_bp = Blueprint("fluxo_caixa", __name__, url_prefix="/fluxo_caixa")


@fluxo_caixa_bp.route("/painel", methods=["GET", "POST"])
@login_required
def painel():
    form = FluxoCaixaForm(request.form)

    if request.method == "GET" and not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%Y-%m")

    mes_ano_str = form.mes_ano.data
    movimentacoes_consolidadas = []
    kpis = {
        "receitas": Decimal("0.00"),
        "despesas": Decimal("0.00"),
        "balanco": Decimal("0.00"),
        "comprometimento": 0,
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
                or_(
                    SalarioMovimento.movimento_bancario_salario_id.isnot(None),
                    SalarioMovimento.movimento_bancario_beneficio_id.isnot(None),
                ),
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

        for mov in salario_movimentos:
            if mov.movimento_bancario_salario_id:
                salario_liquido = sum(
                    i.valor for i in mov.itens if i.salario_item.tipo == "Provento"
                ) - sum(
                    i.valor
                    for i in mov.itens
                    if i.salario_item.tipo in ["Imposto", "Desconto"]
                )
                movimentacoes_consolidadas.append(
                    {
                        "data": mov.movimento_bancario_salario.data_movimento,
                        "descricao": f"Salário (Ref: {mov.mes_referencia})",
                        "categoria": "Salário",
                        "valor": salario_liquido,
                        "tipo": "entrada",
                        "status": "Recebido",
                        "valor_realizado": salario_liquido,
                        "diferenca": Decimal("0.00"),
                    }
                )
                kpis["receitas"] += salario_liquido

            if mov.movimento_bancario_beneficio_id:
                total_beneficios = sum(
                    i.valor for i in mov.itens if i.salario_item.tipo == "Benefício"
                )
                movimentacoes_consolidadas.append(
                    {
                        "data": mov.movimento_bancario_beneficio.data_movimento,
                        "descricao": f"Benefícios (Ref: {mov.mes_referencia})",
                        "categoria": "Benefício",
                        "valor": total_beneficios,
                        "tipo": "entrada",
                        "status": "Recebido",
                        "valor_realizado": total_beneficios,
                        "diferenca": Decimal("0.00"),
                    }
                )
                kpis["receitas"] += total_beneficios

        outras_receitas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.status == "Pago",
                DespRecMovimento.data_pagamento >= data_inicio_mes,
                DespRecMovimento.data_pagamento <= data_fim_mes,
                DespRecMovimento.despesa_receita.has(natureza="Receita"),
            )
            .options(joinedload(DespRecMovimento.despesa_receita))
            .all()
        )
        for receita in outras_receitas:
            valor_previsto = receita.valor_previsto
            valor_realizado = receita.valor_realizado or Decimal("0.00")
            movimentacoes_consolidadas.append(
                {
                    "data": receita.data_pagamento,
                    "descricao": receita.despesa_receita.nome,
                    "categoria": "Receita",
                    "valor": valor_previsto,
                    "tipo": "entrada",
                    "status": receita.status,
                    "valor_realizado": valor_realizado,
                    "diferenca": valor_previsto - valor_realizado,
                }
            )
            kpis["receitas"] += valor_realizado

        faturas_pagas = (
            CrediarioFatura.query.filter(
                CrediarioFatura.usuario_id == current_user.id,
                CrediarioFatura.status.in_(["Paga", "Parcialmente Paga"]),
                CrediarioFatura.data_pagamento >= data_inicio_mes,
                CrediarioFatura.data_pagamento <= data_fim_mes,
            )
            .options(joinedload(CrediarioFatura.crediario))
            .all()
        )
        for fatura in faturas_pagas:
            valor_previsto = fatura.valor_total_fatura
            valor_pago = fatura.valor_pago_fatura
            movimentacoes_consolidadas.append(
                {
                    "data": fatura.data_pagamento,
                    "descricao": f"Fatura {fatura.crediario.nome_crediario}",
                    "categoria": "Crediário",
                    "valor": valor_previsto,
                    "tipo": "saida",
                    "status": fatura.status,
                    "valor_realizado": valor_pago,
                    "diferenca": valor_previsto - valor_pago,
                }
            )
            kpis["despesas"] += valor_pago

        parcelas_pagas = (
            FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
            .filter(
                FinanciamentoParcela.status == "Paga",
                FinanciamentoParcela.data_pagamento >= data_inicio_mes,
                FinanciamentoParcela.data_pagamento <= data_fim_mes,
                FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            )
            .options(joinedload(FinanciamentoParcela.financiamento))
            .all()
        )
        for parcela in parcelas_pagas:
            valor_previsto = parcela.valor_total_previsto
            movimentacoes_consolidadas.append(
                {
                    "data": parcela.data_pagamento,
                    "descricao": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                    "categoria": "Financiamento",
                    "valor": valor_previsto,
                    "tipo": "saida",
                    "status": parcela.status,
                    "valor_realizado": valor_previsto,
                    "diferenca": Decimal("0.00"),
                }
            )
            kpis["despesas"] += valor_previsto

        outras_despesas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.status == "Pago",
                DespRecMovimento.data_pagamento >= data_inicio_mes,
                DespRecMovimento.data_pagamento <= data_fim_mes,
                DespRecMovimento.despesa_receita.has(natureza="Despesa"),
            )
            .options(joinedload(DespRecMovimento.despesa_receita))
            .all()
        )
        for despesa in outras_despesas:
            valor_previsto = despesa.valor_previsto
            valor_realizado = despesa.valor_realizado or Decimal("0.00")
            movimentacoes_consolidadas.append(
                {
                    "data": despesa.data_pagamento,
                    "descricao": despesa.despesa_receita.nome,
                    "categoria": "Despesa",
                    "valor": valor_previsto,
                    "tipo": "saida",
                    "status": despesa.status,
                    "valor_realizado": valor_realizado,
                    "diferenca": valor_previsto - valor_realizado,
                }
            )
            kpis["despesas"] += valor_realizado

        movimentacoes_consolidadas.sort(key=lambda x: x["data"])

        kpis["balanco"] = kpis["receitas"] - kpis["despesas"]
        if kpis["receitas"] > 0:
            kpis["comprometimento"] = round((kpis["despesas"] / kpis["receitas"]) * 100)

    return render_template(
        "fluxo_caixa/painel.html",
        form=form,
        movimentacoes=movimentacoes_consolidadas,
        kpis=kpis,
        title="Fluxo de Caixa Mensal",
    )
