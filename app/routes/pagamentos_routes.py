# app/routes/pagamentos_routes.py

from datetime import date, datetime, timedelta
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
from sqlalchemy import extract

from app import db
from app.forms.pagamentos_forms import PagamentoForm, PainelPagamentosForm
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.crediario_fatura_model import CrediarioFatura
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.financiamento_parcela_model import FinanciamentoParcela

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

        # 1. Buscar Faturas de Crediário
        faturas = CrediarioFatura.query.filter(
            CrediarioFatura.usuario_id == current_user.id,
            CrediarioFatura.data_vencimento_fatura >= data_inicio_mes,
            CrediarioFatura.data_vencimento_fatura <= data_fim_mes,
        ).all()
        for fatura in faturas:
            valor_original = fatura.valor_total_fatura
            valor_pago = fatura.valor_pago_fatura
            contas_a_pagar.append(
                {
                    "vencimento": fatura.data_vencimento_fatura,
                    "origem": f"Fatura {fatura.crediario.nome_crediario}",
                    "valor": valor_original - valor_pago,
                    "status": fatura.status,
                    "tipo": "Crediário",
                    "id_original": fatura.id,
                }
            )
            totais["previsto"] += valor_original
            totais["pago"] += valor_pago

        # 2. Buscar Parcelas de Financiamento
        parcelas = (
            FinanciamentoParcela.query.join(FinanciamentoParcela.financiamento)
            .filter(
                FinanciamentoParcela.data_vencimento >= data_inicio_mes,
                FinanciamentoParcela.data_vencimento <= data_fim_mes,
                FinanciamentoParcela.financiamento.has(usuario_id=current_user.id),
            )
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
                    "valor": valor_original - valor_pago,
                    "status": parcela.status,
                    "tipo": "Financiamento",
                    "id_original": parcela.id,
                }
            )
            totais["previsto"] += valor_original
            totais["pago"] += valor_pago

        # 3. Buscar Despesas
        despesas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.data_vencimento >= data_inicio_mes,
                DespRecMovimento.data_vencimento <= data_fim_mes,
                DespRecMovimento.despesa_receita.has(natureza="Despesa"),
            )
            .all()
        )
        for despesa in despesas:
            valor_original = despesa.valor_previsto
            valor_pago = despesa.valor_realizado or Decimal("0.00")
            contas_a_pagar.append(
                {
                    "vencimento": despesa.data_vencimento,
                    "origem": despesa.despesa_receita.nome,
                    "valor": valor_original - valor_pago,
                    "status": despesa.status,
                    "tipo": "Despesa",
                    "id_original": despesa.id,
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
        try:
            conta_debito = Conta.query.get(form.conta_id.data)
            valor_pago = form.valor_pago.data

            # --- LÓGICA DE VALIDAÇÃO DE SALDO ADICIONADA ---
            saldo_disponivel = conta_debito.saldo_atual
            if conta_debito.tipo in ["Corrente", "Digital"] and conta_debito.limite:
                saldo_disponivel += conta_debito.limite

            if valor_pago > saldo_disponivel:
                flash(
                    f"Saldo insuficiente na conta {conta_debito.nome_banco}. Saldo disponível (com limite): R$ {saldo_disponivel:.2f}",
                    "danger",
                )
                return redirect(
                    url_for("pagamentos.painel", mes_ano=request.form.get("mes_ano"))
                )
            # --- FIM DA LÓGICA DE VALIDAÇÃO ---

            tipo_transacao_debito = ContaTransacao.query.filter_by(
                usuario_id=current_user.id, transacao_tipo="PAGAMENTOS", tipo="Débito"
            ).first()
            if not tipo_transacao_debito:
                flash(
                    'Tipo de transação "PAGAMENTOS" (Débito) não encontrado. Por favor, cadastre-o primeiro.',
                    "danger",
                )
                return redirect(url_for("pagamentos.painel"))

            novo_movimento = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_debito.id,
                conta_transacao_id=tipo_transacao_debito.id,
                data_movimento=form.data_pagamento.data,
                valor=valor_pago,
                descricao=form.item_descricao.data,
            )
            db.session.add(novo_movimento)
            conta_debito.saldo_atual -= valor_pago
            db.session.flush()

            item_id = form.item_id.data
            item_tipo = form.item_tipo.data

            if item_tipo == "Despesa":
                item = DespRecMovimento.query.get(item_id)
                item.status = "Pago"
                item.valor_realizado = valor_pago
                item.data_pagamento = form.data_pagamento.data
                item.movimento_bancario_id = novo_movimento.id
            elif item_tipo == "Financiamento":
                item = FinanciamentoParcela.query.get(item_id)
                item.status = "Paga"
                item.data_pagamento = form.data_pagamento.data
                item.movimento_bancario_id = novo_movimento.id
            elif item_tipo == "Crediário":
                item = CrediarioFatura.query.get(item_id)
                item.valor_pago_fatura += valor_pago
                item.data_pagamento = form.data_pagamento.data
                if item.valor_pago_fatura >= item.valor_total_fatura:
                    item.status = "Paga"
                else:
                    item.status = "Parcialmente Paga"

            db.session.commit()
            flash("Pagamento registrado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Ocorreu um erro ao registrar o pagamento.", "danger")
            current_app.logger.error(f"Erro ao pagar conta: {e}", exc_info=True)

    return redirect(url_for("pagamentos.painel", mes_ano=request.form.get("mes_ano")))


@pagamentos_bp.route("/estornar", methods=["POST"])
@login_required
def estornar_pagamento():
    """Estorna um pagamento, revertendo a movimentação e o status do item."""
    item_id = request.form.get("item_id")
    item_tipo = request.form.get("item_tipo")

    try:
        movimento_bancario_id = None
        valor_estornado = Decimal("0.00")

        if item_tipo == "Despesa":
            item = DespRecMovimento.query.get(item_id)
            movimento_bancario_id = item.movimento_bancario_id
            valor_estornado = item.valor_realizado
            item.status = "Pendente"
            item.valor_realizado = None
            item.data_pagamento = None
            item.movimento_bancario_id = None

        elif item_tipo == "Financiamento":
            item = FinanciamentoParcela.query.get(item_id)
            movimento_bancario_id = item.movimento_bancario_id
            valor_estornado = item.valor_total_previsto
            item.status = "A Pagar"
            item.data_pagamento = None
            item.movimento_bancario_id = None

        elif item_tipo == "Crediário":
            item = CrediarioFatura.query.get(item_id)
            valor_estornado = item.valor_pago_fatura
            item.valor_pago_fatura = Decimal("0.00")
            item.status = "Aberta"
            item.data_pagamento = None

        if movimento_bancario_id:
            movimento_bancario = ContaMovimento.query.get(movimento_bancario_id)
            if movimento_bancario:
                conta_bancaria = Conta.query.get(movimento_bancario.conta_id)
                conta_bancaria.saldo_atual += valor_estornado
                db.session.delete(movimento_bancario)

        db.session.commit()
        flash("Pagamento estornado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Ocorreu um erro ao estornar o pagamento.", "danger")
        current_app.logger.error(f"Erro ao estornar pagamento: {e}", exc_info=True)

    return redirect(url_for("pagamentos.painel", mes_ano=request.form.get("mes_ano")))
