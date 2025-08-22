# app\routes\extrato_consolidado_routes.py

from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.forms.extrato_forms import ExtratoConsolidadoForm
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.models.salario_movimento_model import SalarioMovimento

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
    if mes_ano_str:
        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = date(ano, mes, 1)
        data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
            day=1
        ) - timedelta(days=1)

        # 1. Busca Despesas e Receitas
        desp_rec = DespRecMovimento.query.filter(
            DespRecMovimento.usuario_id == current_user.id,
            DespRecMovimento.data_vencimento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for item in desp_rec:
            movimentacoes.append(
                {
                    "data": item.data_vencimento,
                    "origem": item.despesa_receita.nome,
                    "tipo": item.despesa_receita.natureza,
                    "valor_previsto": item.valor_previsto,
                    "valor_realizado": item.valor_realizado,
                    "status": item.status,
                }
            )

        # 2. Busca Faturas de Crediário
        faturas = CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == current_user.id,
            CrediarioFatura.data_vencimento_fatura.between(
                data_inicio_mes, data_fim_mes
            ),
        ).all()
        for fatura in faturas:
            movimentacoes.append(
                {
                    "data": fatura.data_vencimento_fatura,
                    "origem": f"Fatura {fatura.crediario.nome_crediario}",
                    "tipo": "Crediário",
                    "valor_previsto": fatura.valor_total_fatura,
                    "valor_realizado": fatura.valor_pago_fatura,
                    "status": fatura.status,
                }
            )

        # 3. Busca Parcelas de Financiamento
        parcelas = FinanciamentoParcela.query.filter(
            FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            FinanciamentoParcela.data_vencimento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for parcela in parcelas:
            movimentacoes.append(
                {
                    "data": parcela.data_vencimento,
                    "origem": f"{parcela.financiamento.nome_financiamento} ({parcela.numero_parcela}/{parcela.financiamento.prazo_meses})",
                    "tipo": "Financiamento",
                    "valor_previsto": parcela.valor_total_previsto,
                    "valor_realizado": parcela.valor_pago,
                    "status": parcela.status,
                }
            )

        # 4. Busca Salários e Benefícios
        salarios = SalarioMovimento.query.filter(
            SalarioMovimento.usuario_id == current_user.id,
            SalarioMovimento.data_recebimento.between(data_inicio_mes, data_fim_mes),
        ).all()
        for salario in salarios:
            salario_liquido = sum(
                i.valor for i in salario.itens if i.salario_item.tipo == "Provento"
            ) - sum(
                i.valor
                for i in salario.itens
                if i.salario_item.tipo in ["Imposto", "Desconto"]
            )
            beneficios = sum(
                i.valor for i in salario.itens if i.salario_item.tipo == "Benefício"
            )

            if salario_liquido > 0:
                movimentacoes.append(
                    {
                        "data": salario.data_recebimento,
                        "origem": f"Salário (Ref: {salario.mes_referencia})",
                        "tipo": "Salário",
                        "valor_previsto": salario_liquido,
                        "valor_realizado": (
                            salario_liquido
                            if salario.status in ["Recebido", "Parcialmente Recebido"]
                            else None
                        ),
                        "status": salario.status,
                    }
                )
            if beneficios > 0:
                movimentacoes.append(
                    {
                        "data": salario.data_recebimento,
                        "origem": f"Benefícios (Ref: {salario.mes_referencia})",
                        "tipo": "Benefício",
                        "valor_previsto": beneficios,
                        "valor_realizado": (
                            beneficios
                            if salario.status in ["Recebido", "Parcialmente Recebido"]
                            else None
                        ),
                        "status": salario.status,
                    }
                )

        movimentacoes.sort(key=lambda x: x["data"])

    return render_template(
        "extratos/consolidado.html",
        form=form,
        movimentacoes=movimentacoes,
        title="Extrato Consolidado",
    )
