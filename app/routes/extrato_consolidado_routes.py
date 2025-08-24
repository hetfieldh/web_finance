# app/routes/extrato_consolidado_routes.py

from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.forms.extrato_forms import ExtratoConsolidadoForm
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento
from app.services import relatorios_service  # Importando o service

extrato_consolidado_bp = Blueprint(
    "extrato_consolidado", __name__, url_prefix="/extratos"
)


@extrato_consolidado_bp.route("/consolidado", methods=["GET", "POST"])
@login_required
def extrato_consolidado():
    form = ExtratoConsolidadoForm(request.form)
    movimentacoes = []

    if request.method == "GET" and not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%Y-%m")

    mes_ano_str = form.mes_ano.data
    kpis = relatorios_service.get_balanco_mensal(
        current_user.id, int(mes_ano_str.split("-")[0]), int(mes_ano_str.split("-")[1])
    )

    if mes_ano_str:
        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = date(ano, mes, 1)
        data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        # 1. Busca Despesas
        despesas = DespRecMovimento.query.filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.despesa_receita.has(natureza="Despesa"),
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for item in despesas:
            movimentacoes.append(
                {
                    "data": item.data_pagamento,
                    "origem": item.despesa_receita.nome,
                    "tipo": "Despesa",
                    "valor_realizado": item.valor_realizado,
                }
            )

        # 2. Busca Receitas (sem ser Salário)
        receitas = DespRecMovimento.query.filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.despesa_receita.has(natureza="Receita"),
            DespRecMovimento.data_pagamento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for item in receitas:
            movimentacoes.append(
                {
                    "data": item.data_pagamento,
                    "origem": item.despesa_receita.nome,
                    "tipo": "Receita",
                    "valor_realizado": item.valor_realizado,
                }
            )

        # 3. Busca Faturas de Crediário Pagas
        faturas = CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == current_user.id,
            CrediarioFatura.data_pagamento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for fatura in faturas:
            movimentacoes.append(
                {
                    "data": fatura.data_pagamento,
                    "origem": f"Fatura {fatura.crediario.nome_crediario}",
                    "tipo": "Crediário",
                    "valor_realizado": fatura.valor_pago_fatura,
                }
            )

        # 4. Busca Parcelas de Financiamento Pagas e Amortizadas
        parcelas = FinanciamentoParcela.query.filter(
            FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            FinanciamentoParcela.data_pagamento.between(data_inicio_mes, data_fim_mes),
            FinanciamentoParcela.status.in_(["Paga", "Amortizada"]),
        ).all()
        for parcela in parcelas:
            descricao = f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})"
            tipo = "Amortização" if parcela.status == "Amortizada" else "Financiamento"
            movimentacoes.append(
                {
                    "data": parcela.data_pagamento,
                    "origem": descricao,
                    "tipo": tipo,
                    "valor_realizado": parcela.valor_pago,
                }
            )

        # 5. Busca Salários e Benefícios Recebidos
        salarios = SalarioMovimento.query.filter(
            SalarioMovimento.usuario_id == current_user.id,
            SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for salario in salarios:
            if salario.movimento_bancario_salario_id:
                movimentacoes.append(
                    {
                        "data": salario.data_recebimento,
                        "origem": f"Salário (Ref: {salario.mes_referencia})",
                        "tipo": "Salário",
                        "valor_realizado": salario.salario_liquido,
                    }
                )
            if salario.movimento_bancario_beneficio_id:
                movimentacoes.append(
                    {
                        "data": salario.data_recebimento,
                        "origem": f"Benefícios (Ref: {salario.mes_referencia})",
                        "tipo": "Benefício",
                        "valor_realizado": salario.total_beneficios,
                    }
                )

        # Ordena a lista final pela data do evento
        movimentacoes.sort(key=lambda x: x["data"])

    return render_template(
        "extratos/consolidado.html",
        form=form,
        movimentacoes=movimentacoes,
        kpis=kpis,
        title="Extrato Consolidado",
    )
