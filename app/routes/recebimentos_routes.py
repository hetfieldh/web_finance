# app/routes/recebimentos_routes.py

from datetime import date, timedelta
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
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.models.salario_movimento_model import SalarioMovimento

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

        # 1. Buscar Salário Líquido e Benefícios
        salario_movimentos = SalarioMovimento.query.filter(
            SalarioMovimento.usuario_id == current_user.id,
            SalarioMovimento.data_recebimento >= data_inicio_mes,
            SalarioMovimento.data_recebimento <= data_fim_mes,
        ).all()

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

        # 2. Buscar Outras Receitas
        outras_receitas = (
            DespRecMovimento.query.join(DespRecMovimento.despesa_receita)
            .filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.data_vencimento >= data_inicio_mes,
                DespRecMovimento.data_vencimento <= data_fim_mes,
                DespRecMovimento.despesa_receita.has(natureza="Receita"),
            )
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
        try:
            conta_credito = Conta.query.get(form.conta_id.data)
            valor_recebido = form.valor_recebido.data
            item_id = form.item_id.data
            item_tipo = form.item_tipo.data

            tipo_transacao_credito = ContaTransacao.query.filter_by(
                usuario_id=current_user.id,
                transacao_tipo="RECEBIMENTO",
                tipo="Crédito",
            ).first()
            if not tipo_transacao_credito:
                flash(
                    'Tipo de transação "RECEBIMENTO" (Crédito) não encontrado. Por favor, cadastre-o primeiro.',
                    "danger",
                )
                return redirect(url_for("recebimentos.painel"))

            novo_movimento = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_credito.id,
                conta_transacao_id=tipo_transacao_credito.id,
                data_movimento=form.data_recebimento.data,
                valor=valor_recebido,
                descricao=form.item_descricao.data,
            )
            db.session.add(novo_movimento)
            conta_credito.saldo_atual += valor_recebido
            db.session.flush()

            if item_tipo == "Receita":
                item = DespRecMovimento.query.get(item_id)
                item.status = "Pago"
                item.valor_realizado = valor_recebido
                item.data_pagamento = form.data_recebimento.data
                item.movimento_bancario_id = novo_movimento.id
            elif item_tipo in ["Salário", "Benefício"]:
                item = SalarioMovimento.query.get(item_id)

                has_beneficios = any(
                    i.salario_item.tipo == "Benefício" for i in item.itens
                )

                if item_tipo == "Salário":
                    item.movimento_bancario_salario_id = novo_movimento.id
                else:
                    item.movimento_bancario_beneficio_id = novo_movimento.id

                if item.movimento_bancario_salario_id and (
                    not has_beneficios or item.movimento_bancario_beneficio_id
                ):
                    item.status = "Recebido"
                else:
                    item.status = "Parcialmente Recebido"

            db.session.commit()
            flash("Recebimento registrado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Ocorreu um erro ao registrar o recebimento.", "danger")
            current_app.logger.error(
                f"Erro ao registrar recebimento: {e}", exc_info=True
            )

    return redirect(url_for("recebimentos.painel", mes_ano=request.form.get("mes_ano")))


@recebimentos_bp.route("/estornar", methods=["POST"])
@login_required
def estornar_recebimento():
    item_id = request.form.get("item_id")
    item_tipo = request.form.get("item_tipo")

    try:
        movimento_bancario_id = None
        item_a_atualizar = None

        if item_tipo == "Receita":
            item_a_atualizar = DespRecMovimento.query.get(item_id)
            if item_a_atualizar:
                movimento_bancario_id = item_a_atualizar.movimento_bancario_id
                item_a_atualizar.status = "Pendente"
                item_a_atualizar.valor_realizado = None
                item_a_atualizar.data_pagamento = None
                item_a_atualizar.movimento_bancario_id = None

        elif item_tipo in ["Salário", "Benefício"]:
            item_a_atualizar = SalarioMovimento.query.get(item_id)
            if item_a_atualizar:
                if item_tipo == "Salário":
                    movimento_bancario_id = (
                        item_a_atualizar.movimento_bancario_salario_id
                    )
                    item_a_atualizar.movimento_bancario_salario_id = None
                else:
                    movimento_bancario_id = (
                        item_a_atualizar.movimento_bancario_beneficio_id
                    )
                    item_a_atualizar.movimento_bancario_beneficio_id = None

                if (
                    item_a_atualizar.movimento_bancario_salario_id
                    or item_a_atualizar.movimento_bancario_beneficio_id
                ):
                    item_a_atualizar.status = "Parcialmente Recebido"
                else:
                    item_a_atualizar.status = "Pendente"

        if movimento_bancario_id:
            movimento_bancario = ContaMovimento.query.get(movimento_bancario_id)
            if movimento_bancario:
                conta_bancaria = Conta.query.get(movimento_bancario.conta_id)
                conta_bancaria.saldo_atual -= movimento_bancario.valor
                db.session.delete(movimento_bancario)

        db.session.commit()
        flash("Recebimento estornado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Ocorreu um erro ao estornar o recebimento.", "danger")
        current_app.logger.error(f"Erro ao estornar recebimento: {e}", exc_info=True)

    return redirect(url_for("recebimentos.painel", mes_ano=request.form.get("mes_ano")))
